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

from langchain.memory import ConversationBufferMemory, ConversationSummaryMemory, ChatMessageHistory

from langchain.chains import ConversationChain

from langchain import PromptTemplate, LLMChain


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

        # Load prompts
        self.__load_prompts()

        # Initialize the embedding
        self.embedding = OpenAIEmbeddings()
        # Initialize chromadb 
        self.vectorstore_conversation = Chroma(embedding_function=self.embedding)
        
        # Initialize other vectorstore
        
        # Initialize the memory
        self.memory = ChatMessageHistory()
        
        # Initialize the summarizer of current conversation
        # self.summarizer = LLMChain(llm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature = 0.1), 
        #                                 verbose = False,prompt=PromptTemplate.from_template("empty {empty}"))
        
        self.summarizer = ConversationSummaryMemory(llm=ChatOpenAI(model_name="gpt-3.5-turbo", temperature = 0.1),
                                                    ai_prefix='Terapeutic assistant', human_prefix = 'Patient')
        
        #Initialize the summarizer of finish session
        self.summarizer_finish_session = LLMChain(llm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature = 0.1), 
                                        verbose = False,prompt=PromptTemplate.from_template("empty {empty}"))
        
        # Initialize personal information updater
        self.personal_information_updater = LLMChain(llm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature = 0.1), 
                                        verbose = False,prompt=PromptTemplate.from_template("empty {empty}"))
        
        # Initialize the conversation
        self.conversation = LLMChain(llm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature = 0.5),
                                     verbose = False, prompt=PromptTemplate.from_template("empty {empty}"))
        
        
        
        # # Initialize the model
        # self.model =  ChatOpenAI(model_name="gpt-3.5-turbo", temperature = 0.5)
        
        
        # Initialize the chatbot
        self.initialize_chatbot()
        
        self.summary_complete_conversation = None
        # 
        pass

    
    def initialize_chatbot(self,):
        # Initialize the config_user_init
        self.__config_user_init()
        
        # Update the state
        self.__update_state()
        
        # Load the data to vector database
        self.__load_data_to_vector_database()
        
        # Message of welcome
        self.message_of_welcome()

        # Load the masters prompt
        self.__load_prompts()
        
        # Configurate conversation chatbot
        self.__config_conversation_chatbot()
        
        pass
    
    def chat(self, patient_message):
        # Obtain last messages
        last_messages = self.__obtain_n_last_messages_string(n_last_messages=2)
        
        # Add patient message to memory
        self.__add_user_messages_in_memory(patient_message)

        # Predict a new summary
        self.__predict_new_summary()

        # Update current personal information
        self.__update_personal_information(patient_message)
        
        # Obtain similarity search
        similar_conversations = self.__similarity_search(patient_message)
        
        # Predict AI assistant message
        if self.state == 0:
            AI_asistant_message = self.conversation.predict(personal_information=self.personal_information, 
                                                    last_messages =  last_messages, 
                                                    actual_session_summary = self.summarizer.buffer,
                                                    similar_conversation = similar_conversations,
                                                    patient_message = patient_message)
        elif self.state == 1:
            AI_asistant_message = self.conversation.predict(personal_information=self.personal_information, 
                                                    summary_previuos_session= self.summary_previous_session, 
                                                    summary_conversation = self.summarizer.buffer,
                                                    patient_message = patient_message)

        # Add AI assistant message to memory
        self.__add_ai_messages_in_memory(AI_asistant_message)

        # Print AI assistant message
        print(f"Eve :{AI_asistant_message}")
        
    def finalize_chatbot(self,):
        self.user_manager.modify_last_sessions_number(self.current_session_number, self.current_session_date)
        
        # Generate the convertation txt
        complete_conversation = convert_messages_in_txt(self.memory.messages)
        
        # Update personal information finish session
        self.__update_personal_information_finish_session(complete_conversation)
        # Save personal information
        self.user_manager.modify_personal_information(self.personal_information)
        
        # Update summary of the complete conversation
        self.__predict_new_summary_finish_session(complete_conversation)
        # Save summary of the complete conversation
        self.user_manager.save_summary_session(self.summary_complete_conversation, self.current_session_number, 
                                               self.current_session_date)
        
        # Save entery conversation
        self.user_manager.save_entery_conversation(complete_conversation, self.current_session_number, self.current_session_date)
        
        pass

    def __config_conversation_chatbot(self,):
        if self.state == 0:
            # Config conversation prompt
            self.conversation.prompt = self.prompt_first_session_master
            
        elif self.state == 1 :
            # Config conversation prompt
            self.conversation.prompt = self.prompt_sessions_master
        
        # Config summarizer prompt
        self.summarizer.prompt = self.summary_conversation_prompt
        # Config personal information updater prompt
        self.personal_information_updater.prompt = self.update_personal_information_prompt
        # Config summarizer finish session prompt
        self.summarizer_finish_session.prompt = self.summary_conversation_finish_session_prompt
                
    def __load_prompts(self,):
        
        # Load prompts for first session master
        template_first_session_master = read_txt_files(FIRST_SESSION_MASTER_PROMPT_PATH)
        self.prompt_first_session_master = PromptTemplate(input_variables=['personal_information', 'last_messages','actual_session_summary','similar_conversation','patient_message'], 
                                                    output_parser=None, partial_variables={}, template=template_first_session_master, 
                                                    template_format='f-string', validate_template=True)
        # Load prompts for sessions master
        template_sessions_master = read_txt_files(SESSIONS_MASTER_PROMPT_PATH)
        self.prompt_sessions_master = PromptTemplate(input_variables=['personal_information','summary_previuos_session', 
                                                                      'summary_conversation','patient_message'],
                                                     output_parser=None, partial_variables={}, 
                                                     template=template_sessions_master, 
                                                     template_format='f-string', validate_template=True
                                                    )
                                                     
        
        # Load prompts for the summarizer
        template_summary_conversation = read_txt_files(SUMMARY_CONVERSATION_PROMPT_PATH)
        self.summary_conversation_prompt = PromptTemplate(input_variables=['summary', 'new_lines'], output_parser=None, partial_variables={}, 
                                    template=template_summary_conversation, template_format='f-string', validate_template=True)
        
        # Load summary prompt for finish session
        template_summary_conversation_finish_session = read_txt_files(SUMMARY_CONVERSATION_FINISH_SESSION_PROMPT_PATH)
        self.summary_conversation_finish_session_prompt = PromptTemplate(input_variables=['conversation'], output_parser=None, partial_variables={}, 
                                    template=template_summary_conversation_finish_session, template_format='f-string', validate_template=True)
        
        # Load prompts for personal information updater
        update_personal_information_prompt_txt = read_txt_files(UPDATE_PERSONAL_INFORMATION_PROMPT_PATH)
        self.update_personal_information_prompt = PromptTemplate(input_variables=['previous_information', 'new_messages'], 
                                             output_parser=None, partial_variables={}, template=update_personal_information_prompt_txt, 
                                             template_format='f-string', validate_template=True)
        
        #
        
        # Load prompts for personal information updater finish session
        update_personal_information_finish_session_prompt_txt = read_txt_files(UPDATE_PERSONAL_INFORMATION_FINISH_SESSION_PROMPT_PATH)
        self.update_personal_information_finish_session_prompt = PromptTemplate(input_variables=['previous_information', 'conversation'], 
                                                                                output_parser=None, partial_variables={}, 
                                                                                template=update_personal_information_finish_session_prompt_txt, 
                                                                                template_format='f-string', validate_template=True)
        
        # Load other prompts
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
        
        # Load last session summary
        self.user_manager.load_last_session_summary()
        self.summary_previous_session = self.user_manager.load_last_session_summary()
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
        self.vectorstore_conversation.add_documents(documents_conversation, metadata = metadata, verbose = False)
    
        # Load history of chat sessions

        # Load summary of chat sessions
        
        # Load summary of last sessions
        
        # Load user profile
        
        # Not implemented yet
        pass
    
    def __similarity_search(self, query , n_results = 1):
        results = self.vectorstore_conversation.similarity_search(query)[n_results-1]
        results_strings = results.page_content
        return results_strings
        
    def message_of_welcome(self,):
        if self.state == 0:
            # Read the message of welcome from the file
            with open(PREDEFINED_MESSAGES + "/welcome_messages.txt", 'r') as file:
                # Replace <<<USERNAME>>> in txt for self.username
                message = file.read().replace("<<<USERNAME>>>", self.username)
                # Print the message
                print(message)
        else: 
            # Read the message of welcome from the file
            with open(PREDEFINED_MESSAGES + "/welcome_messages.txt", 'r') as file:
                # Replace <<<USERNAME>>>,<<<SESSION>>> and <<<LAST_SESSION_DATE>>> in txt for self.username, self.last_session_number and self.last_session_date
                last_session_date = self.last_session_date[6:]
                message = file.read().replace("<<<USERNAME>>>", self.username).replace("<<<SESSION>>>", str(self.last_session_number)).replace("<<<LAST_SESSION_DATE>>>", last_session_date)
                # Add EVE: to the beginning of the message and print the message
                print(message)

    def __obtain_n_last_messages_string(self, n_last_messages = 2):
        last_messages = self.__obtain_n_last_messages(n_last_messages= n_last_messages)
        last_messages_txt = convert_messages_in_txt(last_messages)
        return last_messages_txt
        
    def __predict_new_summary(self):
        # Generate a summary of the conversation
        if self.summarizer.buffer == '':
            return ''
        else:
            last_messages = self.obtain_n_last_messages()
            last_summary = self.summarizer.buffer()
            self.summarizer.buffer = self.summarizer.predict_new_summary(messages= last_messages, existing_summary=last_summary)

    def __predict_new_summary_finish_session(self,complete_conversation):
        self.summary_complete_conversation = self.summarizer_finish_session.predict(conversation= complete_conversation)
           
    def __obtain_last_summary(self):
        return self.summarizer.buffer()

    def __obtain_n_last_messages(self, n_last_messages = 2):
        # If the number of messages is less than n_last_messages, we obtain all the messages
        if len(self.memory.messages) < n_last_messages:
            messages = self.memory.messages
        else: 
            # Obtain the last n messages
            messages = self.memory.messages[-n_last_messages:]
        return messages
        
    def __add_ai_messages_in_memory(self,message_content):
        self.memory.add_ai_message(message_content)
    
    def __add_user_messages_in_memory(self,message_content):
        self.memory.add_user_message(message_content)

    def __update_personal_information(self,message_content):
        # Replace the personal information 
        self.personal_information = self.personal_information_updater.predict(previous_information=self.personal_information,
                                                                            new_messages= message_content)

    def __update_personal_information_finish_session(self,complete_conversation):
        # Update personal information updater prompt 
        self.personal_information_updater.prompt = self.update_personal_information_finish_session_prompt
        # Replace the personal information 
        self.personal_information = self.personal_information_updater.predict(previous_information=self.personal_information,
                                                                                conversation= complete_conversation)
        
        




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
                

