import os
import sys
from langchain.text_splitter import CharacterTextSplitter

from config import CHUNK_OVERLAP, CHUNK_SIZE

def read_txt_files(path):
    file_path  = path 
    with open(file_path, 'r') as output_file:
        content = output_file.read()
    return content


def split_txt_file(raw_text, separator = "\n#"):
    text_splitter = CharacterTextSplitter(
            separator=separator,
            chunk_size= CHUNK_SIZE,
            chunk_overlap= CHUNK_OVERLAP,
            length_function=len
            
        )
    chunks = text_splitter.split_text(raw_text)
    return chunks


def convert_messages_in_txt(conversation_messages):
    conversation_txt = ""
    for message in conversation_messages:
        if message.__class__.__name__ == "AIMessage":
            conversation_txt += 'Terapeutic assistant: ' + message.content + '\n'
        elif message.__class__.__name__ == "HumanMessage":
            conversation_txt += 'Patient: ' + message.content + '\n'
    return conversation_txt

def save_as_txt(path, content):
    file_path  = path 
    if not os.path.exists(os.path.dirname(file_path)):
        #Create the directory
        os.makedirs(os.path.dirname(file_path))
    with open(file_path, 'w') as output_file:
        output_file.write(content)
