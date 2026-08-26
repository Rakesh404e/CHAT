class ShortTermMemory:
    def __init__(self):
        self.messages: list[dict] = []
        self.summary = None

    def load(self, messages, summary=None):
        self.messages = messages.copy()
        self.summary = summary

    def add_message(self, role: str, message: str):
        self.messages.append({
            "role": role,
            "content": message
        })

    def get_messages(self):
        formatted_messages = []
        if self.summary:
            formatted_messages.append({
                "role": "system",
                "content": f"Summary of previous conversation:\n{self.summary}"
            })
        formatted_messages.extend(self.messages[-10:])
        return formatted_messages

    def get_summary(self):
        return self.summary

    def remove_old_messages(self, count):
        self.messages = self.messages[count:]

    def set_summary(self, summary):
        self.summary = summary

    def clear(self):
        self.messages = []
        self.summary = None

