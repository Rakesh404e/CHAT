# Benchmark Methodology Specification

This document details the technical methodology, hardware/runtime environment, dataset specifications, mathematical equations, and reproducibility guidelines for the AI Agent Chatbot Benchmarking Suite.

---

## 1. Environment & Hardware Runtime

- **Operating System**: Windows 11 (build 26100) / x64
- **Runtime**: Python 3.12.5 (win32)
- **Primary LLM Provider**: Groq API (`groq/compound-mini` / Llama 3 models)
- **Vector DB**: ChromaDB 0.5+ (PersistentClient)
- **Relational DB**: SQLite 3 (WAL journal mode / single file storage)
- **Embedding Model**: Local 1536-dimensional Hashing & Character N-Gram Fallback Embedding (`LocalFallbackEmbedding`)
- **Isolation Guarantee**: All benchmark evaluation runs instantiate isolated temporary SQLite databases (`tempfile.mkdtemp`) and ChromaDB collections, ensuring production state remains completely untouched.

---

## 2. Evaluation Datasets

### A. Long-Term Memory Retrieval Dataset (`golden_retrieval_dataset.json`)
- **Total Memories**: 60 entries (40 for User A [101], 20 for User B [102])
- **Memory Categories**: 5 categories (Preference, Goal, Fact, Plan, Decision)
- **Total Test Queries**: 60 natural language queries mapped to target ground-truth memory keys and substrings.
- **User Isolation Test Cases**: 100% of queries verify strict multi-tenant isolation (ensuring User A queries never return User B records).

### B. Structured Memory Extraction Dataset (`golden_extraction_dataset.json`)
- **Total User Messages**: 60 realistic user inputs
- **Included Commands**: Memory additions/updates, zero-memory conversational inputs (control group), explicit item deletions (`forget location`), and complete memory wipes (`clear all memories`).

---

## 3. Metrics & Mathematical Definitions

### A. Retrieval Metrics
- **Recall@K**: Percentage of test queries where the expected ground-truth memory key/content appears within the top $K$ returned results ($K \in \{1, 3, 5\}$).
  $$\text{Recall@K} = \frac{\sum_{i=1}^{N} \mathbb{I}(\text{rank}_i \le K)}{N} \times 100$$
- **Mean Reciprocal Rank (MRR)**: Average of reciprocal ranks of the first relevant document.
  $$\text{MRR} = \frac{1}{N} \sum_{i=1}^{N} \frac{1}{\text{rank}_i}$$
- **User Isolation Failure Count**: Count of returned items where `metadata.user_id` does not match the querying user.

### B. Memory Extraction Metrics
- **Precision**: $\frac{\text{TP}}{\text{TP} + \text{FP}}$
- **Recall**: $\frac{\text{TP}}{\text{TP} + \text{FN}}$
- **F1-Score**: $2 \times \frac{\text{Precision} \times \text{Recall}}{\text{Precision} + \text{Recall}}$
- **Accuracy**: $\frac{\text{TP} + \text{TN}}{\text{TP} + \text{FP} + \text{FN} + \text{TN}}$

### C. Summarization & Token Compression Metrics
- **Compression Ratio**:
  $$\text{Compression Ratio} = \frac{\text{Post-Summary Tokens}}{\text{Pre-Summary Tokens}}$$
- **Token Reduction Percentage**:
  $$\text{Token Reduction \%} = 100 \times \left(1 - \frac{\text{Post-Summary Tokens}}{\text{Pre-Summary Tokens}}\right)$$

### D. Latency Quantiles
- **P50 / P95 / P99**: 50th, 95th, and 99th percentiles calculated from sorted execution durations across repetitions.

### E. Async Latency Reduction
- **Latency Reduction %**:
  $$\text{Latency Reduction \%} = 100 \times \frac{\text{Sync Latency (P50)} - \text{Async Latency (P50)}}{\text{Sync Latency (P50)}}$$

### F. Caching Speedup
- **Speedup Factor**:
  $$\text{Speedup Factor} = \frac{\text{Uncached Latency (P50)}}{\text{Cached Latency (P50)}}$$
