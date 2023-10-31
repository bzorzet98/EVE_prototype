import chromadb
from chromadb.config import Settings
import openai
import yaml
from time import time, sleep
import datetime

from uuid import uuid4

import os

# Import prompts path of config.py
from config import SUMMARY_CONVERSATION_PROMPT_PATH, MODIFIED_PATIENT_MESSAGE_PROMPT_PATH , STATE_SELECTOR_PROMPT_PATH, MODIFIED_PERSONAL_INFORMATION_PATIENT_PROMPT_PATH
from config import EVE_RESPONSE_PROMPT_PATH,EVE_RESPONSE_FINETUNE_PROMPT_PATH,MODIFIED_EVE_MESSAGE_PROMPT_PATH, ADVICE_STATE_PROMPT_PATH, KEEP_HEARDING_STATE_PROMPT_PATH, MEDITATE_STATE_PROMPT_PATH, WARNING_STATE_PROMPT_PATH


import threading

from config import CONVERSATION_EXAMPLES_PATH , OPENAI_API_KEY , PROMPTS_PATH, DICT_STATES, PREDEFINED_MESSAGES, CHAT_TEMPERATURE, FT_NAME

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
    def __init__(self, developer_mode = False, model_finetune = False):
        # User manager
        self.user_manager = UserManager()
        self.username = None
        os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY
        
        self.first_session = None
        self.last_session_number = None
        self.last_session_date = None

        self.current_session_number = None
        self.current_session_date = None

        self.developer_mode = developer_mode
        
        # Define if we use th
        self.model_finetune = model_finetune
        

        self.cambalache_model = ChatOpenAI(model_name = 'gpt-3.5-turbo', temperature = CAMBALACHE_TEMPERATURE)
        
        if self.model_finetune:
            # Initialize the models used for Eve
            self.chat_model = ChatOpenAI(model_name = FT_NAME, temperature = CHAT_TEMPERATURE)
        else:
            # Initialize the embedding
            self.embedding = OpenAIEmbeddings()
            
            # Initialize vectorstore of examples of conversations 
            self.vectorstore_examples_conversation = Chroma(embedding_function=self.embedding)
            
            self.prompt_state_selector = PromptTemplate.from_template("empty {empty}")
            self.chain_state_selector = LLMChain(llm = self.cambalache_model, verbose = False, 
                                                prompt = self.prompt_state_selector)
            
            self.prompt_modified_patient_message = PromptTemplate.from_template("empty {empty}")
            self.chain_modified_patient_message = LLMChain(llm = self.cambalache_model, verbose = False,
                                                        prompt=self.prompt_modified_patient_message)
            self.prompt_modified_eve_response = PromptTemplate.from_template("empty {empty}")
            self.chain_modified_eve_response = LLMChain(llm = self.cambalache_model, verbose = False,
                                                        prompt=self.prompt_modified_eve_response)
            # Initialize the models used for Eve
            self.chat_model = ChatOpenAI(model_name = 'gpt-3.5-turbo', temperature = CHAT_TEMPERATURE)
        
        # Initialize the memory of conversations
        self.memory_conversation = ChatMessageHistory()
        self.memory_conversation_modified = ChatMessageHistory()
        
        # Initialize the chains of Eve
        self.prompt_summary_conversation = PromptTemplate.from_template("empty {empty}")
        self.chain_summary_current_conversation = LLMChain(llm = self.cambalache_model, verbose = False,
                                                   prompt=self.prompt_summary_conversation)
 
        self.prompt_modified_personal_information_patient = PromptTemplate.from_template("empty {empty}")
        self.chain_personal_information_updater = LLMChain(llm = self.cambalache_model, verbose = False,
                                                           prompt = self.prompt_modified_personal_information_patient)
        
        self.prompt_eve_response = PromptTemplate.from_template("empty {empty}")
        self.chain_conversation = LLMChain(llm = self.chat_model, verbose = False, prompt = self.prompt_eve_response)
        
        
        # Initialize the chatbot
        self.initialize_chatbot()

        self.summary_complete_conversation = None
        pass

    
    def initialize_chatbot(self,):
        # Initialize the config_user_init
        self.__config_user_init()
        
        # Check if it is the first session
        self.__check_first_session()
        
        # Load the data to vector database
        if self.model_finetune == False:
            self.__load_data_to_vector_database()
        
        # Message of welcome
        self.message_of_welcome()

        # Load the masters prompt
        self.__load_prompts()
        
        # Configurate promts of chains
        self.__config_prompts_chains()
        
        pass
    

    def process_new_summary(self, conversation_history_modified, summary_holder):
        summary = self.__predict_new_summary(conversation=conversation_history_modified)
        summary_holder[0] = summary
        
    def process_similarity_search(self, patient_message_modified, similar_conversation_holder):
        similar_conversations = self.__similarity_search(patient_message_modified)
        similar_conversation_holder[0] = similar_conversations
        
    def chat(self, patient_message):
        # Obtain last messages
        last_messages = self.__obtain_n_last_messages_string(n_last_messages=2)
        # Add patient message to memory
        self.__add_user_messages_in_memory(patient_message)
        
        if self.model_finetune:
            #Obtain the conversation history
            conversation_history = self.get_complete_conversation()
            
             # Create threads for parallel processing
            personal_info_thread = threading.Thread(target=self.__update_personal_information, args=(conversation_history))
            
            summary_holder = [None]
            new_summary_thread = threading.Thread(target=self.process_new_summary, args=(conversation_history, summary_holder))
            
            # Start the threads
            personal_info_thread.start()
            new_summary_thread.start()
           
            # Wait for all threads to finish before continuing
            personal_info_thread.join()
            new_summary_thread.join()
            
            # 
            conversation_summary = summary_holder[0]
            
            eve_message = self.chain_conversation.predict(personal_information = self.personal_information,
                                                            previous_conversation_summary = conversation_summary,
                                                            last_messages=last_messages,
                                                            patient_message=patient_message
                                                            )
            if self.developer_mode:
                print(f'Original message of Eve: {eve_message}')

            # Add AI assistant message to memory
            self.__add_ai_messages_in_memory(eve_message)
            
            return eve_message
        else:
            # Modified the patient message
            conversation_history_modified = self.get_complete_conversation_modified()
            patient_message_modified = self.chain_modified_patient_message.predict(conversation= conversation_history_modified,
                                                                                last_patient_message = patient_message)
            
            if self.developer_mode:
                print(f"\n Mensaje del paciente modificado:{patient_message_modified}")
            # Add patient message modified to memory
            self.__add_user_messages_modified_in_memory(patient_message_modified)
            # Obtain conversation history modified
            conversation_history_modified = self.get_complete_conversation_modified()
            
            # Create threads for parallel processing
            personal_info_thread = threading.Thread(target=self.__update_personal_information, args=(conversation_history_modified))
            
            summary_holder = [None]
            new_summary_thread = threading.Thread(target=self.process_new_summary, args=(conversation_history_modified, summary_holder))
            
        
            similar_conversation_holder = [None]
            similarity_search_thread = threading.Thread(target=self.process_similarity_search, args=(patient_message_modified,similar_conversation_holder))

            # Start the threads
            personal_info_thread.start()
            new_summary_thread.start()
            similarity_search_thread.start()

            # Wait for all threads to finish before continuing
            personal_info_thread.join()
            new_summary_thread.join()
            similarity_search_thread.join()
            
            # 
            conversation_summary = summary_holder[0]
            similar_conversations = similar_conversation_holder[0]
            # Obtain similarity search
            similar_conversations = self.__similarity_search(patient_message_modified)
            
            # Obtain the state: 
            state = self.chain_state_selector.predict(conversation = conversation_history_modified,
                                                    last_patient_message = patient_message_modified)
            
            state_str = convert_state_str_to_variables(state)
            
            if self.developer_mode:
                print(f"\n --------Este es el estado predicho:{state_str}-------\n ")
            
            if state_str == "WARN":
                eve_message = self.chain_conversation.predict(personal_information = self.personal_information,
                                                            previous_conversation_summary = conversation_summary,
                                                            last_messages=last_messages,
                                                            conversation_examples=similar_conversations,
                                                            patient_message=patient_message_modified,
                                                            prompt_state = self.template_warning)
            elif state_str == "ADVISE":
                eve_message = self.chain_conversation.predict(personal_information = self.personal_information,
                                                            previous_conversation_summary = conversation_summary,
                                                            last_messages=last_messages,
                                                            conversation_examples=similar_conversations,
                                                            patient_message=patient_message_modified,
                                                            prompt_state = self.template_advice_state)
                pass
            elif state_str == "MEDITATE":
                eve_message = self.chain_conversation.predict(personal_information = self.personal_information,
                                                            previous_conversation_summary = conversation_summary,
                                                            last_messages=last_messages,
                                                            conversation_examples=similar_conversations,
                                                            patient_message=patient_message_modified,
                                                            prompt_state = self.template_meditate)
                pass
            elif state_str == "EXPAND LISTENING":
                eve_message = self.chain_conversation.predict(personal_information = self.personal_information,
                                                            previous_conversation_summary = conversation_summary,
                                                            last_messages=last_messages,
                                                            conversation_examples=similar_conversations,
                                                            patient_message=patient_message_modified,
                                                            prompt_state = self.template_keep_hearding_state)
            if self.developer_mode:
                print(f'Original message of Eve: {eve_message}')
            
            # Modified the eve message
            eve_message_modified = self.chain_modified_eve_response.predict(conversation = conversation_history_modified,
                                                                            last_eve_message = eve_message)
            
            # Add AI assistant message to memory
            self.__add_ai_messages_in_memory(eve_message)
            self.__add_ai_messages_in_memory_modified(eve_message_modified)

            # Print AI assistant message
            print(f"Eve :{eve_message_modified}")
            
            return eve_message_modified
    
    def get_complete_conversation_modified(self,):
        return convert_messages_in_txt(self.memory_conversation_modified.messages)
    
    def get_complete_conversation(self,):
        return convert_messages_in_txt(self.memory_conversation.messages)
    
    def finalize_chatbot(self,):
        self.user_manager.modify_last_sessions_number(self.current_session_number, self.current_session_date)
        
        # Generate the convertation txt
        complete_conversation_modified = self.get_complete_conversation_modified()
        
        # Update personal information finish session
        self.__update_personal_information(complete_conversation_modified)
        
        # Save personal information
        self.user_manager.modify_personal_information(self.personal_information)
        
        # Update summary of the complete conversation
        summary_complete_conversation = self.__predict_new_summary(complete_conversation_modified, n_last_messages = 2)
        
        # Save summary of the complete conversation
        self.user_manager.save_summary_session(summary_complete_conversation, self.current_session_number, 
                                               self.current_session_date)
        
        # Save entery conversation
        complete_conversation = self.get_complete_conversation()
        self.user_manager.save_entery_conversation(complete_conversation, self.current_session_number, self.current_session_date)
        
        pass

    def __config_prompts_chains(self,):
        # Config prompts of the chains
        self.chain_conversation.prompt = self.prompt_eve_response
        self.chain_personal_information_updater.prompt = self.prompt_modified_personal_information_patient
        self.chain_summary_current_conversation.prompt = self.prompt_summary_conversation
        if self.model_finetune == False:
            self.chain_modified_patient_message.prompt = self.prompt_modified_patient_message
            self.chain_state_selector.prompt = self.prompt_state_selector
            self.chain_modified_eve_response.prompt = self.prompt_modified_eve_response      
        
    def __config_conversation_chatbot(self,):
        if self.state == 0:
            # Config conversation prompt
            self.chain_conversation.prompt = self.prompt_first_session_master
            
        elif self.state == 1 :
            # Config conversation prompt
            self.chain_conversation.prompt = self.prompt_sessions_master
        
        # Config summarizer prompt
        self.summarizer.prompt = self.summary_conversation_prompt
        # Config personal information updater prompt
        self.chain_personal_information_updater.prompt = self.update_personal_information_prompt
        # Config summarizer finish session prompt
        self.summarizer_finish_session.prompt = self.summary_conversation_finish_session_prompt
                
    def __load_prompts(self,):
        # Load prompt of summary conversation
        template_summary_conversation = read_txt_files(SUMMARY_CONVERSATION_PROMPT_PATH)
        self.prompt_summary_conversation = PromptTemplate(input_variables=['n_messages_before', 'conversation'], 
                                                          output_parser=None, partial_variables={},template=template_summary_conversation, 
                                                        template_format='f-string', validate_template=True)

        # Load prompt of modified personal information patient
        template_modified_personal_information_patient = read_txt_files(MODIFIED_PERSONAL_INFORMATION_PATIENT_PROMPT_PATH)
        self.prompt_modified_personal_information_patient = PromptTemplate(input_variables=['conversation', 'previous_information'],
                                                                           output_parser=None, partial_variables={},
                                                                           template=template_modified_personal_information_patient, 
                                                                            template_format='f-string', validate_template=True)

        if self.model_finetune:
             # Load prompt of eve response
            template_eve_response = read_txt_files(EVE_RESPONSE_FINETUNE_PROMPT_PATH)
            self.prompt_eve_response = PromptTemplate(input_variables=['personal_information', 'previous_conversation_summary', 'last_messages','patient_message'],
                                                    output_parser=None, partial_variables={},
                                                    template=template_eve_response, 
                                                    template_format='f-string', validate_template=True)
        else:
            # Load prompt of modified patient message
            template_modified_patient_message = read_txt_files(MODIFIED_PATIENT_MESSAGE_PROMPT_PATH)
            self.prompt_modified_patient_message = PromptTemplate(input_variables=['conversation', 'last_patient_message'], 
                                                            output_parser=None, partial_variables={},template=template_modified_patient_message, 
                                                            template_format='f-string', validate_template=True)
            # Load prompt of eve response
            template_eve_response = read_txt_files(EVE_RESPONSE_PROMPT_PATH)
            self.prompt_eve_response = PromptTemplate(input_variables=['personal_information', 'previous_conversation_summary', 'last_messages', 'conversation_examples','patient_message','prompt_state'],
                                                    output_parser=None, partial_variables={},
                                                    template=template_eve_response, 
                                                    template_format='f-string', validate_template=True)
            # Load prompt of state selector
            template_state_selector = read_txt_files(STATE_SELECTOR_PROMPT_PATH)
            self.prompt_state_selector = PromptTemplate(input_variables=['conversation', 'last_patient_message'], 
                                                            output_parser=None, partial_variables={},template=template_state_selector, 
                                                            template_format='f-string', validate_template=True)
            
            # Load template of advice state, keep hearding, meditate and warning
            self.template_advice_state = read_txt_files(ADVICE_STATE_PROMPT_PATH)
            self.template_keep_hearding_state = read_txt_files(KEEP_HEARDING_STATE_PROMPT_PATH)
            self.template_meditate = read_txt_files(MEDITATE_STATE_PROMPT_PATH)
            self.template_warning = read_txt_files(WARNING_STATE_PROMPT_PATH)
            
            # Load prompt of eve modified response
            template_modified_eve_response = read_txt_files(MODIFIED_EVE_MESSAGE_PROMPT_PATH)
            self.prompt_modified_eve_response = PromptTemplate(input_variables=['conversation', 'last_eve_message'],
                                                            output_parser=None, partial_variables={},
                                                                template=template_modified_eve_response, 
                                                                template_format='f-string', validate_template=True)
    
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
        
    def __check_first_session(self,):
        # Identify the stat
        if self.last_session_number == None:
            self.first_session = True # First session
        else:
            self.first_session = False # Not first session
        
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
        self.vectorstore_examples_conversation.add_documents(documents_conversation, metadata = metadata, verbose = False)
    
        # Load history of chat sessions

        # Load summary of chat sessions
        
        # Load summary of last sessions
        
        # Load user profile
        
        # Not implemented yet
        pass
    
    def __similarity_search(self, query , n_results = 1):
        results = self.vectorstore_examples_conversation.similarity_search(query)[n_results-1]
        results_strings = results.page_content
        if self.developer_mode:
            print(f"\n --------Estos son los resultados de la busqueda:{results_strings}-------\n ")
        return results_strings
        
    def message_of_welcome(self,):
        # Read the message of welcome from the file
        with open(PREDEFINED_MESSAGES + "/welcome_messages.txt", 'r') as file:
            # Replace <<<USERNAME>>> in txt for self.username
            message = file.read().replace("<<<USERNAME>>>", self.username)
            # Print the message
            print(message)
       

    def __obtain_n_last_messages_string(self, n_last_messages = 2):
        last_messages = self.__obtain_n_last_messages(n_last_messages= n_last_messages)
        last_messages_txt = convert_messages_in_txt(last_messages)
        return last_messages_txt
        
    def __predict_new_summary(self, conversation, n_last_messages = 2):
        summary = self.chain_summary_current_conversation.predict(conversation = conversation,
                                                                  n_messages_before = n_last_messages)
        if self.developer_mode:
            print(f"\n --------Esta es el resumen generado:{summary}-------\n ")
        return summary
               
    def __obtain_last_summary(self):
        return self.summarizer.buffer()

    def __obtain_n_last_messages(self, n_last_messages = 2):
        # If the number of messages is less than n_last_messages, we obtain all the messages
        if len(self.memory_conversation_modified.messages) < n_last_messages:
            messages = self.memory_conversation_modified.messages
        else: 
            # Obtain the last n messages
            messages = self.memory_conversation_modified.messages[-n_last_messages:]
        return messages
        
    def __add_ai_messages_in_memory(self,message_content):
        self.memory_conversation.add_ai_message(message_content)
    
    def __add_user_messages_in_memory(self,message_content):
        self.memory_conversation.add_user_message(message_content)

    def __add_user_messages_modified_in_memory(self,message_content):
        self.memory_conversation_modified.add_user_message(message_content)
        
    def __add_ai_messages_in_memory_modified(self,message_content):
        self.memory_conversation_modified.add_ai_message(message_content)
        
    def __update_personal_information(self,conversation):
        # Replace the personal information 
        self.personal_information = self.chain_personal_information_updater.predict(previous_information=self.personal_information,
                                                                            conversation = conversation)
        if self.developer_mode:
            print(f"\n --------Esta es la actualizacion de la información personal:{self.personal_information}-------\n ")
    
    




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
                

