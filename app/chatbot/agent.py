import time
from models.base import LLM
from memory.short_term import ShortTermMemory
from memory.sumarizer import Summarizer
from memory.context_manager import ContextManager
from observability.logger import logger
from observability.metrics import metrics_collector


class ChatAgent:

    def __init__(
        self,
        model: LLM,
        memory: ShortTermMemory,
        chat_store,
        conversation_id,
        long_term_memory=None,
        extractor=None,
        context_manager=None
    ):
        self.model = model
        self.memory = memory
        self.chat_store = chat_store
        self.conversation_id = conversation_id
        self.long_term_memory = long_term_memory
        self.extractor = extractor
        self.summarizer = Summarizer(model)
        self.context_manager = context_manager or ContextManager()

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

    def chat(self, message: str, trace_id: str = None) -> str:
        trace_id = trace_id or logger.generate_trace_id()
        start_time = time.time()
        logger.info(f"Starting chat turn for conversation {self.conversation_id}", trace_id=trace_id)

        # 1. Save user message to persistent DB
        self.chat_store.save_message(
            self.conversation_id,
            "user",
            message
        )

        # 2. Add to active short-term memory
        self.memory.add_message(
            "user",
            message
        )

        # 3. Retrieve relevant long-term memories if available
        relevant_memories = []
        if self.long_term_memory:
            try:
                relevant_memories = self.long_term_memory.search_memories(message, top_k=5)
            except Exception as e:
                logger.warning(f"Error searching long-term memory: {e}", trace_id=trace_id)

        # 4. Check summarization if message limit reached
        self._check_and_summarize()

        # 5. Build system & message context including long-term memories
        full_context = self.context_manager.build_context(
            summary=self.memory.get_summary(),
            recent_messages=self.memory.messages[:-1],  # Exclude current message since ContextManager appends it
            current_message=message,
            long_term_memories=relevant_memories
        )

        # 6. Send context to LLM
        if hasattr(self.model, "generate") and "trace_id" in self.model.generate.__code__.co_varnames:
            response = self.model.generate(full_context, trace_id=trace_id)
        else:
            response = self.model.generate(full_context)

        # 7. Save assistant response
        self.chat_store.save_message(
            self.conversation_id,
            "assistant",
            response
        )

        # 8. Add assistant response to active memory
        self.memory.add_message(
            "assistant",
            response
        )

        # Check summarization again
        self._check_and_summarize()

        # 9. Extract and store/update/delete long-term memories
        if self.extractor and self.long_term_memory:
            try:
                extracted_memories = self.extractor.extract(message)
                for mem in extracted_memories:
                    action = getattr(mem, "action", "add_or_update")
                    if hasattr(action, "value"):
                        action = action.value

                    m_type = mem.memory_type.value if hasattr(mem.memory_type, "value") else str(mem.memory_type)

                    if action == "delete_all":
                        self.long_term_memory.delete_all_memories()
                    elif action == "delete":
                        self.long_term_memory.delete_memory_by_key(
                            memory_type=m_type,
                            key=mem.key,
                            scope=mem.scope
                        )
                    else:
                        self.long_term_memory.add_or_update_memory(
                            memory_type=m_type,
                            key=mem.key,
                            value=mem.value,
                            scope=mem.scope
                        )
            except Exception as e:
                logger.warning(f"Error extracting/processing memory: {e}", trace_id=trace_id)

        duration_ms = (time.time() - start_time) * 1000
        logger.info(f"Completed chat turn in {duration_ms:.2f}ms", trace_id=trace_id, duration_ms=duration_ms)
        return response

    def get_observability_report(self) -> dict:
        return {
            "conversation_id": self.conversation_id,
            "context_stats": self.context_manager.get_last_context_stats(),
            "metrics": metrics_collector.get_metrics_summary()
        }




