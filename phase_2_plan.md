# Phase 2: RAG Mastery Plan (Basic → Advanced)

**Philosophy:** Hum sirf ek RAG banayenge nahi — hum **3 versions** banayenge (Naive → Intermediate → Advanced), apne test scenarios par results compare karenge, aur har jagah evaluate karenge. Aap end mein RAG expert ban jayenge.

---

## The 3 Tiers We Will Build

| Tier | Name | Techniques Used |
|---|---|---|
| **Tier 1** | Naive RAG | Fixed Chunking, Basic Embeddings, Cosine Similarity |
| **Tier 2** | Intermediate RAG | Semantic Chunking, Re-ranking, Metadata Filtering |
| **Tier 3** | Advanced RAG | HyDE, Query Expansion, Hybrid Search, RAG Fusion |

---

## Tier 1: Naive RAG (Foundation)

Yeh sabse basic RAG hai. Isko samajh lena mandatory hai.

### Concept 1.1: Document Loading
**Kya hai:** Policy folder ke sare `.md` files ko Python mein read karna.
**Implementation:** Manually `open()` se files parho, ya `LangChain`'s `DirectoryLoader`.

### Concept 1.2: Fixed-Size Chunking
**Kya hai:** Poore document ko ek fixed size mein todna. Jaise har 300 characters par ek naya chunk.
**Flaw:** Ek sentence beech mein toot sakta hai, meaning khrab hoti hai.
**Parameters:** `chunk_size=300`, `chunk_overlap=50` (overlap se meaning ka connection rahta hai).
**Implement karein:** `RecursiveCharacterTextSplitter` (LangChain).

### Concept 1.3: Dense Embeddings (Semantic)
**Kya hai:** Text ko numbers mein convert karna. Similar meaning = similar numbers.
**Tech:** `sentence-transformers` library ka `all-MiniLM-L6-v2` model (free + local).
**Why this model:** Chota, fast, aur bilkul theek hai basic RAG ke liye.

### Concept 1.4: Vector Store (ChromaDB)
**Kya hai:** Vectors ko ek searchable database mein save karna.
**Tech:** ChromaDB (local, free, no API key needed).

### Concept 1.5: Naive Retrieval (Top-K)
**Kya hai:** Customer ka sawal embed karo, aur database se Top-3 sabse milte julte chunks nikalo.
**Method:** Cosine Similarity (simple distance between vectors).

**✅ Evaluation Tier 1:**
- Kya relevant chunks wapis aye? (Manual check)
- Kya irrelevant chunks bhi aye? (False Positives)
- `Hit Rate` aur `MRR` (Mean Reciprocal Rank) measure karo.

---

## Tier 2: Intermediate RAG (Smarter Retrieval)

Yahan hum Tier 1 ki kamzoriyon ko fix karenge.

### Concept 2.1: Semantic Chunking
**Kya hai:** Fixed size ki jagah, hum text ko **meaning** ke mutabiq todenge. Jab topic change ho, naya chunk start ho.
**Flaw Fixed:** Ab sentence beech mein nahi tutega.
**Implement:** `SemanticChunker` from LangChain.

### Concept 2.2: Metadata Filtering
**Kya hai:** Har chunk ke sath us ka source store karna (e.g., `source: "refund_policy.md"`).
**Use:** Agar customer refund ke baare mein pooche, hum pehle se filter laga sakte hain ke sirf `refund_policy.md` ke chunks hi dhoondhna.

### Concept 2.3: Re-Ranking (Cross-Encoder)
**Kya hai:** Top-K results aane ke baad, unhe ek **dusre, slower-but-smarter model** se dobara rank karna.
**Why:** Initial retrieval (Bi-Encoder) fast hota hai lekin imprecise. Re-ranker (Cross-Encoder) slow hai lekin bohat accurate.
**Implement:** `cross-encoder/ms-marco-MiniLM-L-6-v2` model.

**✅ Evaluation Tier 2:**
- Kya Semantic Chunking ne Tier 1 se behtar results diye? (Compare chunks)
- Kya Re-Ranking ne top result ko improve kiya? (Rank comparison)

---

## Tier 3: Advanced RAG (Expert Level)

### Concept 3.1: HyDE (Hypothetical Document Embeddings)
**Kya hai:** Customer ka sawal hum seedha embed nahi karte. Pehle LLM se ek **hypothetical ideal answer** generate karate hain, phir us answer ko embed karke search karte hain.
**Why:** Sawal aur answer ka embedding space same nahi hota. HyDE is gap ko close karta hai.

### Concept 3.2: Query Expansion
**Kya hai:** Ek customer sawal ko LLM se 3-4 alag-alag ways mein rewrite karana aur sab ke results lena.
**Example:** "My package is late" → Expanded to: "delayed shipment", "package not arrived", "missed delivery date".

### Concept 3.3: Hybrid Search (Dense + Sparse)
**Kya hai:** Dense embeddings (semantic) ke saath BM25 (keyword search) milana. Dono ke results ko combine karna.
**Why:** Dense search meaning samajhta hai. Sparse/BM25 exact keywords (jaise order IDs, tracking numbers) dhoondhta hai.

### Concept 3.4: RAG Fusion
**Kya hai:** Query Expansion + Multiple retrievals + Reciprocal Rank Fusion (RRF) se sab results ko merge aur re-rank karna.
**Why:** Yeh aaj kal production systems mein sab se powerful technique hai.

**✅ Evaluation Tier 3:**
- RAGAS Framework (Faithfulness, Answer Relevancy, Context Precision, Context Recall) se automated evaluation.
- Tier 1 vs Tier 2 vs Tier 3 ka side-by-side comparison table.

---

## Tech Stack for Phase 2

| Component | Library |
|---|---|
| Document Loading | LangChain `DirectoryLoader` |
| Chunking | `RecursiveCharacterTextSplitter`, `SemanticChunker` |
| Embeddings | `sentence-transformers` (HuggingFace, local/free) |
| Vector DB | `ChromaDB` |
| Re-Ranking | `sentence-transformers` cross-encoder |
| Evaluation | `RAGAS` |

> [!IMPORTANT]
> Kya yeh plan aapko pasand aaya? Agar aap agree karte hain toh hum **Tier 1, Concept 1.1 (Document Loading)** se shuru karte hain, main concept samjhaunga aur aap code karenge!
