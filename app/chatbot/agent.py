from models.base import LLM
from memory.short_term import ShortTermMemory


class ChatAgent:

    def __init__(self, model: LLM , memory:ShortTermMemory, chat_store, conversation_id):
        self.model = model
        self.memory = memory
        self.chat_store = chat_store
        self.conversation_id = conversation_id

    def load_context(self):
        messages = self.chat_store.get_recent_messages(
            self.conversation_id,
            limit=20
        )

        summary = self.chat_store.get_summary(
            self.conversation_id
        )

        self.memory.load(messages,summary)

    def chat(self, message):

        # 1. Save user message
        self.chat_store.save_message(
            self.conversation_id,
            "user",
            message
        )

        # 2. Add to active memory
        self.memory.add_message(
            "user",
            message
        )

        # 3. Send context to LLM
        response = self.model.generate(
            self.memory.get_messages()
        )

        # 4. Save assistant response
        self.chat_store.save_message(
            self.conversation_id,
            "assistant",
            response
        )

        # 5. Add only after successful DB save
        self.memory.add_message(
            "assistant",
            response
        )

        return response