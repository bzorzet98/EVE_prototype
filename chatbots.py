import chromadb
from chromadb.config import Settings
import openai
import yaml
from time import time, sleep
import datetime

from uuid import uuid4

import os

from config import CONVERSATION_EXAMPLES_PATH , OPENAI_API_KEY , PROMPTS_PATH, DICT_STATES, PREDEFINED_MESSAGES

# Import prompts path 
from config import *

# Import the vector store
from langchain.vectorstores import Chroma
# Import the embedding
from langchain.embeddings.openai import OpenAIEmbeddings 

from langchain.chat_models import ChatOpenAI

from langchain.memory import ConversationBufferMemory, ConversationSummaryMemory

from langchain.chains import ConversationChain

from langchain import PromptTemplate

from langchain.vectorstores.chroma import Chroma
from langchain.docstore.document import Document

from langchain.text_splitter import CharacterTextSplitter

# Import user manager from users.py
from users import UserManager
from functions_auxiliary import *


class Chatbot():
    def __init__(self,):
        # User manager
        self.user_manager = UserManager()
        self.username = None
        os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY
        
        self.state = 0
        self.last_session_number = None
        self.last_session_date = None

        self.current_session_number = None
        self.current_session_date = None

        # Initialize the embedding
        self.embedding = OpenAIEmbeddings()
        # Initialize chromadb 
        self.vectorstore_conversation = Chroma(embedding_function=self.embedding)
        # Initialize other vectorstore
        
        
        # Initialize the model
        self.model =  ChatOpenAI(model_name="gpt-3.5-turbo", temperature = 0.7)
        
        # Initialize the memory
        self.memory = None
        
        # Initialize the conversation chain
        self.conversation = None
        
        # Initialize the chatbot
        self.initialize_chatbot()
        
        # 
        pass

    
    def initialize_chatbot(self,):
        # Initialize the config_user_init
        self.__config_user_init()
        
        # Message of welcome
        self.message_of_welcome()

        # Update the state
        self.__update_state()
        
        # Load the data to vector database
        #self.__load_data_to_vector_database()
        
        # Load the masters prompt
        self.__load_prompts()
        
        # Configurate conversation chatbot
        self.__config_conversation_chatbot()
        pass

    def __config_conversation_chatbot(self,):
        if self.state == 0:
            self.memory = ConversationSummaryMemory(llm=self.model , prompt= self.first_session_summary_prompt)
            self.conversation = ConversationChain(llm=self.model, memory=self.memory, 
                                                  verbose=False, prompt=self.first_session_prompt)
            
    def __load_prompts(self,):
        # Load first session prompts
        first_session_text = read_txt_files(FIRST_SESSION_PROMPT_PATH)
        self.first_session_prompt = PromptTemplate(input_variables=['history', 'input'], output_parser=None, partial_variables={}, 
                               template=first_session_text, template_format='f-string', validate_template=True)
        
        # Load first session summary prompt
        first_session_summary_text = read_txt_files(FIRST_SESSION_SUMMARY_PROMPT_PATH)
        self.first_session_summary_prompt = PromptTemplate(input_variables=['summary', 'new_lines'], output_parser=None, partial_variables={}, 
                                                      template=first_session_summary_text, template_format='f-string', validate_template=True)

        # Load summary of last sessions
        last_session_summary_text = read_txt_files(SESSION_FINISHED_SUMMARY_PROMPT_PATH)
        self.last_session_summary_prompt = PromptTemplate(input_variables=["complete_conversation"],output_parser=None, 
                                                          partial_variables={},
                                                          template=last_session_summary_text, 
                                                          template_format='f-string', 
                                                          validate_template=True)
        # Load prompts to update the user profile
        personal_information_prompt_txt = read_txt_files(PERSONAL_INFORMATION_PROMPT_PATH)
        self.personal_information_prompt = PromptTemplate(input_variables=["previous_personal_information", "complete_conversation"],
                                                          output_parser=None, 
                                                          partial_variables={},
                                                          template=personal_information_prompt_txt, 
                                                          template_format='f-string', 
                                                          validate_template=True)
        # Load other prompts
        pass

    def chat(self, input_text):
        output = self.conversation.run(input_text)
        print(f"EVE: {output}")
        pass
        
    def finalize_chatbot(self,):
        self.user_manager.modify_last_sessions_number(self.current_session_number, self.current_session_date)
        
        # Generate a summary of the conversation
        complete_conversation = convert_messages_in_txt(self.conversation.memory.chat_memory.messages)
        session_summary = self.last_session_summary_prompt.format(complete_conversation = complete_conversation)
        summary_session = self.model.predict(session_summary)
        self.user_manager.save_summary_session(summary_session, self.current_session_number, self.current_session_date)
        
        # Save entery conversation
        self.user_manager.save_entery_conversation(complete_conversation, self.current_session_number, self.current_session_date)
        
        # Generate the new personal information
        personal_information_txt = self.personal_information_prompt.format(previous_personal_information = self.personal_information, complete_conversation = complete_conversation)
        self.personal_information = self.model.predict(personal_information_txt)
        self.user_manager.modify_personal_information(self.personal_information.replace('$$$',''))
        
        pass

    def __config_user_init(self,):
        # Configure User Manager
        self.user_manager.identify_user()
        self.username = self.user_manager.username
        # Identify the number of sessions and the date of the last session
        self.last_session_number, self.last_session_date = self.user_manager.identify_last_sessions_number()
        # Actualize the number of the current session and the date of the current session
        self.__actualize_session_number()
        self.user_manager.modify_last_sessions_number(self.current_session_number, self.current_session_date)
        # Load personal information
        self.user_manager.load_personal_information()
        self.personal_information = self.user_manager.give_personal_information()
        return None

    def __actualize_session_number(self,):
        if self.last_session_number is None:
            self.current_session_number = 0
        else:
            self.current_session_number = self.last_session_number + 1
        self.current_session_date = datetime.datetime.now().strftime("%H:%M-%Y/%m/%d")
        return None
        
    def __update_state(self,):
        # Identify the state
        if self.last_session_number == None:
            self.state = 0 # First session
        else:
            self.state = 1 # Not first session
        
    def __load_data_to_vector_database(self,):
        # Load conversations to vector database
        conversation_examples = read_txt_files(CONVERSATION_EXAMPLES_PATH)
        # Split the conversation examples
        conversation_examples = split_txt_file(conversation_examples)
        # Label conversataion examples
        labels = ['conversation_examples']*(len(conversation_examples))
        metadata = [{"labels": l} for l in labels]

        # Create the documents
        documents_conversation = [Document(page_content=f, metadata=m) 
            for f, m in zip(conversation_examples, metadata)]
        
        # Load the data to vector database
        self.vectorstore.add_documents(documents_conversation, metadata = metadata)
    
        # Load history of chat sessions

        # Load summary of chat sessions
        
        # Load summary of last sessions
        
        # Load user profile
        
        # Not implemented yet
        pass
    
    def message_of_welcome(self,):
        if self.state == 0:
            # Read the message of welcome from the file
            with open(PREDEFINED_MESSAGES + "/welcome_message_new_user.txt", 'r') as file:
                # Replace <<<USERNAME>>> in txt for self.username
                message = file.read().replace("<<<USERNAME>>>", self.username)
                # Print the message
                print("EVE: " + message)
        else: 
            # Read the message of welcome from the file
            with open(PREDEFINED_MESSAGES + "/welcome_message_old_user.txt", 'r') as file:
                # Replace <<<USERNAME>>>,<<<SESSION>>> and <<<LAST_SESSION_DATE>>> in txt for self.username, self.last_session_number and self.last_session_date
                last_session_date = self.last_session_date[6:]
                message = file.read().replace("<<<USERNAME>>>", self.username).replace("<<<SESSION>>>", str(self.last_session_number)).replace("<<<LAST_SESSION_DATE>>>", last_session_date)
                # Add EVE: to the beginning of the message and print the message
                print("EVE: " + message)



        









class EVE_chat  :
    
    def __init__(self,prompt_to_default_system_file = 'system_default.txt', 
                 user_profile_file = 'user_profile.txt',
                 prompt_to_instantiate_new_kb_file = 'system_instantiate_new_kb.txt',
                 prompt_to_system_update_existing_kb_file = 'system_update_existing_kb.txt',
                 prompt_to_system_split_kb_file = 'system_split_kb.txt',
                 prompt_to_system_update_user_profile_file ='system_update_user_profile.txt',
                 openai_api_key_file = 'key_openai.txt', 
                 chromab_directory = "chromadb", 
                 n_messages_to_update = 5 ):
        
        self.persist_directory = chromab_directory
        self.chroma_client = chromadb.PersistentClient(path=self.persist_directory)
        self.collection = self.chroma_client.get_or_create_collection(name="knowledge_base")
        self.n_messages_to_update = n_messages_to_update
        self.openai_api_key = self.open_file(openai_api_key_file)
        
        # User profile file
        self.user_profile_file = user_profile_file
        self.prompt_to_default_system_file = prompt_to_default_system_file
        # Files prompts 
        self.prompt_to_instantiate_new_kb_file = prompt_to_instantiate_new_kb_file
        self.prompt_to_system_update_existing_kb_file = prompt_to_system_update_existing_kb_file
        self.prompt_to_system_split_kb_file = prompt_to_system_split_kb_file
        self.prompt_to_system_update_user_profile_file = prompt_to_system_update_user_profile_file

    def save_yaml(self, filepath, data):
        with open(filepath, 'w', encoding='utf-8') as file:
            yaml.dump(data, file, allow_unicode=True)

    def save_file(self, filepath, content):
        with open(filepath, 'w', encoding='utf-8') as outfile:
            outfile.write(content)

    def open_file(self, filepath):
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as infile:
            return infile.read()

    def chatbot(self, messages, model="gpt-4", temperature=0):
        max_retry = 7
        max_tokens = 7000
        retry = 0
        while True:
            try:
                openai.api_key = self.openai_api_key
                response = openai.ChatCompletion.create(model=model, messages=messages, temperature=temperature)
                text = response['choices'][0]['message']['content']

                debug_object = [i['content'] for i in messages]
                debug_object.append(text)
                self.save_yaml('api_logs/convo_%s.yaml' % time(), debug_object)
                if response['usage']['total_tokens'] >= max_tokens:
                    a = messages.pop(1)

                return text
            except Exception as oops:
                print(f'\n\nError communicating with OpenAI: "{oops}"')
                if 'maximum context length' in str(oops):
                    a = messages.pop(1)
                    print('\n\n DEBUG: Trimming oldest message')
                    continue
                retry += 1
                if retry >= max_retry:
                    print(f"\n\nExiting due to excessive errors in API: {oops}")
                    exit(1)
                print(f'\n\nRetrying in {2 ** (retry - 1) * 5} seconds...')
                sleep(2 ** (retry - 1) * 5)

    def update_data_profile(self, user_messages, current_profile):
        prompt_to_system_update_user_profile = self.open_file(self.prompt_to_system_update_user_profile_file)
        print('\n\nUpdating user profile...')
        # if len(user_messages) > 3:
        #     user_messages.pop(0)
        user_scratchpad = '\n'.join(user_messages).strip()
        profile_length = len(current_profile.split(' '))
        profile_conversation = [{'role': 'system', 'content': prompt_to_system_update_user_profile.replace('<<UPD>>', current_profile).replace('<<WORDS>>', str(profile_length))},
                                {'role': 'user', 'content': user_scratchpad}]
        profile = self.chatbot(profile_conversation)
        self.save_file(self.user_profile_file , profile)
        
    def update_kd(self, all_messages):
        # if len(all_messages) > 5:
        #     all_messages.pop(0)
        prompt_to_instantiate_new_kb = self.open_file(self.prompt_to_instantiate_new_kb_file)
        prompt_to_system_update_existing_kb = self.open_file(self.prompt_to_system_update_existing_kb_file)
        prompt_to_system_split_kb = self.open_file(self.prompt_to_system_split_kb_file)
        
        main_scratchpad = '\n\n'.join(all_messages).strip()
        print('\n\nUpdating KB...')
        if self.collection.count() == 0:
            kb_convo = [{'role': 'system', 'content': prompt_to_instantiate_new_kb},
                        {'role': 'user', 'content': main_scratchpad}]
            article = self.chatbot(kb_convo)
            new_id = str(uuid4())
            self.collection.add(documents=[article], ids=[new_id])
        else:
            results = self.collection.query(query_texts=[main_scratchpad], n_results=1)
            kb = results['documents'][0][0]
            kb_id = results['ids'][0][0]

            kb_convo = [{'role': 'system', 'content': prompt_to_system_update_existing_kb.replace('<<KB>>', kb)},
                        {'role': 'user', 'content': main_scratchpad}]
            article = self.chatbot(kb_convo)
            self.collection.update(ids=[kb_id], documents=[article])
            #self.save_file('db_logs/log_%s_update.txt' % time(), 'Updated document %s:\n%s' % (kb_id, article))

            kb_len = len(article.split(' '))
            if kb_len > 1000:
                kb_convo = [{'role': 'system', 'content': self.open_file('system_split_kb.txt')},
                            {'role': 'user', 'content': article}]
                articles = self.chatbot(kb_convo).split('ARTICLE 2:')
                a1 = articles[0].replace('ARTICLE 1:', '').strip()
                a2 = articles[1].strip()
                self.collection.update(ids=[kb_id], documents=[a1])
                new_id = str(uuid4())
                self.collection.add(documents=[a2], ids=[new_id])
                
    def start_chat(self):
        current_profile = self.open_file(self.user_profile_file)
        prompt_to_default_system = self.open_file(self.prompt_to_default_system_file)
        
        conversation = [{'role': 'system', 'content': prompt_to_default_system}]
        user_messages = []
        all_messages = []

        finish_session = False
        
        while finish_session == False:
            text = input('\n\nUSER: ')
            
            if text.lower() == "exit":
                finish_session = True
            
            user_messages.append(text)
            all_messages.append('USER: %s' % text)
            conversation.append({'role': 'user', 'content': text})
            
            self.save_file('chat_logs/chat_%s_user.txt' % time(), text)

            if len(all_messages) > self.n_messages_to_update:
                all_messages.pop(0)
            main_scratchpad = '\n\n'.join(all_messages).strip()

            kb = 'No KB articles yet'
            if self.collection.count() > 0:
                results = self.collection.query(query_texts=[main_scratchpad], n_results=1)
                kb = results['documents'][0][0]

            #That part we can to do differently
            default_system_prompt = prompt_to_default_system.replace('<<PROFILE>>', current_profile).replace('<<KB>>', kb)
            conversation[0]['content'] = default_system_prompt

            response = self.chatbot(conversation)

            self.save_file('chat_logs/chat_%s_chatbot.txt' % time(), response)
            conversation.append({'role': 'assistant', 'content': response})
            all_messages.append('EVE: %s' % response)
            print('\n\nEVE: %s' % response)            
            
            # If all_messages have more than 7000 tokens, update the knowledge database
            total_tokens = sum(len(message.split()) for message in all_messages)
            if total_tokens >= 7000:
                self.update_kd(all_messages)

            # If finish session, we have to update the current profile, the knoledge database, obtain the tags, etc,etc 
            if finish_session:
                print('Finish session')
                # Here we need to implement other method that update the profile
                self.update_data_profile(user_messages = user_messages, current_profile = current_profile)
                

