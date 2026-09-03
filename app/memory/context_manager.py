import math


def estimate_tokens(text: str) -> int:
    """
    Estimates token count using standard word/character heuristics (~4 characters per token).
    """
    if not text:
        return 0
    return max(1, math.ceil(len(text) / 4.0))


class ContextManager:
    """
    Context Engineering engine for dynamic prompt composition, memory categorization,
    token budgeting, dynamic pruning, and context usage analytics.
    """

    def __init__(
        self,
        system_instructions: str | None = None,
        max_total_tokens: int = 4096,
        max_memory_tokens: int = 1024,
        max_history_tokens: int = 2048
    ):
        self.system_instructions = system_instructions or (
            "You are a helpful, intelligent AI Assistant with access to user long-term memories."
        )
        self.max_total_tokens = max_total_tokens
        self.max_memory_tokens = max_memory_tokens
        self.max_history_tokens = max_history_tokens
        self.last_stats = {}

    def format_categorized_memories(self, memories: list) -> str:
        """
        Categorizes retrieved memories into distinct sections (Preferences, Goals, Facts, Plans, Decisions)
        to prevent 'Lost in the Middle' phenomena and improve LLM contextual attention.
        """
        if not memories:
            return ""

        categories = {
            "preference": [],
            "goal": [],
            "fact": [],
            "plan": [],
            "decision": [],
            "other": []
        }

        for item in memories:
            content = item.get("content") if isinstance(item, dict) and "content" in item else str(item)
            meta = item.get("metadata", {}) if isinstance(item, dict) else {}
            m_type = str(meta.get("memory_type", "")).lower()

            if m_type in categories:
                categories[m_type].append(content)
            else:
                categories["other"].append(content)

        formatted_sections = []
        labels = {
            "preference": "User Preferences",
            "goal": "User Goals",
            "fact": "User Facts & Context",
            "plan": "User Plans",
            "decision": "User Decisions",
            "other": "Other Relevant Memories"
        }

        for cat_key, label in labels.items():
            items = categories[cat_key]
            if items:
                lines = [f"  - {line}" for line in items]
                formatted_sections.append(f"### {label}:\n" + "\n".join(lines))

        return "\n\n".join(formatted_sections)

    def build_context(
        self,
        summary: str | None,
        recent_messages: list[dict],
        current_message: str,
        long_term_memories: list | None = None
    ) -> list[dict]:
        """
        Assembles, token-budgets, and dynamically prunes prompt context.
        """
        system_parts = [self.system_instructions]

        if summary:
            system_parts.append(f"## Conversation Summary:\n{summary}")

        if long_term_memories:
            formatted_memories = self.format_categorized_memories(long_term_memories)
            if formatted_memories:
                # Truncate memories if they exceed memory token budget
                mem_tokens = estimate_tokens(formatted_memories)
                if mem_tokens > self.max_memory_tokens:
                    char_limit = self.max_memory_tokens * 4
                    formatted_memories = formatted_memories[:char_limit] + "\n  - [Truncated for context length]"
                system_parts.append(f"## Relevant Long-Term Memory & User Profile:\n{formatted_memories}")

        system_prompt_content = "\n\n".join(system_parts)
        system_tokens = estimate_tokens(system_prompt_content)
        current_user_tokens = estimate_tokens(current_message)

        # Remaining budget for chat history buffer
        remaining_budget = min(
            self.max_history_tokens,
            self.max_total_tokens - system_tokens - current_user_tokens - 10
        )
        remaining_budget = max(0, remaining_budget)

        # Dynamic Pruning: keep most recent history turns fitting within remaining_budget
        pruned_history = []
        accumulated_history_tokens = 0
        pruned_count = 0

        # Traverse recent messages backwards (newest to oldest)
        for msg in reversed(recent_messages or []):
            msg_tokens = estimate_tokens(msg.get("content", "")) + 4
            if accumulated_history_tokens + msg_tokens <= remaining_budget:
                pruned_history.append(msg)
                accumulated_history_tokens += msg_tokens
            else:
                pruned_count += 1

        pruned_history.reverse()

        # Build final context list
        context = [{"role": "system", "content": system_prompt_content}]
        context.extend(pruned_history)
        context.append({"role": "user", "content": current_message})

        total_tokens = system_tokens + accumulated_history_tokens + current_user_tokens
        self.last_stats = {
            "system_tokens": system_tokens,
            "memory_count": len(long_term_memories or []),
            "history_tokens": accumulated_history_tokens,
            "history_messages_included": len(pruned_history),
            "history_messages_pruned": pruned_count,
            "current_user_tokens": current_user_tokens,
            "total_estimated_tokens": total_tokens,
            "max_total_tokens": self.max_total_tokens
        }

        return context

    def get_last_context_stats(self) -> dict:
        return self.last_stats
