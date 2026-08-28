from abc import ABC, abstractmethod


class VectorStore(ABC):

    @abstractmethod
    def add(self, id, vector, metadata, document):
        pass

    @abstractmethod
    def search(self, vector, user_id, top_k=5):
        pass

    @abstractmethod
    def update(self, id, vector, metadata, document):
        pass

    @abstractmethod
    def delete(self, id):
        pass