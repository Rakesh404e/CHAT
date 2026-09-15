class Summarizer:

    def __init__(self, model):
        self.model = model

    def summarize(self, old_summary, messages):

        prompt = f"""
            You are maintaining a conversation summary.

            Existing summary:
            {old_summary or "No previous summary."}

            New conversation messages:
            {messages}

            Create a concise summary that preserves:
            - important facts
            - user preferences
            - goals
            - decisions
            - important technical context
            - unresolved questions

            Do not include irrelevant details.
            Do not invent information.
            """

        response = self.model.generate([
            {
                "role": "system",
                "content": "You are a conversational AI summarizer that produces clear, structured summaries of user interactions."
            },
            {
                "role": "user",
                "content": prompt
            }
        ])

        return response