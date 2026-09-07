import time
from typing import Optional
from models.base import LLM
from memory.short_term import ShortTermMemory
from memory.sumarizer import Summarizer
from memory.context_manager import ContextManager
from tasks.manager import task_manager as default_task_manager, TaskType, TaskStatus
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
        context_manager=None,
        task_manager=None,
        async_processing: bool = True
    ):
        self.model = model
        self.memory = memory
        self.chat_store = chat_store
        self.conversation_id = conversation_id
        self.long_term_memory = long_term_memory
        self.extractor = extractor
        self.summarizer = Summarizer(model)
        self.context_manager = context_manager or ContextManager()
        self.task_manager = task_manager or default_task_manager
        self.async_processing = async_processing
        self.last_task_id: Optional[str] = None

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

    def _process_post_turn(self, message: str, trace_id: str):
        """
        Executes post-turn background work: context summarization and
        long-term memory extraction & dual-store persistence.
        """
        # 1. Check summarization
        self._check_and_summarize()

        # 2. Extract and store/update/delete long-term memories
        extracted_count = 0
        if self.extractor and self.long_term_memory:
            try:
                extracted_memories = self.extractor.extract(message)
                extracted_count = len(extracted_memories)
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
                raise e

        return {"memories_extracted": extracted_count}

    def chat(self, message: str, trace_id: str = None, async_processing: Optional[bool] = None) -> str:
        trace_id = trace_id or logger.generate_trace_id()
        start_time = time.time()
        use_async = self.async_processing if async_processing is None else async_processing
        logger.info(
            f"Starting chat turn for conversation {self.conversation_id} (async={use_async})",
            trace_id=trace_id
        )

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

        # 4. Check summarization if message limit reached (prior to generation)
        self._check_and_summarize()

        # 5. Build system & message context including long-term memories
        full_context = self.context_manager.build_context(
            summary=self.memory.get_summary(),
            recent_messages=self.memory.messages[:-1],  # Exclude current message since ContextManager appends it
            current_message=message,
            long_term_memories=relevant_memories
        )

        # 6. Send context to LLM
        gen_fn = getattr(self.model, "generate", None)
        code_obj = getattr(gen_fn, "__code__", None)
        if code_obj and hasattr(code_obj, "co_varnames") and "trace_id" in code_obj.co_varnames:
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

        # 9. Asynchronous or Synchronous post-turn processing
        user_id = getattr(self.long_term_memory, "user_id", None) if self.long_term_memory else None
        meta = {
            "trace_id": trace_id,
            "user_id": user_id,
            "conversation_id": self.conversation_id
        }

        if use_async and self.task_manager:
            self.last_task_id = self.task_manager.submit(
                TaskType.MEMORY_EXTRACTION,
                self._process_post_turn,
                message,
                trace_id,
                metadata=meta
            )
        else:
            self._process_post_turn(message, trace_id)
            self.last_task_id = None

        duration_ms = (time.time() - start_time) * 1000
        logger.info(
            f"Completed chat turn in {duration_ms:.2f}ms (async_task={self.last_task_id})",
            trace_id=trace_id,
            duration_ms=duration_ms
        )
        return response

    def get_last_task_id(self) -> Optional[str]:
        return self.last_task_id

    def wait_for_background_tasks(self, timeout: float = 5.0) -> bool:
        if self.last_task_id and self.task_manager:
            record = self.task_manager.wait_for_task(self.last_task_id, timeout=timeout)
            return record is not None and record.status == TaskStatus.COMPLETED
        return True

    def get_observability_report(self) -> dict:
        return {
            "conversation_id": self.conversation_id,
            "last_task_id": self.last_task_id,
            "context_stats": self.context_manager.get_last_context_stats(),
            "metrics": metrics_collector.get_metrics_summary()
        }
