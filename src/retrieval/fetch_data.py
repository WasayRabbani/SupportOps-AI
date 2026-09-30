"""
extract_policies.py  --  PDF -> ordered, metadata-rich elements -> JSON

Extraction layer only. No chunking, no embeddings.

Pipeline:
  1. extract   : per page, text LINES (with position + font info) and TABLES (with bbox)
  2. boilerplate: detect repeated header/footer lines (margin zones only) and remove them
  3. build     : merge lines + tables in true reading order, detect headings,
                 track section path, stitch tables that continue across pages
  4. save      : elements JSON + audit JSON

Requires: pip install -U pdfplumber
Optional OCR: pip install pytesseract  (+ the Tesseract binary installed on your machine)
"""
import re
import json
import hashlib
import statistics
from pathlib import Path
from collections import Counter, defaultdict

import pdfplumber

# ----------------------------------------------------------------------
# CONFIG
# ----------------------------------------------------------------------
BOILERPLATE_THRESHOLD = 0.6          # line must repeat on >= 60% of pages
BOILERPLATE_MIN_PAGES = 3            # don't guess on tiny files
MARGIN_FRACTION = 0.10               # only top/bottom 10% of the page can be boilerplate
MAX_BOILERPLATE_LINES_PER_ZONE = 3   # never eat more than 3 lines per margin per page
PROTECT_PATTERNS = []                # regexes that must NEVER be removed, e.g. [r"cash on delivery"]

CONT_PREV_BOTTOM = 0.70              # previous table must end below 70% of its page height
CONT_CURR_TOP = 0.30                 # continuing table must start above 30% of its page height
HEADER_SIM = 0.80                    # fraction of header cells that must match to call it a repeated header

HEADING_SIZE_RATIO = 1.15            # font >= 1.15 x body size => heading
MAX_HEADING_CHARS = 120
MAX_BOLD_HEADING_CHARS = 80

ENABLE_OCR = False                   # set True once pytesseract + Tesseract are installed

# Optional extra metadata per file, merged into every element of that file. Example:
# DOC_META = {"refund_policy.pdf": {"policy_type": "refund"}}
DOC_META = {}


# ----------------------------------------------------------------------
# SMALL HELPERS
# ----------------------------------------------------------------------
def _slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def make_doc_id(file):
    """Stable ID: filename slug + first 8 chars of the file's content hash.
    If the PDF content changes, the ID changes (good for re-indexing)."""
    h = hashlib.sha1(Path(file).read_bytes()).hexdigest()[:8]
    return f"{_slug(Path(file).stem)}-{h}"


def clean_text(text):
    text = (text.replace("\ufb01", "fi").replace("\ufb02", "fl")
                .replace("\ufb00", "ff").replace("\ufb03", "ffi")
                .replace("\ufb04", "ffl"))
    text = re.sub(r"\(cid:\d+\)", "", text)          # unmapped glyphs
    text = re.sub(r"(\w)-\n(\w)", r"\1\2", text)      # deliv-\nery -> delivery
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _clean_cell(cell):
    if cell is None:
        return ""
    return re.sub(r"\s+", " ", str(cell)).strip()


def _union_bbox(boxes):
    return [round(min(b[0] for b in boxes), 1), round(min(b[1] for b in boxes), 1),
            round(max(b[2] for b in boxes), 1), round(max(b[3] for b in boxes), 1)]


# ----------------------------------------------------------------------
# STAGE 1: EXTRACTION (lines with font info + tables with bbox)
# ----------------------------------------------------------------------
def _make_table_filter(tables):
    """Keep an object only if it is NOT inside any table bbox."""
    def not_in_a_table(obj):
        v_mid = (obj["top"] + obj["bottom"]) / 2
        h_mid = (obj["x0"] + obj["x1"]) / 2
        for t in tables:
            x0, top, x1, bottom = t.bbox
            if x0 <= h_mid <= x1 and top <= v_mid <= bottom:
                return False
        return True
    return not_in_a_table


def _line_info(line):
    text = (line.get("text") or "").strip()
    chars = [c for c in line.get("chars", []) if c["text"].strip()]
    if not text or not chars:
        return None
    size = round(statistics.median(c["size"] for c in chars), 1)
    bold_chars = sum(
        1 for c in chars
        if any(k in c.get("fontname", "").lower() for k in ("bold", "black", "heavy"))
    )
    return {
        "text": text,
        "x0": float(line["x0"]), "x1": float(line["x1"]),
        "top": float(line["top"]), "bottom": float(line["bottom"]),
        "size": size,
        "bold": bold_chars / len(chars) > 0.6,
    }


def _ocr_page(page):
    try:
        import pytesseract
    except ImportError:
        return None
    try:
        img = page.to_image(resolution=300).original
        return pytesseract.image_to_string(img)
    except Exception:
        return None


def _extract_page(page, enable_ocr):
    tables = page.find_tables()
    filtered = page.filter(_make_table_filter(tables)) if tables else page

    lines = []
    for ln in filtered.extract_text_lines(return_chars=True):
        info = _line_info(ln)
        if info:
            lines.append(info)

    tbls = [{"raw": t.extract(), "bbox": tuple(round(v, 1) for v in t.bbox)} for t in tables]

    ocr_text = None
    if not lines and not tbls and enable_ocr:
        ocr_text = _ocr_page(page)

    return {
        "height": float(page.height), "width": float(page.width),
        "lines": lines, "tables": tbls, "ocr_text": ocr_text,
        "n_chars": len(page.chars), "n_images": len(page.images),
        "failed": False, "error": None,
    }


class Fetch_data:
    def __init__(self, path, enable_ocr=ENABLE_OCR):
        self.path = Path(path)
        self.enable_ocr = enable_ocr
        self.file_errors = []

    def fetch_pdf(self):
        all_pages = []
        for file in sorted(self.path.rglob("*.pdf")):
            try:
                doc_id = make_doc_id(file)
                with pdfplumber.open(file) as pdf:
                    for i, page in enumerate(pdf.pages):
                        base = {"file_name": file.name, "doc_id": doc_id, "page_num": i + 1}
                        try:
                            data = _extract_page(page, self.enable_ocr)
                        except Exception as e:      # one bad page must not kill the file
                            data = {"height": float(page.height), "width": float(page.width),
                                    "lines": [], "tables": [], "ocr_text": None,
                                    "n_chars": 0, "n_images": 0,
                                    "failed": True, "error": str(e)}
                        all_pages.append({**base, **data, "removed": []})
            except Exception as e:                  # one bad file must not kill the run
                self.file_errors.append({"file": file.name, "error": str(e)})
                print(f"[ERROR] Could not open {file.name}: {e}")
        return all_pages


# ----------------------------------------------------------------------
# STAGE 2: BOILERPLATE (safer: margin zones only, position-aware, capped, logged)
# ----------------------------------------------------------------------
def _norm_line(text):
    return re.sub(r"\s+", " ", re.sub(r"\d+", "#", text.lower())).strip()


def _zone(line, height):
    if line["top"] < MARGIN_FRACTION * height:
        return "top"
    if line["bottom"] > (1 - MARGIN_FRACTION) * height:
        return "bottom"
    return None


def _protected(text):
    return any(re.search(p, text, re.IGNORECASE) for p in PROTECT_PATTERNS)


def detect_boilerplate(all_pages):
    """{file_name: set of (zone, normalized_text)} -- only lines inside the
    top/bottom margin that repeat on most pages of the SAME file."""
    by_file = defaultdict(list)
    for p in all_pages:
        by_file[p["file_name"]].append(p)

    flagged = {}
    for fname, fpages in by_file.items():
        total = len(fpages)
        if total < BOILERPLATE_MIN_PAGES:
            flagged[fname] = set()
            continue
        counter = Counter()
        for p in fpages:
            seen = set()
            for ln in p["lines"]:
                z = _zone(ln, p["height"])
                if z and not _protected(ln["text"]):
                    seen.add((z, _norm_line(ln["text"])))
            counter.update(seen)               # once per page, not once per occurrence
        flagged[fname] = {k for k, c in counter.items() if c / total >= BOILERPLATE_THRESHOLD}
    return flagged


def remove_boilerplate(all_pages, flagged):
    for p in all_pages:
        keys = flagged.get(p["file_name"], set())
        if not keys:
            continue
        kept, removed_per_zone = [], Counter()
        for ln in p["lines"]:
            z = _zone(ln, p["height"])
            key = (z, _norm_line(ln["text"]))
            if z and key in keys and removed_per_zone[z] < MAX_BOILERPLATE_LINES_PER_ZONE:
                removed_per_zone[z] += 1
                p["removed"].append(ln["text"])
            else:
                kept.append(ln)
        p["lines"] = kept


# ----------------------------------------------------------------------
# STAGE 3a: HEADING DETECTION (font size + bold, learned per file)
# ----------------------------------------------------------------------
def _is_size_heading(ln, body):
    return ln["size"] >= body * HEADING_SIZE_RATIO and _heading_text_ok(ln["text"], MAX_HEADING_CHARS)


def _heading_text_ok(text, max_chars):
    if len(text) > max_chars:
        return False
    if re.fullmatch(r"[\d\W]+", text):                    # only digits/symbols
        return False
    if text.startswith(("\u2022", "-", "*", "\u2013")):    # bullet line
        return False
    return True


def analyze_fonts(file_pages):
    """Returns (body_size, {heading_size: level}, bold_level)."""
    counts = Counter()
    for p in file_pages:
        for ln in p["lines"]:
            counts[ln["size"]] += len(ln["text"])          # weight by characters
    if not counts:
        return None, {}, 1
    body = counts.most_common(1)[0][0]
    sizes = sorted({ln["size"] for p in file_pages for ln in p["lines"]
                    if _is_size_heading(ln, body)}, reverse=True)
    level_map = {s: i + 1 for i, s in enumerate(sizes)}
    return body, level_map, len(sizes) + 1


def heading_level(ln, body, level_map, bold_level):
    if body is None:
        return None
    if ln["size"] in level_map:
        return level_map[ln["size"]]
    if (ln["bold"] and ln["size"] >= body * 0.95
            and _heading_text_ok(ln["text"], MAX_BOLD_HEADING_CHARS)
            and not ln["text"].endswith((".", ",", ";"))):
        return bold_level
    return None


# ----------------------------------------------------------------------
# STAGE 3b: TABLES (structure kept + embedding text + continuation check)
# ----------------------------------------------------------------------
def _clean_rows(raw):
    rows = [[_clean_cell(c) for c in row] for row in (raw or [])]
    return [r for r in rows if any(r)]


def _make_header(row):
    return [c or f"Column {i + 1}" for i, c in enumerate(row)]


def _norm_cell(c):
    return re.sub(r"\s+", " ", c.lower()).strip()


def _header_similarity(row, header):
    if not row or len(row) != len(header):
        return 0.0
    same = sum(1 for a, b in zip(row, header) if _norm_cell(a) == _norm_cell(b))
    return same / len(header)


def _looks_like_header(row):
    cells = [c for c in row if c]
    return bool(cells) and all(not re.search(r"\d", c) for c in cells)


def rows_to_text(rows, header):
    lines = []
    for row in rows:
        row = row + [""] * (len(header) - len(row))
        parts = [f"{h}: {v}" for h, v in zip(header, row) if v]
        if parts:
            lines.append(" | ".join(parts))
    return "\n".join(lines)


def check_continuation(prev, rows, bbox, page, first_on_page):
    """Returns (is_continuation, reason).
    Needs ALL of: previous table ended its page, this table starts its page,
    same column count, sensible positions, AND header evidence."""
    if prev is None:
        return False, "no_previous_table"
    if not prev["ends_page"] or prev["page"] != page["page_num"] - 1:
        return False, "prev_table_not_at_page_end"
    if not first_on_page:
        return False, "table_not_first_on_page"
    if prev["ncols"] != len(rows[0]):
        return False, "column_count_differs"
    if not (prev["bbox"][3] > CONT_PREV_BOTTOM * prev["height"]
            and bbox[1] < CONT_CURR_TOP * page["height"]):
        return False, "position_mismatch"

    if _header_similarity(rows[0], prev["header"]) >= HEADER_SIM:
        return True, "header_repeated"
    if not _looks_like_header(rows[0]):
        return True, "headerless_continuation"      # first row looks like data
    return False, "header_differs"                   # first row looks like a NEW header


# ----------------------------------------------------------------------
# STAGE 3c: BUILD ELEMENTS IN READING ORDER
# ----------------------------------------------------------------------
def _join_lines(lines):
    heights = [l["bottom"] - l["top"] for l in lines]
    med = statistics.median(heights) if heights else 10
    out = [lines[0]["text"]]
    for prev, cur in zip(lines, lines[1:]):
        gap = cur["top"] - prev["bottom"]
        out.append(("\n\n" if gap > 0.8 * med else "\n") + cur["text"])
    return clean_text("".join(out))


def build_elements(all_pages):
    elements, audit = [], {}

    by_file = defaultdict(list)
    for p in all_pages:
        by_file[p["file_name"]].append(p)

    for fname, fpages in by_file.items():
        fpages.sort(key=lambda p: p["page_num"])
        doc_id = fpages[0]["doc_id"]
        extra_meta = DOC_META.get(fname, {})
        body, level_map, bold_level = analyze_fonts(fpages)

        a = audit[fname] = {
            "doc_id": doc_id, "pages": len(fpages), "failed_pages": [], "empty_pages": [],
            "ocr_pages": [], "needs_ocr_pages": [], "headings": 0, "text_blocks": 0,
            "tables": 0, "continuation_tables": 0, "continuations_rejected": [],
            "boilerplate_removed": Counter(), "chars": 0,
            "body_font_size": body, "heading_font_levels": level_map,
        }

        seq = 0
        table_counter = 0
        stack = []            # [(level, heading_text)]
        prev_table = None

        def new_el(kind, content, page_num, bbox, **extra):
            nonlocal seq
            path = [t for _, t in stack]
            el = {
                "element_id": f"{doc_id}:e{seq:04d}", "seq": seq, "doc_id": doc_id,
                "file_name": fname, "page_num": page_num, "type": kind,
                "content": content, "bbox": bbox,
                "section": " > ".join(path), "section_path": path, "source": "pdf",
                **extra_meta, **extra,
            }
            seq += 1
            elements.append(el)
            a["chars"] += len(content)
            return el

        for p in fpages:
            pn = p["page_num"]
            for txt in p["removed"]:
                a["boilerplate_removed"][txt] += 1

            if p["failed"]:
                a["failed_pages"].append({"page": pn, "error": p["error"]})
                prev_table = None
                continue

            # OCR fallback page
            if p["ocr_text"] and p["ocr_text"].strip():
                new_el("text", clean_text(p["ocr_text"]), pn, [0, 0, p["width"], p["height"]],
                       source="ocr")
                a["text_blocks"] += 1
                a["ocr_pages"].append(pn)
                prev_table = None
                continue

            items = [("line", l["top"], l["x0"], l) for l in p["lines"]]
            items += [("table", t["bbox"][1], t["bbox"][0], t) for t in p["tables"]]
            items.sort(key=lambda x: (x[1], x[2]))          # TRUE reading order (top->bottom, left->right)

            if not items:
                if p["n_chars"] == 0:
                    a["needs_ocr_pages"].append(pn)         # nothing extractable => likely scanned
                a["empty_pages"].append(pn)
                prev_table = None
                continue

            buf, last_heading = [], None
            emitted_before = len(elements)

            def flush():
                nonlocal buf
                if buf:
                    bbox = _union_bbox([(l["x0"], l["top"], l["x1"], l["bottom"]) for l in buf])
                    new_el("text", _join_lines(buf), pn, bbox)
                    a["text_blocks"] += 1
                    buf = []

            for idx, (kind, _, _, obj) in enumerate(items):
                if kind == "table":
                    flush()
                    last_heading = None
                    rows = _clean_rows(obj["raw"])
                    if not rows:
                        continue

                    cont, reason = check_continuation(prev_table, rows, obj["bbox"], p, idx == 0)
                    if reason in ("header_differs", "column_count_differs", "position_mismatch"):
                        a["continuations_rejected"].append({"page": pn, "reason": reason})

                    if cont:
                        header, table_id = prev_table["header"], prev_table["table_id"]
                        data_rows = rows[1:] if reason == "header_repeated" else rows
                        a["continuation_tables"] += 1
                    else:
                        header = _make_header(rows[0])
                        data_rows = rows[1:]
                        table_counter += 1
                        table_id = f"{doc_id}:t{table_counter}"

                    new_el("table", rows_to_text(data_rows, header), pn, list(obj["bbox"]),
                           table_id=table_id, header=header, raw_table=rows,
                           continued_from_prev_page=cont,
                           continuation_reason=reason if cont else None)
                    a["tables"] += 1
                    prev_table = {"page": pn, "header": header, "ncols": len(header),
                                  "bbox": obj["bbox"], "height": p["height"],
                                  "table_id": table_id, "ends_page": False}
                    continue

                # ---- a text line: heading or body ----
                lvl = heading_level(obj, body, level_map, bold_level)
                if lvl is None:
                    buf.append(obj)
                    last_heading = None
                    continue

                # multi-line heading: same level, directly under the previous heading line
                line_h = obj["bottom"] - obj["top"]
                if (last_heading and not buf and last_heading["level"] == lvl
                        and obj["top"] - last_heading["bottom"] < 0.35 * line_h):
                    el = last_heading["el"]
                    el["content"] += " " + obj["text"]
                    el["bbox"] = _union_bbox([el["bbox"], (obj["x0"], obj["top"], obj["x1"], obj["bottom"])])
                    stack[-1] = (lvl, el["content"])
                    el["section_path"] = [t for _, t in stack]
                    el["section"] = " > ".join(el["section_path"])
                    last_heading["bottom"] = obj["bottom"]
                    continue

                flush()
                while stack and stack[-1][0] >= lvl:
                    stack.pop()
                stack.append((lvl, obj["text"]))
                el = new_el("heading", obj["text"], pn,
                            [round(obj["x0"], 1), round(obj["top"], 1), round(obj["x1"], 1), round(obj["bottom"], 1)],
                            level=lvl)
                a["headings"] += 1
                last_heading = {"el": el, "level": lvl, "bottom": obj["bottom"]}

            flush()

            # only a table that is the LAST thing on its page can continue on the next page
            if items[-1][0] == "table" and prev_table and prev_table["page"] == pn:
                prev_table["ends_page"] = True
            else:
                prev_table = None

            if len(elements) == emitted_before:
                a["empty_pages"].append(pn)

        a["boilerplate_removed"] = dict(a["boilerplate_removed"])
    return elements, audit


# ----------------------------------------------------------------------
# STAGE 4: SAVE + AUDIT
# ----------------------------------------------------------------------
def save_json(obj, out_path):
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
    print(f"Saved -> {out_path}")


def print_audit(audit, file_errors):
    print("\n================ AUDIT ================")
    for fname, a in audit.items():
        print(f"\n{fname}  (doc_id={a['doc_id']})")
        print(f"  pages={a['pages']} | chars={a['chars']} | body font={a['body_font_size']} "
              f"| heading levels={a['heading_font_levels']}")
        print(f"  headings={a['headings']} | text blocks={a['text_blocks']} | tables={a['tables']} "    
              f"| continuation tables={a['continuation_tables']}")
        print(f"  failed pages={a['failed_pages']}")
        print(f"  empty pages={a['empty_pages']} | needs OCR={a['needs_ocr_pages']} | OCR'd={a['ocr_pages']}")
        print(f"  continuations rejected={a['continuations_rejected']}")
        print(f"  boilerplate removed={a['boilerplate_removed']}")
    for e in file_errors:
        print(f"[FILE ERROR] {e['file']}: {e['error']}")


# ----------------------------------------------------------------------
# RUN
# ----------------------------------------------------------------------
if __name__ == "__main__":
    POLICY_DIR = r"D:\Coding Stuff\SupportOps AI\data\policies"
    OUT_DIR = Path(r"D:\Coding Stuff\SupportOps AI\data\processed")

    fetcher = Fetch_data(POLICY_DIR)
    pages = fetcher.fetch_pdf()

    flagged = detect_boilerplate(pages)
    remove_boilerplate(pages, flagged)

    elements, audit = build_elements(pages)
    print_audit(audit, fetcher.file_errors)

    save_json(elements, OUT_DIR / "policies_elements.json")
    save_json({"files": audit, "file_errors": fetcher.file_errors}, OUT_DIR / "policies_audit.json")