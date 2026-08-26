from models.base import LLM
from memory.short_term import ShortTermMemory
from memory.sumarizer import Summarizer


class ChatAgent:

    def __init__(self, model: LLM, memory: ShortTermMemory, chat_store, conversation_id):
        self.model = model
        self.memory = memory
        self.chat_store = chat_store
        self.conversation_id = conversation_id
        self.summarizer = Summarizer(model)

    def load_context(self):
        messages = self.chat_store.get_recent_messages(
            self.conversation_id,
            limit=10
        )

        summary = self.chat_store.get_summary(
            self.conversation_id
        )

        self.memory.load(messages, summary)

    def _check_and_summarize(self):
        if len(self.memory.messages) > 10:
            overflow_count = len(self.memory.messages) - 10
            older_messages = self.memory.messages[:overflow_count]
            old_summary = self.memory.get_summary()

            new_summary = self.summarizer.summarize(old_summary, older_messages)

            self.chat_store.update_summary(self.conversation_id, new_summary)
            self.memory.set_summary(new_summary)
            self.memory.remove_old_messages(overflow_count)

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

        # Summarize if memory exceeds 10 messages
        self._check_and_summarize()

        # 3. Send context to LLM
        response = self.model.generate(
            self.memory.get_messages()
        )
        # print(self.memory.summary)
        # print(self.memory.messages)

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

        # Check summarization again after assistant response
        self._check_and_summarize()

        return response
