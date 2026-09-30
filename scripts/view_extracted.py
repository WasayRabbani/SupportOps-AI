import json
from pathlib import Path
from collections import defaultdict

INPUT_FILE = Path("data/processed/policies_elements.json")
OUTPUT_FILE = Path("data/processed/policies_readable.txt")


def convert_to_txt():
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Group elements by PDF file
    files = defaultdict(list)

    for element in data:
        file_name = element.get("file_name", "unknown.pdf")
        files[file_name].append(element)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as out:

        for file_name, elements in files.items():

            out.write("=" * 80 + "\n")
            out.write(f"FILE: {file_name}\n")
            out.write("=" * 80 + "\n\n")

            # Preserve extraction order
            elements.sort(key=lambda x: x.get("seq", 0))

            current_page = None

            for element in elements:

                page = element.get("page_num")

                if page != current_page:
                    current_page = page

                    out.write("\n" + "-" * 60 + "\n")
                    out.write(f"PAGE {page}\n")
                    out.write("-" * 60 + "\n\n")

                element_type = element.get("type")
                content = element.get("content", "").strip()

                if not content:
                    continue

                if element_type == "heading":
                    level = element.get("level", 1)
                    out.write(f"\n{'#' * level} {content}\n\n")

                elif element_type == "table":
                    out.write("\n[TABLE]\n")
                    out.write(content)
                    out.write("\n[/TABLE]\n\n")

                else:
                    out.write(content)
                    out.write("\n\n")

    print(f"Readable file created: {OUTPUT_FILE}")


if __name__ == "__main__":
    convert_to_txt()