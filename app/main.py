from chatbot.agent import ChatAgent
from models.factory import ModelFactory
from config import Config
from memory.database import Database
from memory.chat_store import ChatStore
from memory.short_term import ShortTermMemory


def main():
    config=Config()
    model = ModelFactory.create(config)

    database = Database()
    database.initialize()

    chat_store = ChatStore(database)
    
    user_id = int(input("Enter user ID: "))

    user = chat_store.get_user(user_id)

    if user is None:
        user_id = chat_store.create_user()
        print(f"New user created: {user_id}")

    conversations=chat_store.get_user_conversations(user_id)

    for i, conversation in enumerate(conversations):
        print(f"{i+1}. {conversation['title']}")
    choice = input("Choose conversation (number) or press Enter for new: ")
    if choice.strip():
        conversation_id = conversations[int(choice) - 1]["id"]
    else:
        conversation_id = chat_store.create_conversation(
            user_id,
            "My first chat"
        )

    memory = ShortTermMemory()

    model = ModelFactory.create(config)

    agent = ChatAgent(
        model=model,
        memory=memory,
        chat_store=chat_store,
        conversation_id=conversation_id
    )
    agent.load_context()

    while True:
        user_input=input("You : ")
        if user_input.lower()=='exit':
            break
        response=agent.chat(user_input)
        print(f"Bot : {response}")

if __name__ == "__main__":
    main()
