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

    def search_memories(self, query: str, top_k: int = 5) -> list[dict]:
        """
        Retrieves relevant memories using ChromaDB vector search with fallback to SQL search.
        """
        if self.vector_store and self.embedding_model:
            try:
                query_vector = self.embedding_model.embed(query)
                vector_results = self.vector_store.search(
                    vector=query_vector,
                    user_id=self.user_id,
                    top_k=top_k
                )
                if vector_results:
                    return [
                        {
                            "id": item["id"],
                            "content": item["document"],
                            "metadata": item["metadata"]
                        }
                        for item in vector_results
                    ]
            except Exception as e:
                print(f"[LongTermMemory] Vector search fallback to SQL search: {e}")

        # Fallback to keyword search over SQLite memories
        memories = self.get_memories()
        query_words = query.lower().split()
        relevant = []

        for memory in memories:
            text = f"{memory['memory_type']} {memory['key']} {memory['value']} {memory['scope'] or ''}".lower()
            score = sum(1 for word in query_words if word in text)
            if score > 0:
                relevant.append((score, memory))

        relevant.sort(key=lambda x: x[0], reverse=True)
        return [
            {
                "id": m["id"],
                "content": f"{m['memory_type'].upper()} [{m['key']}]: {m['value']}",
                "metadata": m
            }
            for _, m in relevant[:top_k]
        ]

    def search(self, query: str) -> list[dict]:
        return self.search_memories(query)

    def get_memories(self) -> list[dict]:
        return self.chat_store.get_memories(self.user_id)

    def delete_memory(self, memory_id: int):
        self.chat_store.delete_memory(memory_id)
        if self.vector_store:
            try:
                self.vector_store.delete(str(memory_id))
            except Exception:
                pass