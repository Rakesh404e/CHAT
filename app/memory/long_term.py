class LongTermMemory:
    def __init__(self, chat_store, user_id, vector_store=None, embedding_model=None):
        self.chat_store = chat_store
        self.user_id = int(user_id)
        self.vector_store = vector_store
        self.embedding_model = embedding_model

    def add_or_update_memory(self, memory_type: str, key: str, value: str, scope: str | None = None) -> int:
        """
        Saves a memory item or updates an existing one (Memory Reversal/Update),
        keeping SQLite database and ChromaDB vector store strictly in sync.
        """
        doc_text = f"{memory_type.upper()} [{key}]: {value}"
        if scope:
            doc_text += f" (scope: {scope})"

        existing = self.chat_store.find_memory(
            self.user_id,
            memory_type,
            key,
            scope
        )

        metadata = {
            "user_id": self.user_id,
            "memory_type": str(memory_type),
            "key": str(key),
            "scope": str(scope or "")
        }

        if existing:
            memory_id = existing["id"]
            # 1. Update SQLite
            self.chat_store.update_memory(memory_id, value)

            # 2. Update Vector Store
            if self.vector_store and self.embedding_model:
                try:
                    vector = self.embedding_model.embed(doc_text)
                    self.vector_store.update(
                        id=str(memory_id),
                        vector=vector,
                        metadata=metadata,
                        document=doc_text
                    )
                except Exception as e:
                    print(f"[LongTermMemory] Vector store update error: {e}")

            return memory_id
        else:
            # 1. Save to SQLite
            memory_id = self.chat_store.save_memory(
                self.user_id,
                memory_type,
                key,
                value,
                scope
            )

            # 2. Add to Vector Store
            if self.vector_store and self.embedding_model:
                try:
                    vector = self.embedding_model.embed(doc_text)
                    self.vector_store.add(
                        id=str(memory_id),
                        vector=vector,
                        metadata=metadata,
                        document=doc_text
                    )
                except Exception as e:
                    print(f"[LongTermMemory] Vector store add error: {e}")

            return memory_id

    def add_memory(self, memory_type, key, value, scope=None):
        return self.add_or_update_memory(memory_type, key, value, scope)

    def search_memories(self, query: str, top_k: int = 5, min_score: float = 0.0) -> list[dict]:
        """
        Retrieves relevant memories using Hybrid Search (Vector Similarity + SQL Keyword Search)
        combined via Reciprocal Rank Fusion (RRF).
        """
        vector_candidates = {}
        vector_ranks = {}

        # 1. Vector Search
        if self.vector_store and self.embedding_model:
            try:
                query_vector = self.embedding_model.embed(query)
                results = self.vector_store.search(
                    vector=query_vector,
                    user_id=self.user_id,
                    top_k=max(top_k * 2, 10)
                )
                if results:
                    for rank, item in enumerate(results, start=1):
                        mem_id = str(item["id"])
                        dist = item.get("distance", 0.0)
                        vector_candidates[mem_id] = item
                        vector_ranks[mem_id] = rank
            except Exception as e:
                print(f"[LongTermMemory] Vector search error: {e}")

        # 2. Keyword & Metadata Search over SQLite
        all_memories = self.get_memories()
        query_lower = query.lower()
        query_words = set(query_lower.split())

        keyword_scores = []
        for memory in all_memories:
            mem_id = str(memory["id"])
            m_type = str(memory["memory_type"]).lower()
            m_key = str(memory["key"]).lower()
            m_val = str(memory["value"]).lower()
            m_scope = str(memory["scope"] or "").lower()

            text = f"{m_type} {m_key} {m_val} {m_scope}"

            # Score based on word matches and exact key/type matches
            match_score = 0
            for word in query_words:
                if word in m_key:
                    match_score += 3
                elif word in m_type:
                    match_score += 2
                elif word in text:
                    match_score += 1

            if match_score > 0:
                doc_text = f"{memory['memory_type'].upper()} [{memory['key']}]: {memory['value']}"
                if memory.get("scope"):
                    doc_text += f" (scope: {memory['scope']})"
                keyword_scores.append((
                    match_score,
                    mem_id,
                    {
                        "id": mem_id,
                        "document": doc_text,
                        "metadata": {
                            "user_id": self.user_id,
                            "memory_type": memory["memory_type"],
                            "key": memory["key"],
                            "scope": memory["scope"] or ""
                        }
                    }
                ))

        keyword_scores.sort(key=lambda x: x[0], reverse=True)
        keyword_candidates = {}
        keyword_ranks = {}
        for rank, (_, mem_id, item) in enumerate(keyword_scores, start=1):
            keyword_candidates[mem_id] = item
            keyword_ranks[mem_id] = rank

        # 3. Reciprocal Rank Fusion (RRF)
        all_ids = set(vector_ranks.keys()).union(set(keyword_ranks.keys()))
        rrf_results = []

        RRF_K = 60
        for mem_id in all_ids:
            score = 0.0
            if mem_id in vector_ranks:
                score += 1.0 / (RRF_K + vector_ranks[mem_id])
            if mem_id in keyword_ranks:
                score += 1.0 / (RRF_K + keyword_ranks[mem_id])

            if score >= min_score:
                item = vector_candidates.get(mem_id) or keyword_candidates.get(mem_id)
                if item:
                    rrf_results.append({
                        "id": item["id"],
                        "content": item["document"],
                        "metadata": item["metadata"],
                        "score": score
                    })

        # Sort candidates by combined RRF score descending
        rrf_results.sort(key=lambda x: x["score"], reverse=True)
        return rrf_results[:top_k]

    def search(self, query: str) -> list[dict]:
        return self.search_memories(query)

    def get_memories(self) -> list[dict]:
        return self.chat_store.get_memories(self.user_id)

    def delete_memory(self, memory_id: int):
        self.chat_store.delete_memory(memory_id)
        if self.vector_store:
            try:
                self.vector_store.delete(str(memory_id))
            except Exception as e:
                print(f"[LongTermMemory] Vector store delete error: {e}")

    def delete_memory_by_key(self, memory_type: str, key: str, scope: str | None = None) -> int:
        """
        Deletes memory item(s) by type, key, and scope from both SQLite and ChromaDB vector store.
        """
        deleted_ids = self.chat_store.delete_memory_by_key(
            self.user_id,
            memory_type,
            key,
            scope
        )
        if self.vector_store and deleted_ids:
            for mem_id in deleted_ids:
                try:
                    self.vector_store.delete(str(mem_id))
                except Exception as e:
                    print(f"[LongTermMemory] Vector store delete error for ID {mem_id}: {e}")
        return len(deleted_ids)

    def delete_all_memories(self) -> int:
        """
        Deletes all long-term memories for this user from both SQLite and ChromaDB vector store.
        """
        deleted_ids = self.chat_store.delete_all_memories(self.user_id)
        if self.vector_store:
            try:
                self.vector_store.delete_by_user(self.user_id)
            except Exception as e:
                print(f"[LongTermMemory] Vector store delete_by_user error: {e}")
        return len(deleted_ids)
