# RAG: Complete Concepts Guide (Basic → Advanced)

Yeh document RAG ke **har concept ko general terms mein** samjhata hai, aur sath mein yeh bhi batata hai ke hamare SupportOps AI project mein woh concept kaise use hoga.

---

## What is RAG? (The Big Picture)

**General Concept:**
RAG (Retrieval-Augmented Generation) ek design pattern hai jismein hum ek LLM (jaise GPT, Gemini, Claude) ko answer generate karne se pehle uski "memory" mein se relevant information dhoondhte hain aur usse dete hain.

**Problem RAG Solves:**
LLMs ke paas 2 badi problems hain:
1. **Hallucination:** Woh confidence se galat cheezein bol dete hain.
2. **Knowledge Cutoff:** Unke paas aapke private/company data ka koi ilm nahi.

**RAG Ka Formula:**
```
Answer = LLM( Customer Question + Retrieved Relevant Context )
```

**Hamare Project Mein:**
Agar customer puchay "Kya mujhe damaged item ka refund milega?", LLM ko pata nahi hamari company ki refund policy kya hai. RAG pehle hamare `refund_policy.md` se relevant rules nikalega aur LLM ko dega. LLM phir us policy ke mutabiq jawab dega.

---

## The RAG Pipeline (5 Stages)

```
[Documents] → [Chunking] → [Embeddings] → [Vector DB]   ← (Indexing - one time)
                                                ↑
[User Question] → [Embed Question] → [Search Vector DB] → [Retrieved Chunks] → [LLM] → [Answer]
                                                              (Retrieval - every query)
```

RAG ke 2 main phases hain:
1. **Indexing Phase** (Ek baar hota hai — setup ke waqt)
2. **Retrieval Phase** (Har query par hota hai)

---

# INDEXING PHASE CONCEPTS

---

## Concept 1: Document Loading

**General:**
RAG ki shuruat yahan se hoti hai. Hum apne data sources (PDF, Word, Markdown, Web pages, Databases) se raw text nikalte hain. Yeh step ensure karta hai ke raw data Python mein available ho.

**Formats:**
* PDF → `PyPDFLoader`
* Word → `Docx2txtLoader`
* Web Pages → `WebBaseLoader`
* Markdown → `TextLoader` / `DirectoryLoader`
* Database → Custom SQL queries

**Hamare Project Mein:**
Hum `policies/` folder se 3 `.md` files (`refund_policy.md`, `shipping_policy.md`, `faq.md`) load karenge. Yeh hoga `DirectoryLoader` ya manually `open()` se.

---

## Concept 2: Text Splitting / Chunking

**General:**
Raw document poora LLM mein nahi daal sakte kyunki:
* LLMs ka context window limit hota hai (tokens ki limit).
* Pura document dene se LLM confuse hota hai — sirf relevant part chahiye.

Isliye document ko **chotay pieces (chunks)** mein toda jata hai.

### 2a. Fixed-Size Chunking (Naive)
**General:** Har `chunk_size` characters ke baad naya chunk. Simple lekin dumb.
```
"Our return policy allows returns within 30 days of delivery. Items must be unused. 
Electronics must be unopened..."
         ↓ chunk_size=50, overlap=10
Chunk 1: "Our return policy allows returns within 30 days"
Chunk 2: "30 days of delivery. Items must be unused. Electr"  ← Beech mein cut!
```
**Problem:** Sentence beech mein toot sakta hai, meaning destroy ho jati hai.
**Hamare Project Mein:** Yeh Tier 1 (Naive RAG) mein use karenge as a baseline.

### 2b. Recursive Character Text Splitter
**General:** Fixed-size se smart. Pehle `\n\n` (paragraph) par todne ki koshish karta hai, phir `\n`, phir `.`, phir space. Agar koi bhi nahi mila toh characters par todhta hai.
**Hamare Project Mein:** Tier 1 mein yeh use karenge kyunki Markdown mein paragraphs hain.

### 2c. Semantic Chunking (Intermediate)
**General:** Har sentence ka embedding banata hai aur jab 2 consecutive sentences ki meaning bahut alag ho jaye, wahan chunk break karta hai.
```
"Returns allowed within 30 days."  → Topic: Returns
"Items must be in original condition." → Topic: Returns  ← Same topic, no break
"Our shipping partner is FedEx."  → Topic: Shipping  ← Different topic, BREAK here!
```
**Why Better:** Har chunk ek complete idea contain karta hai.
**Hamare Project Mein:** Yeh Tier 2 (Intermediate RAG) mein use karenge.

### 2d. Agentic/Proposition Chunking (Advanced)
**General:** LLM se har paragraph ko ek self-contained "proposition" (fact statement) mein convert karwana.
```
Original: "Gold members, who spend over $2000 lifetime, get free shipping."
Proposition: "Gold members get free shipping."
Proposition: "A customer becomes Gold member after $2000 lifetime spend."
```
**Why Better:** Retrieval bohat precise hoti hai kyunki har chunk ek atomic fact hai.
**Hamare Project Mein:** Tier 3 mein explore karenge.

---

## Concept 3: Embeddings

**General:**
Embedding ek AI model hai jo text ko ek **high-dimensional vector** (numbers ki list) mein convert karta hai. Iska jadoo yeh hai ke similar meaning wale texts ke vectors math mein bhi kareebi hote hain.

```
"Damaged item"      → [0.12, -0.87, 0.34, ...]
"Broken product"    → [0.11, -0.85, 0.36, ...]  ← Kareebi (close) vectors!
"Shipping address"  → [0.91,  0.23, -0.67, ...] ← Door (far) vectors!
```

### Types of Embedding Models:

| Model | Type | Cost | Quality |
|---|---|---|---|
| `all-MiniLM-L6-v2` | Local/HuggingFace | Free | Medium (great for start) |
| `text-embedding-3-small` | OpenAI API | Paid | High |
| `text-embedding-3-large` | OpenAI API | Paid (expensive) | Very High |
| `BGE-M3` | Local/HuggingFace | Free | Very High |

**Bi-Encoder vs Cross-Encoder:**
* **Bi-Encoder:** Document aur question alag alag embed hote hain, phir compare kiye jate hain. **Fast** lekin less accurate. Retrieval mein use hota hai.
* **Cross-Encoder:** Document aur question ek sath ek model mein jaate hain. **Slow** lekin very accurate. Re-ranking mein use hota hai.

**Hamare Project Mein:**
* Tier 1 & 2: `all-MiniLM-L6-v2` (free, local, kaafi hai).
* Tier 3: `BGE-M3` ya OpenAI embeddings se compare karenge.

---

## Concept 4: Vector Database

**General:**
Regular databases (SQL) numbers (vectors) ke liye efficient nahi hain. Vector Database vectors ko is tarah store karta hai ke "similar vectors dhoondhna" bohat fast ho.

### Popular Vector DBs:

| Database | Type | Best For |
|---|---|---|
| **ChromaDB** | Local/Free | Development, small projects |
| **FAISS** (by Meta) | Local/Free | Large scale, in-memory |
| **Pinecone** | Cloud/Paid | Production, managed |
| **Weaviate** | Cloud/Self-hosted | Production, hybrid search |
| **Qdrant** | Cloud/Self-hosted | Production, filtering |

**Hamare Project Mein:**
Hum **ChromaDB** use karenge. Yeh local chal jata hai, koi API key nahi chahiye, aur development ke liye perfect hai.

---

# RETRIEVAL PHASE CONCEPTS

---

## Concept 5: Query Processing

Jab user sawal karta hai, usse bhi usi embedding model se vector mein convert karte hain jo indexing mein use kiya tha. Is vector se phir Vector DB mein search hoti hai.

### 5a. Naive Query (Basic)
User ka original sawal seedha embed karke search karo.
**Problem:** "My laptop is broken" aur "Defective electronics" ka matlab same hai lekin user ke words policy words se match nahi karenge perfectly.

### 5b. Query Expansion (Intermediate/Advanced)
LLM se user ke original sawal ko 3-5 alag ways mein rewrite karana, phir sab ke liye retrieval karna.
```
Original: "My package is late"
Expanded:
  → "delayed shipment policy"
  → "package not arrived on time"
  → "missed estimated delivery date compensation"
```
**Why:** Zyada angles cover hote hain, better chunks milte hain.
**Hamare Project Mein:** Tier 3 mein use karenge.

### 5c. HyDE (Hypothetical Document Embeddings) (Advanced)
**General:** User ke sawal ko directly embed karne ki jagay, pehle LLM se ek **hypothetical ideal answer** generate karana aur us answer ko embed karna.
```
Question: "What happens if my package is lost?"
          ↓ LLM generates hypothetical answer:
HyDE Doc: "If a package is lost, the company will issue a full refund or send a 
           replacement via expedited shipping within 24 hours of the report."
          ↓ Embed THIS instead of the question
```
**Why Better:** Answer ka embedding space question ke embedding space se zyada documents se match karta hai.
**Hamare Project Mein:** Tier 3 mein use karenge.

---

## Concept 6: Similarity Search (Finding Relevant Chunks)

### 6a. Cosine Similarity (Naive)
**General:** Do vectors ke beech ka angle measure karta hai. 0 = bilkul same, 1 = bilkul alag.
**Use:** Top-K similar vectors nikalo (e.g., Top 3 most similar chunks).
**Hamare Project Mein:** Tier 1 ka default retrieval method.

### 6b. MMR (Maximal Marginal Relevance) (Intermediate)
**General:** Sirf similarity nahi, **diversity** bhi consider karta hai. Agar pehle 2 chunks same topic ke hain, teesra chunk kuch aur topic ka lata hai.
**Why:** Koi important policy miss na ho jaye.
**Hamare Project Mein:** Tier 2 mein try karenge.

### 6c. Hybrid Search (Dense + Sparse) (Advanced)
**General:** 2 alag retrieval methods combine karta hai:
* **Dense (Semantic):** Embedding-based, meaning samajhta hai.
* **Sparse (BM25/Keyword):** Old-school keyword matching, exact words dhoondhta hai.

Dono ke results ko **Reciprocal Rank Fusion (RRF)** se merge karta hai.

```
Dense: Finds "damaged item return" even if user said "broken product refund"
Sparse: Finds exact "ORD-798923" or "FedEx" if user mentions them
Hybrid: Best of both worlds!
```
**Hamare Project Mein:** Tier 3 mein zaroor use karenge kyunki customer order IDs aur tracking numbers mention karte hain (exact keyword match needed).

---

## Concept 7: Re-Ranking

**General:**
Initial retrieval (Top-K se 10 chunks nikale) fast lekin imprecise hoti hai. Re-ranking mein hum un 10 chunks ko ek **Cross-Encoder** model mein daalte hain jo har chunk ko question ke against individually score karta hai aur best wale upar aate hain.

```
Initial Retrieval → Top 10 chunks (fast, approximate)
        ↓
Cross-Encoder Re-Ranker → Scores each of 10 chunks properly
        ↓
Final Top 3 (slow but very accurate)
```

**Model:** `cross-encoder/ms-marco-MiniLM-L-6-v2` (free, HuggingFace)
**Hamare Project Mein:** Tier 2 mein add karenge.

---

## Concept 8: Context Window Management

**General:**
Retrieved chunks LLM ko dene se pehle yeh ensure karna ke total tokens limit se zyada na hon. Agar 10 chunks aaye aur sab bohat lambe hain, toh LLM crash ya truncate kar dega.

**Techniques:**
* Sirf Top-3 chunks lo.
* Chunks ko summarize karo.
* `max_tokens` set karo.

**Hamare Project Mein:** Hum sirf Top-3 relevant chunks LLM ko denge.

---

## Concept 9: RAG Fusion (Advanced)

**General:**
Query Expansion + Hybrid Search + Re-Ranking = RAG Fusion.
1. Original query ko 4 versions mein expand karo.
2. Har version se alag alag retrieve karo.
3. Sab results ko RRF (Reciprocal Rank Fusion) se merge karo.
4. Final best chunks LLM ko doh.

**Why It's Powerful:** Multiple perspectives se retrieved chunks mein bahut kam chance hai ke koi important information miss ho.
**Hamare Project Mein:** Tier 3 ka final form.

---

# EVALUATION CONCEPTS

---

## Concept 10: RAG Evaluation Metrics

Sirf "ache results aaye" kehna kaafi nahi — hum numbers mein measure karenge.

### 10a. Retrieval Metrics (Retrieval kitna achha hai?)
* **Hit Rate:** Kya relevant chunk Top-K mein aya? (1 ya 0 per query)
* **MRR (Mean Reciprocal Rank):** Relevant chunk kaunse number par aya? Top-1 = perfect (1.0), Top-3 = 0.33.

### 10b. Generation Metrics (RAGAS Framework)
* **Faithfulness:** Kya LLM ka answer sirf retrieved context se hai ya usne kuch hallucinate kiya?
* **Answer Relevancy:** Kya answer user ke sawal se relevant hai?
* **Context Precision:** Retrieved chunks mein se kitne actually useful thay?
* **Context Recall:** Kya sab zaroori information retrieve ho gayi ya kuch miss hua?

**Hamare Project Mein:** Phase 6 (Evaluation Framework) mein RAGAS use karenge. Lekin Phase 2 mein bhi manual aur basic automated evaluation karenge.

---

## Summary Table: Kya Kab Use Karein

| Scenario | Recommended Technique |
|---|---|
| Starting out / Prototype | Fixed Chunking + MiniLM + ChromaDB + Cosine |
| Need better chunk quality | Semantic Chunking |
| Need better ranking | Add Cross-Encoder Re-Ranker |
| User queries are vague | Add HyDE or Query Expansion |
| User mentions exact keywords/IDs | Add Hybrid Search (BM25 + Dense) |
| Production system | RAG Fusion + RAGAS Evaluation |
