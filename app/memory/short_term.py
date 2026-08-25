from torch.utils.tensorboard import summary
class ShortTermMemory:
    def __init__(self):
        self.messages:list[str]=[]
        self.summary = None

    def load(self,messages):
        self.messages = messages.copy()
        self.summary = summary

    def add_message(self,role:str,message:str):
        self.messages.append({
            "role":role,
            "content": message
        })

    def get_messages(self):
        return self.messages
    
    def get_summary(self):
        return self.summary
    
    def set_summary(self, summary):
        self.summary = summary

    def clear(self):
        self.messages=[]
        self.summary=None
    
