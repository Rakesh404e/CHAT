class ContextManager:

    def build_context(
        self,
        summary,
        recent_messages,
        current_message,
        long_term_memories=None
    ):
        context = []
        system_parts = []

        if summary:
            system_parts.append(f"Conversation summary:\n{summary}")

        if long_term_memories:
            formatted_memories = "\n".join(
                [f"- {m['content'] if isinstance(m, dict) and 'content' in m else str(m)}" for m in long_term_memories]
            )
            system_parts.append(f"Relevant User Long-Term Memory & Preferences:\n{formatted_memories}")

        if system_parts:
            context.append({
                "role": "system",
                "content": "\n\n".join(system_parts)
            })

        context.extend(recent_messages)

        context.append({
            "role": "user",
            "content": current_message
        })

        return context