from users import *
from langchain.text_splitter import CharacterTextSplitter
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.chat_models import ChatOpenAI
from langchain.vectorstores import FAISS
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationalRetrievalChain
from langchain.llms import OpenAI

OPENAI_API_KEY = "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"
import os

os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY
def user_init():
    path = os.getcwd()
    user_path = path + "/" + "documents" + "/" + "users"
    
    user_manager = UserManager(path = user_path)
    user_manager.identify_user()
    
    if user_manager.check_user_folder():
        print("La carpeta del usuario ya existe.")
    else:
        folder_name = user_manager.create_user_folder()
        print(f"Se ha creado la carpeta del usuario con el nombre: {folder_name}")


def read_conversations_texts():
    folder = os.getcwd() + "/" + "documents" + "/" + "conversations_examples" # Replace this list with the paths of the folders you want to read
    file_path  =folder + "/" + 'conversations.txt'  # Name of the output file
    with open(file_path, 'r') as output_file:
        content = output_file.read()
    return content
    
def get_chunk_text(raw_text, separator = "\n#"):
    text_splitter = CharacterTextSplitter(
        separator=separator,
        chunk_size= 1000,
        chunk_overlap= 200,
        length_function=len
        
    )
    chunks = text_splitter.split_text(raw_text)
    return chunks    
    
def get_vector_store(chunk_text):
    embeddings = OpenAIEmbeddings()
    vector_store = FAISS.from_texts(texts = chunk_text, embedding = embeddings)
    return vector_store
    
def get_conversation_chain(vector_store):
    llm =  ChatOpenAI(model_name="gpt-3.5-turbo")
    memory = ConversationBufferMemory(memory_key = "chat_history", return_messages = True)
    conversation_chain = ConversationalRetrievalChain.from_llm(llm = llm, retriever = vector_store.as_retriever(),
                                                               memory = memory)
    return conversation_chain
    
def handle_user_input(user_question, conversation_chain):
    response = conversation_chain({'question': user_question})
    chat_history = response['chat_history']
    for i, message in enumerate(chat_history):
        if i%2 == 0:
            pass
        else:
            print(message)
    
if __name__ == "__main__":
    
    user_init()
    print("File reading and writing completed.")
    content = read_conversations_texts()
    print("Conversations texts readed.")
    print(content)
    chunks = get_chunk_text(content)
    print("Text splitted.")
    print(chunks)
    # Created and pass the chunked text to the vector store
    vector_store = get_vector_store(chunks)
    
    # created conversation chain
    conversation = get_conversation_chain(vector_store)
    
    # 
    user_question = input("Pregunta:")
    handle_user_input(user_question, conversation)
    
    a=20