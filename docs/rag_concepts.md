****# RAG: The Complete Concepts Guide (Basic → Absolute Root) — v2

Yeh document RAG ke **har concept ko general terms mein** samjhata hai, aur sath mein yeh bhi batata hai ke hamare SupportOps AI project mein woh concept kaise use hoga (ya kyun nahi hoga). Yeh v2 hai — original doc mein jo gaps thay woh sab fill kiye gaye hain taake yeh sach mein **complete** ho.

**Structure:** Foundations → Indexing → Retrieval → Advanced Architectures → Production Concerns → Evaluation → Minor/Peripheral Concepts (names only, for awareness).

---

## What is RAG? (The Big Picture)

**General Concept:**
RAG (Retrieval-Augmented Generation) ek design pattern hai jismein hum ek LLM ko answer generate karne se pehle uski "memory" mein se relevant information dhoondhte hain aur usse dete hain.

**Problem RAG Solves:**
1. **Hallucination** — LLMs confidence se galat cheezein bol dete hain.
2. **Knowledge Cutoff** — LLM ke paas private/company data ka ilm nahi.
3. **Cost of fine-tuning** — har baar naya fact model mein "bake" karne ke liye retrain karna mehnga hai; RAG mein knowledge sirf ek document update se change ho jati hai.

**RAG Ka Formula:**
```
Answer = LLM( Customer Question + Retrieved Relevant Context )
```

**RAG vs Fine-tuning — decision framework:**
Yeh sawal har engineer ko puchna chahiye pehle: knowledge frequently change hoti hai? → RAG. Knowledge stable hai lekin *style/format/behavior* sikhana hai (jaise ek particular tone mein jawab dena)? → Fine-tuning. Dono bhi combine ho sakte hain (fine-tune for behavior, RAG for facts).

**Hamare Project Mein:**
Refund/shipping policies change hoti rehti hain (seller apni policy update karta hai) — is liye RAG sahi choice hai, fine-tuning nahi.

---

## The RAG Pipeline (5 Stages)

```
[Documents] → [Chunking] → [Embeddings] → [Vector DB]   ← (Indexing - one time)
                                                ↑
[User Question] → [Embed Question] → [Search Vector DB] → [Retrieved Chunks] → [LLM] → [Answer]
                                                              (Retrieval - every query)
```

---

# INDEXING PHASE CONCEPTS

---

## Concept 1: Document Loading

**General:**
RAG ki shuruat yahan se hoti hai — raw data sources (PDF, Word, Markdown, Web pages, Databases) se raw text nikalna.

**Formats:**
* PDF → `PyPDFLoader`
* Word → `Docx2txtLoader`
* Web Pages → `WebBaseLoader`
* Markdown → `TextLoader` / `DirectoryLoader`
* Database → Custom SQL queries

**Additional loading concerns (missing from v1):**

**1a. OCR for scanned/image-based documents:** Agar document scanned image hai (na ke actual text PDF), normal loader khali text dega. Tools: `Tesseract`, `PaddleOCR`, ya vision-capable LLMs (image ko directly LLM ko dena aur text nikalwana). Zaroori jab supplier invoices ya scanned contracts jaisi cheezein aati hain.

**1b. Table-specific extraction at load time:** Tables ko plain text mein extract karna unki structure destroy kar deta hai (rows/columns ek dusre mein mix ho jate hain). Tools jaise `Camelot`, `unstructured.io`, ya `pdfplumber` tables ko structured (CSV/JSON-like) form mein nikalte hain.

**1c. Deduplication before indexing:** Agar do documents (ya do versions of the same policy) 95% same hain, dono ko index karna redundant retrieval aur wasted storage deta hai. Hashing (MinHash/SimHash) se near-duplicate documents detect karke sirf latest/canonical version rakhi jati hai.

**Hamare Project Mein:** Hum `policies/` folder se 3 `.md` files load karenge — `DirectoryLoader` ya manual `open()` se. OCR/table extraction is scope se bahar hai kyunki humari policies plain markdown text hain.

---

## Concept 2: Text Splitting / Chunking

Raw document poora LLM mein nahi daal sakte (context window limit + relevance dilution). Isliye document ko chunks mein todte hain.

### 2a. Fixed-Size Chunking (Naive)
Har `chunk_size` characters ke baad naya chunk. Sentence beech mein toot sakta hai.

### 2b. Recursive Character Text Splitter
Pehle `\n\n` (paragraph) par todne ki koshish, phir `\n`, phir `.`, phir space.

### 2c. Semantic Chunking (Intermediate)
Har sentence ka embedding banake, jab 2 consecutive sentences ki meaning bahut alag ho jaye, wahan break.

### 2d. Agentic/Proposition Chunking (Advanced)
LLM se har paragraph ko atomic "proposition" (self-contained fact statement) mein convert karwana.

### 2e. Structure-Aware Chunking (missing from v1)
**General:** Document ki apni structure (markdown `##` headers, HTML tags, numbered sections) ko chunk boundary ke tor par use karna, generic paragraph-break ke bajaye.
```
## Refund Eligibility
...content...
## Processing Time     ← chunk break yahan, header ki wajah se, na ke random paragraph break par
...content...
```
**Why Better:** Aapke policy docs already headers ke sath organized hain — structure ignore karna waste hai jab woh free mein available hai.
**Hamare Project Mein:** Yeh actually humare liye sabse practical baseline honi chahiye, kyunki humari 3 `.md` files already `##` sections mein organized hain (Eligibility, Process, Exceptions, etc.).

### 2f. Sliding Window / Sentence-Window Chunking (missing from v1)
**General:** Retrieval ke liye chota chunk match hota hai, lekin har chunk apne "neighbor" sentences (pehle 2-3, baad ke 2-3) ka reference bhi store karta hai. Jab chunk retrieve hota hai, LLM ko sirf matched sentence nahi, uske aas-paas ka context bhi diya jata hai.
**Why Better:** Chota chunk = precise matching; bara context = LLM ko poora picture milta hai. Best of both.

### 2g. Parent-Document / Hierarchical Chunking (missing from v1)
**General:** Chote "child" chunks index/search ke liye use hote hain (precise matching), lekin har child ek bare "parent" chunk/section se linked hota hai. Match hone par parent return kiya jata hai, na ke sirf chota fragment.
```
Child chunk (indexed): "Electronics must be unopened."
   ↓ linked to
Parent chunk (returned to LLM): poora "Refund Eligibility" section
```
**Why Better:** Search precise rehti hai, lekin LLM ko fragment nahi, poora relevant context milta hai.
**Hamare Project Mein:** Semantic chunking ke sath combine kar sakte hain — child = semantic chunk, parent = poora policy section.

### 2h. Token-Based Chunking (missing from v1)
**General:** Character count ke bajaye actual model tokenizer (jaise `tiktoken`) se chunk size measure karna. Character-based chunking se embedding/LLM ke actual token limit ka andaza nahi hota (1 token ≈ 4 characters English mein, lekin Urdu/Roman-Urdu mein yeh ratio alag hota hai).
**Why Important:** Agar aap character-count par bharosa karte hain, kabhi kabhi chunk token limit se overshoot kar jayega without warning.

### 2i. Contextual Retrieval / Contextualized Chunking (missing from v1 — important, Anthropic technique)
**General:** Chunk ko embed karne se pehle, ek LLM us chunk ke aage ek chota "situating" sentence prepend karta hai jo batata hai yeh chunk kis document/section se hai aur uska context kya hai.
```
Raw chunk: "Items must be returned within 30 days."
Contextualized chunk: "This is from the refund policy's general eligibility section. 
Items must be returned within 30 days."
```
**Why Better:** Isolated chunk ka embedding kabhi kabhi apna context khud nahi carry karta (e.g. "30 days" kis cheez ke liye hai, agar poore document mein multiple "30 days" mentions hon). Contextualizing se retrieval accuracy significantly barh jati hai — practice mein proposition chunking se zyada cost-effective aur impactful maana jata hai.
**Hamare Project Mein:** Tier 3 mein add karne layak — har chunk mein `"[refund_policy.md — Eligibility section] "` jaisa prefix add karke embed karenge.

### 2j. Late Chunking (missing from v1)
**General:** Traditional chunking mein pehle document todte hain, phir har chunk ko alag alag embed karte hain — is se har chunk "isolated" hota hai, poore document ka context nahi janta. Late chunking ismein ulta karta hai: **pehle poora document** ek long-context embedding model se token-level embeddings banata hai, **phir** un token embeddings ko chunks mein group karta hai. Har chunk ka final vector ab poore document ke context se "aware" hota hai.
**Why Better:** Contextual retrieval se milta concept hai, lekin LLM call ki zaroorat nahi — sirf ek achi long-context embedding model chahiye.
**Hamare Project Mein:** Chote documents ke liye overkill hai, lekin awareness rakhni chahiye — agar policies bara documents ban jayein (multi-page legal text), yeh contextual retrieval ka cheaper alternative hoga.

**Summary Table — Chunking:**

| Technique | Complexity | Best For |
|---|---|---|
| Fixed-size | Trivial | Quick prototype only |
| Recursive character | Easy | General-purpose baseline |
| Structure-aware | Easy | Documents with headers/sections (yehi hamare policies) |
| Semantic | Medium | Documents jahan topics paragraph ke beech mix hote hain |
| Sliding window | Medium | Jab matched fragment ke aas-paas context chahiye |
| Parent-document | Medium | Precise search + full context dono chahiye |
| Contextual retrieval | Medium-High | Production-grade accuracy, LLM budget available |
| Proposition/Agentic | High | Atomic fact-heavy content (FAQs) |
| Late chunking | High (infra) | Large documents, no LLM budget for contextualizing |

**Hamare Project Mein — final recommendation:** Structure-aware chunking as the base splitter (respects `##` headers), semantic chunking within long sections, parent-document linking so retrieval returns full context, aur `faq.md` ke liye proposition chunking.

---

## Concept 3: Embeddings

**General:**
Embedding model text ko high-dimensional vector mein convert karta hai; similar meaning wale texts ke vectors kareebi hote hain.

**Types of Embedding Models:**

| Model | Type | Cost | Quality |
|---|---|---|---|
| `all-MiniLM-L6-v2` | Local/HuggingFace | Free | Medium |
| `text-embedding-3-small` | OpenAI API | Paid | High |
| `text-embedding-3-large` | OpenAI API | Paid (expensive) | Very High |
| `BGE-M3` | Local/HuggingFace | Free | Very High |

**Bi-Encoder vs Cross-Encoder:** Bi-Encoder = alag alag embed, fast, retrieval mein use. Cross-Encoder = sath mein ek model se, slow, accurate, re-ranking mein use.

**Additional embedding concepts (missing from v1):**

**3a. Matryoshka Embeddings:** Kuch naye models (jaise OpenAI's `text-embedding-3` family, ya `nomic-embed`) is tarah train hote hain ke unka vector truncate kiya ja sakta hai (e.g. 1536 dimensions ko 256 tak kaat do) bina bohat quality khoye. Isse storage aur search speed trade-off adjust kar sakte ho on demand.

**3b. Quantized Embeddings:** Vectors ko full-precision float32 ke bajaye int8 ya binary mein store karna — storage aur RAM usage drastically kam ho jata hai, thodi si accuracy ki qeemat par. Bade-scale production systems (millions of vectors) mein zaroori.

**3c. Instruction-Tuned Embedding Models:** Kuch models (jaise `bge`, `e5` family) ko chahiye hota hai ke query ko `"query: "` prefix aur document ko `"passage: "` prefix ke sath diya jaye, warna quality bohat kam ho jati hai. Yeh ek common practical bug hai jo docs mein miss ho jata hai.

**3d. Multi-Vector / Late-Interaction Embeddings (ColBERT-style):** Bi-encoder poore text ka **ek** vector banata hai. Multi-vector approach (ColBERT) har token ka alag vector rakhta hai, aur match karte waqt token-level fine-grained comparison karta hai. Bi-encoder se zyada accurate, single-vector se zyada compute/storage heavy — beech ka trade-off hai single-vector aur cross-encoder ke.

**Hamare Project Mein:** Tier 1-2: `all-MiniLM-L6-v2`. Tier 3: `BGE-M3` compare karenge, aur agar `bge`/`e5` use karein toh query/passage prefix zaroor lagayenge — yeh ek chota detail hai jo aksar log miss karte hain.

---

## Concept 4: Vector Database

**General:**
Vector Database "similar vectors dhoondhna" fast banata hai — ANN (Approximate Nearest Neighbor) algorithms (HNSW) use karke.

**Popular Vector DBs:**

| Database | Type | Best For |
|---|---|---|
| **ChromaDB** | Local/Free | Development, small projects |
| **FAISS** (Meta) | Local/Free | Large scale, in-memory |
| **Pinecone** | Cloud/Paid | Production, managed |
| **Weaviate** | Cloud/Self-hosted | Production, hybrid search |
| **Qdrant** | Cloud/Self-hosted | Production, filtering |

**HNSW (Hierarchical Navigable Small World):** Vectors multiple "layers" mein arrange hote hain — top layer mein kam nodes (long jumps), bottom layer mein sab nodes (fine search). Search funnel ki tarah upar se neeche aati hai — brute-force se bohat fast, lekin "approximate" (100% accurate nahi).

**Other index types worth knowing (missing from v1):**
* **IVF (Inverted File Index):** Vectors ko clusters mein bant deta hai; search sirf relevant clusters mein hoti hai. HNSW se kam memory, thoda slower.
* **PQ (Product Quantization):** Vectors ko chote sub-vectors mein compress karta hai — storage bohat kam ho jati hai, accuracy thodi kam.
* In practice, production vector DBs (Pinecone, Qdrant) inme se combination use karte hain (e.g. HNSW + PQ) — aapko khud implement nahi karna, bas yeh janna hai ke "index type" ek config choice hai jo speed/memory/accuracy trade-off control karta hai.

**Hamare Project Mein:** **ChromaDB** — local, free, no API key, development ke liye perfect.

---

# RETRIEVAL PHASE CONCEPTS

---

## Concept 5: Query Processing

User ka sawal bhi usi embedding model se vector mein convert hota hai jo indexing mein use hua tha.

### 5a. Naive Query
Original sawal seedha embed karke search.

### 5b. Query Expansion
LLM se sawal ko 3-5 alag ways mein rewrite karke, sab ke liye retrieve karna.

### 5c. HyDE (Hypothetical Document Embeddings)
LLM se pehle ek hypothetical ideal answer generate karke, us answer ko embed karna (sawal ki jagah).

### 5d. Query Decomposition (missing from v1)
**General:** Query Expansion "same sawal ko alfaz badal ke" dobara likhta hai. Decomposition **alag** hai — ek complex, multi-part sawal ko chote **independent sub-questions** mein tor deta hai, har ek ko alag retrieve karta hai, phir combine karta hai.
```
Original: "Is order #1234 refund-eligible, and how long will a replacement take?"
Decomposed:
  → Sub-Q1: "What is the refund eligibility policy?"
  → Sub-Q2: "What is order #1234's current status?" (needs DB tool, not RAG)
  → Sub-Q3: "What is the replacement shipping timeline?"
```
**Hamare Project Mein:** Yeh exactly Concept 12 (Agentic RAG) ke sath overlap karta hai — jab customer ek message mein 2 alag sawal puche.

### 5e. Step-Back Prompting (missing from v1)
**General:** Pehle ek zyada **general/abstract** version ka sawal puch ke broader context retrieve karo, phir specific sawal ka jawab do us broader context ke sath.
```
Specific: "Can I return a dress I bought during the Eid sale?"
Step-back: "What is the general return policy?" ← retrieve this first for broader grounding
Then answer the specific case using that broader context.
```
**Why:** Kabhi kabhi specific sawal ka direct embedding niche-specific chunk se match nahi karta, lekin general policy chunk se karta hai.

**Hamare Project Mein:** Tier 3+ mein Query Expansion/HyDE ke sath ek option ke tor par consider karenge.

---

## Concept 6: Similarity Search

### 6a. Cosine Similarity (Naive)
Do vectors ke beech ka angle measure karta hai.

### 6b. MMR (Maximal Marginal Relevance)
Similarity + diversity dono consider karta hai.

### 6c. Hybrid Search (Dense + Sparse)
Dense (embedding-based) + Sparse (BM25/keyword) ko Reciprocal Rank Fusion (RRF) se merge karta hai.

**Additional concept (missing from v1):**

**6d. Distance Metric Choice:** "Cosine similarity" is doc mein default maana gaya hai, lekin yeh khud ek choice hai:
* **Cosine:** Sirf angle/direction dekhta hai, magnitude ignore karta hai — text embeddings ke liye sabse common.
* **Dot Product:** Angle + magnitude dono — jab embedding model already normalized vectors deta ho, dot product aur cosine same result dete hain (aur dot product compute karna thoda fast hota hai).
* **Euclidean (L2) Distance:** Actual straight-line distance — kam common text ke liye, zyada common image/numeric embeddings ke liye.
**Practical note:** Aapki embedding model ki documentation dekh ke pata chalta hai woh kis metric ke liye optimize hui hai (`all-MiniLM` cosine ke liye tuned hai).

**Hamare Project Mein:** Tier 1 default: Cosine Similarity. Tier 2: MMR. Tier 3: Hybrid Search (customer order IDs/tracking numbers ke exact match ke liye zaroori).

---

## Concept 7: Re-Ranking

Initial retrieval (Top-K se 10 chunks) fast lekin imprecise. Cross-Encoder model un 10 ko individually score karke best upar late aata hai.

**Model:** `cross-encoder/ms-marco-MiniLM-L-6-v2` (free, HuggingFace).

**Additional note (missing from v1):** Modern re-ranking APIs bhi available hain jo cross-encoder se aur behtar hote hain — jaise **Cohere Rerank** ya **Jina Reranker** — agar local free model se better accuracy chahiye ho aur thodi si API cost acceptable ho.

**Hamare Project Mein:** Tier 2 mein add karenge.

---

## Concept 8: Context Window Management

Retrieved chunks LLM ko dene se pehle token limit ensure karna. **"Lost in the Middle"** phenomenon — LLMs prompt ke shuru/akhir mein di gayi info ko beech se zyada acha use karte hain.

**Techniques:** Top-3 chunks lo, chunks summarize karo, `max_tokens` set karo, sabse relevant chunk top/bottom par rakho.

**Hamare Project Mein:** Sirf Top-3 relevant chunks, sabse relevant sabse pehle.

---

## Concept 9: RAG Fusion

Query Expansion + Hybrid Search + Re-Ranking = RAG Fusion. Multiple query versions se retrieve karke RRF se merge.

**Hamare Project Mein:** Tier 3 ka final form.

---

# ADVANCED RAG ARCHITECTURES

Yahan tak jo discuss hua woh sab ek **fixed, linear pipeline** hai. Advanced RAG mein system khud decisions leta hai.

---

## Concept 10: Self-RAG
LLM khud decide karta hai "retrieve karun ya nahi", aur reflection tokens (`[Relevant]`, `[Supported]`, `[Useful]`) generate karke apna answer verify karta hai.

## Concept 11: Corrective RAG (CRAG)
Retrieved chunks ko evaluator score karta hai: Correct / Ambiguous / Incorrect. Incorrect hone par local docs discard karke web search fallback.

## Concept 12: Agentic RAG
LLM-based agent decide karta hai kis source/tool se information laani hai, multi-step (multi-hop) bhi le sakta hai.

## Concept 13: GraphRAG
Documents se Knowledge Graph banata hai (entities + relationships), multi-hop questions answer kar sakta hai jo cosine similarity se solve nahi hote.

## Concept 14: Adaptive RAG
Query complexity judge karke path decide karta hai — simple query direct LLM, moderate single-step retrieval, complex multi-step/agentic.

## Concept 15: Multi-modal RAG
Images/tables/charts ko bhi retrieve/understand karna — CLIP-style embeddings, VLM captioning, table-aware chunking.

**Missing advanced architectures (not in v1):**

## Concept 15a: RAPTOR (Recursive Abstractive Processing for Tree-Organized Retrieval)
**General:** Documents ke chunks ko cluster karke, har cluster ka ek summary banaya jata hai (LLM se), phir un summaries ko bhi cluster/summarize kiya jata hai — is tarah ek **tree** banti hai jahan bottom layer mein raw chunks hain aur upar ki layers mein zyada abstract summaries. Query ke hisaab se system decide karta hai ke fine-grained chunk chahiye ya high-level summary.
**Why Better:** "What is this whole policy document about?" jaise broad sawal ke liye upar ki summary layer se jawab milta hai; "What's the exact refund window for electronics?" jaisa specific sawal ke liye neeche ki raw chunk layer use hoti hai.
**Hamare Project Mein:** Chote 3-document setup ke liye overkill, lekin agar policies bade multi-section documents ban jayein (jaise ek 50-page seller agreement), RAPTOR bohat useful hoga.

## Concept 15b: FLARE (Forward-Looking Active Retrieval)
**General:** Normal RAG ek baar retrieve karta hai, phir poora answer generate karta hai. FLARE **generation ke doran** retrieve karta hai — jab model apna next sentence likhte waqt uncertain hota hai (low confidence tokens predict karta hai), woh rukta hai, ek naya retrieval karta hai, aur phir continue karta hai.
**Why Better:** Lambe, multi-fact answers ke liye — jahan ek hi upfront retrieval sab kuch cover nahi kar sakta.
**Hamare Project Mein:** Humare short policy-answer use-case ke liye zaroori nahi (answers chote hain), lekin conceptually samajhna zaroori hai for interviews/depth.

## Concept 15c: Iterative / Multi-Hop Retrieval (IRCoT — Interleaved Retrieval with Chain-of-Thought)
**General:** Reasoning aur retrieval ko interleave karta hai — har reasoning step ke baad ek naya retrieval hota hai jo us step se inform hota hai, phir agla reasoning step.
```
Step 1: "First I need refund eligibility" → retrieve → get eligibility rule
Step 2: "Given eligibility, now I need the exception for electronics" → retrieve (informed by step 1)
Step 3: Combine → final answer
```
**Difference from Agentic RAG (Concept 12):** Agentic RAG ek agent tools choose karta hai; IRCoT specifically reasoning-chain ke har step ke sath retrieval ko tightly couple karta hai.

## Concept 15d: Long-Context-as-Alternative-to-RAG
**General:** Modern LLMs (200K+ token context windows) itne bade ho gaye hain ke chote knowledge bases ke liye **poora document seedha prompt mein daalna** kabhi kabhi RAG se better/simpler results deta hai — chunking/retrieval ki complexity hi nahi chahiye.
**Trade-off:** Zyada tokens = zyada cost + latency per query, aur bara context window "lost in the middle" problem se pura immune nahi hota.
**Hamare Project Mein:** Yeh ek important design question hai jo explicitly consider karni chahiye: humari 3 policy files agar chotti hain (kuch hazar words), toh Tier 1 ke liye RAG banane se pehle yeh sochna chahiye ke kya seedha poora context LLM ko dena hi kaafi tha. **Answer:** Hum RAG isliye bana rahe hain kyunki (a) learning/portfolio goal hai, (b) production mein multiple sellers/documents scale karenge, (c) cost — har query par poora context bhejna RAG se zyada expensive hai bade scale par.

---

# PRACTICAL & PRODUCTION CONCERNS

---

## Concept 16: Metadata Filtering
Har chunk ke sath structured metadata (`source_file`, `date`, `category`, `region`) — similarity search + hard filters combine.

## Concept 17: Prompt Engineering for RAG
Chunks numbered/delimited karo, "sirf context se answer do" instruction do, relevant chunk top/bottom par, few-shot examples.

## Concept 18: Production Concerns
Caching, Latency, Cost, Monitoring & Logging, Guardrails against Prompt Injection.

**Missing production concerns (not in v1):**

**18a. Semantic Caching:** Basic caching exact string match par kaam karta hai ("what's your return policy" cached only for that exact text). Semantic caching incoming query ka embedding banata hai aur agar woh **kisi pehle-cached query ke embedding se close** hai (jaise "return policy kya hai" vs "what's your return policy"), cached answer return kar deta hai — bina naya LLM call kiye.
**Hamare Project Mein:** Very relevant — customers same sawal alag alag alfaz mein (Urdu/English mix) puchte hain; exact-match caching kaam nahi karega, semantic caching karega.

**18b. Access-Control / Permission-Aware Retrieval:** SupportOps multi-tenant hai (multiple sellers) — critical hai ke Seller A ke retrieval mein kabhi Seller B ki policy leak na ho. Yeh metadata filtering (`seller_id` filter mandatory on every query) se enforce hota hai, lekin explicitly design concern ke tor par yaad rakhna zaroori hai — ek bug isse ek data-leak/security incident bana sakta hai.

**18c. Incremental Re-Indexing:** Jab seller apni refund policy update karta hai, poora vector DB dobara se banana wasteful hai. Incremental indexing sirf changed/new documents ko re-chunk/re-embed karta hai, aur purane version ke chunks ko delete/replace karta hai.

**18d. PII Redaction Before Embedding:** Agar retrieved documents mein kabhi customer PII (phone number, address, CNIC) ho, use embed/store karne se pehle redact karna chahiye — warna woh data vector DB mein permanently baith jata hai aur kisi aur query se accidentally retrieve ho sakta hai.

## Concept 19: Orchestration Frameworks

| Framework | Strength |
|---|---|
| **LangChain** | Sabse popular, bohat integrations, chains + agents |
| **LlamaIndex** | RAG-focused specifically, indexing pe strong |
| **Haystack** | Production-grade pipelines, enterprise use |
| **LangGraph** *(missing from v1 — humara khud ka chosen framework)* | Graph-based state machine orchestration — agent ke multi-step, cyclic flows (retry, escalation loops) ke liye LangChain se zyada explicit control deta hai |
| **DSPy** *(missing from v1)* | Prompts ko hand-write karne ke bajaye **programmatically optimize** karta hai — aap pipeline ka structure define karte hain, DSPy khud best prompts/few-shot examples "compile" kar deta hai based on your data |

**Hamare Project Mein:** Tier 1-2 raw Python/ChromaDB (fundamentals ke liye), Tier 3-4 mein LangGraph (already project ka chosen orchestration tool — Phase 4.7).

---

# EVALUATION CONCEPTS

---

## Concept 20: RAG Evaluation Metrics

### 20a. Retrieval Metrics
* **Hit Rate:** Relevant chunk Top-K mein aya ya nahi.
* **MRR (Mean Reciprocal Rank):** Relevant chunk kaunse rank par aya.

### 20b. Generation Metrics (RAGAS Framework)
* **Faithfulness:** Answer sirf retrieved context se hai ya hallucinated.
* **Answer Relevancy:** Answer user ke sawal se relevant hai.
* **Context Precision:** Retrieved chunks mein se kitne useful thay.
* **Context Recall:** Zaroori information sab retrieve hui ya kuch miss hua.

**Missing evaluation concepts (not in v1):**

**20c. LLM-as-a-Judge:** RAGAS ke metrics ke peeche yehi technique hai, lekin standalone samajhna zaroori hai — ek **doosra, alag LLM call** aapke system ke answer ko score/grade karta hai (kabhi kabhi ek rubric ke against, kabhi ek "gold" reference answer ke against). Sasta aur scalable hai human evaluation se, lekin khud bhi biased/imperfect ho sakta hai (isliye "judge" model periodically human-check hona chahiye).

**20d. Golden Dataset Construction:** Evaluation sirf tab meaningful hai jab aapke paas ek acha **golden test set** ho — representative real (ya realistic) questions with correct expected answers/sources. Yeh khud ek skill hai: edge cases, ambiguous cases, aur normal cases sab include hone chahiye, sirf easy cases nahi.
**Hamare Project Mein:** Yeh Phase 1.5 ("Golden test scenarios as fixtures") aur 0.7 mein already planned hai — jaise-jaise real conversations aayengi, synthetic golden set unse replace hoga.

**20e. Regression Testing on Pipeline Changes:** Jab bhi chunking strategy, embedding model, ya prompt change karo, poora golden test set dobara run karna chahiye — taake pata chale kya improvement genuinely hui ya kisi aur cheez ko break kar diya. Isse "silent regressions" avoid hote hain.

**Hamare Project Mein:** Phase 6 mein RAGAS use karenge; Phase 2 mein bhi manual + basic automated evaluation. Har chunking/embedding change ke baad regression run karna standard practice honi chahiye — Phase 4.8 ki prompt-versioning ke sath tie hoti hai.

---

# MINOR / PERIPHERAL CONCEPTS (names only — good to recognize, not deep-dive priority right now)

Yeh woh concepts hain jo RAG ke universe mein exist karte hain lekin humare project ke scale/scope ke liye deep-dive zaroori nahi — sirf naam pehchaanne ke liye taake kahin mention ho toh pata ho yeh kya hai:

- **SPLADE** — sparse retrieval ka ek learned/neural version (BM25 se zyada smart keyword matching)
- **ColBERTv2** — Concept 3d ka production-ready implementation
- **Self-Query Retriever** — LLM khud query se metadata filters extract karta hai (e.g. "electronics refunds" se `category=electronics` filter khud nikal leta hai)
- **Contextual Compression** — retrieve karne ke baad, chunk ke andar se bhi sirf directly-relevant sentences nikal ke LLM ko dena (chunk ko aur chota karna post-retrieval)
- **Small-to-Big Retrieval** — Parent-document chunking (2g) ka doosra naam
- **Time-Weighted Retrieval** — recent documents ko purane se zyada weight dena (news/updates-heavy use cases mein)
- **Ensemble Retrievers** — multiple retrieval methods (dense + sparse + keyword) ko parallel chala ke unke results ko combine karna (Hybrid Search, 6c, iska ek specific case hai)
- **Cross-Lingual RAG** — query ek language mein, documents doosri mein (relevant future consideration humare liye — Urdu queries, English policy docs)
- **Streaming RAG Responses** — retrieval ke baad answer ko token-by-token stream karna (UX concern, retrieval logic se independent)
- **Text-to-SQL RAG** — natural language query ko SQL mein convert karke structured DB se "retrieve" karna (yeh actually humare order-lookup tool, Phase 3, ka underlying concept hai)
- **Vector DB Index Tuning (IVF/PQ params)** — index build-time hyperparameters, sirf bade-scale (millions+ vectors) par matter karte hain
- **Embedding Drift** — jab embedding model version update hoti hai, purani aur nayi embeddings compatible nahi rehti — poora re-index karna parta hai
- **Chunk Size Hyperparameter Search** — chunk size/overlap ko systematically vary karke best combination dhoondna (grid search jaisa, chunking ke liye)
- **RAG Safety / Jailbreak-via-Retrieved-Content** — Concept 18's prompt injection guardrail ka specific naam jab attack retrieved document ke andar chhupi ho

---

# Summary Table: Kya Kab Use Karein (Updated)

| Scenario | Recommended Technique |
|---|---|
| Starting out / Prototype | Structure-aware/Recursive Chunking + MiniLM + ChromaDB + Cosine |
| Documents have clear headers/sections | Structure-Aware Chunking |
| Need better chunk quality within sections | Semantic Chunking |
| Need chunk to carry document context | Contextual Retrieval (2i) |
| Need precise search + full context | Parent-Document Chunking |
| Need better ranking | Cross-Encoder Re-Ranker |
| User queries are vague | HyDE or Query Expansion |
| User asks multi-part questions | Query Decomposition |
| User mentions exact keywords/IDs | Hybrid Search (BM25 + Dense) |
| Retrieved docs might be wrong/missing | Corrective RAG (CRAG) |
| Some queries don't need retrieval at all | Self-RAG or Adaptive routing |
| Need live/dynamic data + multi-step reasoning | Agentic RAG |
| Questions need connecting multiple documents | GraphRAG |
| Very long, hierarchical documents | RAPTOR |
| Long, multi-fact answers | FLARE / IRCoT |
| Documents have images/tables | Multi-modal RAG |
| Very small knowledge base, big-context model available | Consider skipping RAG (2j / long-context alternative) |
| Production system | RAG Fusion + Metadata Filtering + Semantic Caching + Access Control + RAGAS Evaluation |

---

# The Learning Path (Root → Advanced), Updated

1. **Build Tier 1 (Naive/Structure-Aware RAG)** — Concepts 1, 2a/2b/2e, 3, 4, 6a.
2. **Add Intermediate quality** — Concepts 2c, 2f, 2g, 6b, 7 (Semantic Chunking, Sliding Window, Parent-Document, MMR, Re-Ranking).
3. **Add Advanced retrieval** — Concepts 5b/5c/5d/5e, 6c, 9, 2i (Query Expansion, HyDE, Decomposition, Step-Back, Hybrid Search, RAG Fusion, Contextual Retrieval).
4. **Add decision-making** — Concepts 10, 11, 14 (Self-RAG, CRAG, Adaptive RAG).
5. **Add agentic behavior** — Concept 12 (Agentic RAG), 15c (Iterative multi-hop).
6. **Specialize as needed** — Concepts 13, 15, 15a, 15b (GraphRAG, Multi-modal, RAPTOR, FLARE) — only when data actually needs it.
7. **Production-harden** — Concepts 16-19 including 18a-d (Metadata Filtering, Prompt Engineering, Semantic Caching, Access Control, Incremental Indexing, PII Redaction, Orchestration).
8. **Measure everything** — Concept 20 including 20c-e (Evaluation, LLM-as-Judge, Golden Dataset, Regression Testing) — runs alongside every stage, not just at the end.
