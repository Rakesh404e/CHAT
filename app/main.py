from chatbot.agent import ChatAgent
from models.factory import ModelFactory
from config import Config
from memory.database import Database
from memory.chat_store import ChatStore
from memory.short_term import ShortTermMemory
from memory.long_term import LongTermMemory
from memory.extractor import MemoryExtractor
from vector_store.chroma_store import ChromaVectorStore
from embeddings.factory import EmbeddingFactory


def main():
    config = Config()
    model = ModelFactory.create(config)

    database = Database()
    database.initialize()

    chat_store = ChatStore(database)
    
    user_input_id = input("Enter user ID (or press Enter for new user): ")
    if user_input_id.strip():
        user_id = int(user_input_id.strip())
        user = chat_store.get_user(user_id)
        if user is None:
            user_id = chat_store.create_user()
            print(f"User not found. Created new user with ID: {user_id}")
    else:
        user_id = chat_store.create_user()
        print(f"New user created with ID: {user_id}")

    # Vector store and embedding model initialization
    vector_store = ChromaVectorStore(path=config.chroma_path)
    embedding_model = EmbeddingFactory.create(config)


    # Unified LongTermMemory Manager
    long_term_memory = LongTermMemory(
        chat_store=chat_store,
        user_id=user_id,
        vector_store=vector_store,
        embedding_model=embedding_model
    )

    # Memory extractor
    extractor = MemoryExtractor(model=model)

    conversations = chat_store.get_user_conversations(user_id)

    for i, conversation in enumerate(conversations):
        print(f"{i+1}. {conversation['title']}")
    choice = input("Choose conversation (number) or press Enter for new: ")
    if choice.strip():
        conversation_id = conversations[int(choice) - 1]["id"]
    else:
        conversation_id = chat_store.create_conversation(
            user_id,
            "My Chat Session"
        )

    memory = ShortTermMemory()

    agent = ChatAgent(
        model=model,
        memory=memory,
        chat_store=chat_store,
        conversation_id=conversation_id,
        long_term_memory=long_term_memory,
        extractor=extractor
    )
    agent.load_context()

    print(f"\n--- Chat session started for User {user_id} (Conversation {conversation_id}) ---")
    print("Type 'exit' to end session.\n")

    while True:
        user_input = input("You : ")
        if user_input.lower() == 'exit':
            break
        response = agent.chat(user_input)
        print(f"Bot : {response}\n")


if __name__ == "__main__":
    main()

