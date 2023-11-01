import os
import time 
import datetime

from langchain import LLMChain

from prompt_config import PromptConfig_v1
from conversation_manager import ConversationManager_v1
from conversation_analysis import ConversationAnalysis_v1

from configurations.config_llm import FT_NAME, CHAT_TEMPERATURE, OPENAI_API_KEY
from configurations.config_prompts import SUMMARY_CONVERSATION_v1, PERSONAL_INFORMATION_v1, EVE_PROMPT_v1
from configurations.config_templates import PERSONAL_INFORMATION_TEMPLATE_PATH

from functions_auxiliary import read_txt_files

class BaseEve():
    def __init__(self, llm = None):
        self.model = llm
        pass
    
    def response(self, message): 
        pass
    
class Eve_v1(BaseEve):
    
    def __init__(self,):
        # Configure the API key
        os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY
        
        # Initialize the prompt manager
        self.prompt_manager = PromptConfig_v1()
        
        # Initialie the conversation manager
        self.conversation_manager = ConversationManager_v1()
        
        # Initialize the conversation analysis
        self.conversation_analysis = ConversationAnalysis_v1()
        
        # Initialize the model
        self.model = ChatOpenAI(model_name = FT_NAME, temperature = CHAT_TEMPERATURE)
        
        # Initialize the chain conversation 
        empty_prompt = self.prompt_manager.get_empty_prompt_template()
        self.chain_conversation = LLMChain(llm = self.model, verbose = False, prompt = empty_prompt)
        
        pass
    
    def initialize(self,):
        # Load prompts
        self.prompt_manager.load_prompts(paths = [SUMMARY_CONVERSATION_v1['path'], PERSONAL_INFORMATION_v1['path'], EVE_PROMPT_v1['path']],
                                         keys = ['summary_conversation', 'personal_information', 'eve_message'],
                                         input_variables = [SUMMARY_CONVERSATION_v1['input_variables'], PERSONAL_INFORMATION_v1['input_variables'], EVE_PROMPT_v1['input_variables']])
        
        # Aca tenemos que chequear si existe o no archivos de la conversacion anteriores 
        
        # Load template of personal information
        self.conversation_analysis.load_personal_information(personal_information = read_txt_files(PERSONAL_INFORMATION_TEMPLATE_PATH))
        # Load prompt for the personal information
        self.conversation_analysis.load_prompt_personal_information(prompt = self.prompt_manager.get_prompt('personal_information'))
        
        # Load prompt for the summary conversation
        self.conversation_analysis.load_prompt_summary_conversation(prompt = self.prompt_manager.get_prompt('summary_conversation'))
        
        # Load prompt for the eve message
        self.chain_conversation.prompt = self.prompt_manager.get_prompt('eve_message')
        
    def response(self, message):
        
        # We obtain the last messages
        last_messages = self.conversation_manager.get_n_last_messages()
        
        # Add patient message to memory
        self.conversation_manager.add_message(message, is_ai_message = False)
    
        # Obtain the complete current conversation
        current_conversation = self.conversation_manager.get_conversation()
        
        
        

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
    eve_message = self.chain_conversation.predict(personal_information = self.personal_information,
                                                            previous_conversation_summary = conversation_summary,
                                                            last_messages=last_messages,
                                                            patient_message=patient_message
                                                            )
    
    
        


