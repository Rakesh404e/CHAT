class LongTermMemory:
    def __init__(self,chat_store,user_id):
        self.chat_store=chat_store
        self.user_id=user_id
    
    def add_memory(self,memory_type,key,value,scope=None):
        existing = self.chat_store.find_memory(
            self.user_id,
            memory_type,
            key,
            scope
        )

        if existing:
            return existing["id"]

        return self.chat_store.save_memory(
            self.user_id,
            memory_type,
            key,
            value,
            scope
        )

    def get_memories(self):
        return self.chat_store.get_memories(
            self.user_id
        )

    def update_memory(self, memory_id, value):
        self.chat_store.update_memory(
            memory_id,
            value
        )

    def search(self, query):

        memories = self.get_memories()

        query_words = query.lower().split()

        relevant = []

        for memory in memories:

            text = (
                f"{memory['key']} "
                f"{memory['value']} "
                f"{memory['scope'] or ''}"
            ).lower()

            score = sum(
                1 for word in query_words
                if word in text
            )

            if score > 0:
                relevant.append(
                    (score, memory)
                )

        relevant.sort(
            key=lambda x: x[0],
            reverse=True
        )

        return [
            memory
            for score, memory in relevant
        ]