class ContextManager:

    def build_context(
        self,
        summary,
        recent_messages,
        current_message
    ):

        context = []

        if summary:
            context.append({
                "role": "system",
                "content": f"Conversation summary:\n{summary}"
            })

        context.extend(recent_messages)

        context.append({
            "role": "user",
            "content": current_message
        })

        return context