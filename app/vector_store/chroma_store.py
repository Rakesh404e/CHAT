import chromadb
from .base import VectorStore


class ChromaVectorStore(VectorStore):

    def __init__(self, path="./chroma_db", collection_name="long_term_memory"):
        self.client = chromadb.PersistentClient(path=path)
        self.collection = self.client.get_or_create_collection(
            name=collection_name
        )

    def add(self, id: str, vector: list[float], metadata: dict, document: str):
        self.collection.add(
            ids=[str(id)],
            embeddings=[vector],
            metadatas=[metadata],
            documents=[document]
        )

    def update(self, id: str, vector: list[float], metadata: dict, document: str):
        self.collection.upsert(
            ids=[str(id)],
            embeddings=[vector],
            metadatas=[metadata],
            documents=[document]
        )

    def search(self, vector: list[float], user_id: int, top_k: int = 5) -> list[dict]:
        results = self.collection.query(
            query_embeddings=[vector],
            n_results=top_k,
            where={"user_id": int(user_id)}
        )

        memories = []
        if results and results.get("documents") and len(results["documents"]) > 0:
            documents = results["documents"][0]
            metadatas = results["metadatas"][0] if results.get("metadatas") else []
            ids = results["ids"][0] if results.get("ids") else []
            distances = results["distances"][0] if results.get("distances") else []

            for doc, meta, doc_id, dist in zip(documents, metadatas, ids, distances):
                memories.append({
                    "id": doc_id,
                    "document": doc,
                    "metadata": meta,
                    "distance": dist
                })
        return memories

    def delete(self, id: str):
        try:
            self.collection.delete(ids=[str(id)])
        except Exception:
            pass

    def delete_by_user(self, user_id: int):
        try:
            self.collection.delete(where={"user_id": int(user_id)})
        except Exception:
            pass
