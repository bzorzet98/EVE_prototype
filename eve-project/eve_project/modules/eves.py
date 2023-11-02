import os
import time 
import datetime

from langchain.chains import LLMChain
import threading

from prompt_config import PromptConfig_v1
from conversation_manager import ConversationManager_v1
from conversation_analysis import ConversationAnalysis_v1
from chatbot import Chatbot_v1

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
        
        # Initialize the chatbot
        self.chatbot = Chatbot_v1()
        
        # Initialize
        self.initialize()
        
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
        # Load prompt for the chatbot
        self.chatbot.load_prompt(prompt = self.prompt_manager.get_prompt('eve_message'))
             
    def response(self, message):
        # We obtain the last messages
        last_messages = self.conversation_manager.get_n_last_messages()
        
        # Add patient message to memory
        self.conversation_manager.add_message(message, is_ai_message = False)
    
        # Obtain the complete current conversation
        current_conversation = self.conversation_manager.get_conversation()
        
        # Process the personal information
        self.conversation_analysis.update_personal_information(current_conversation)
        # Obtain the new personal information
        personal_info = self.conversation_analysis.get_personal_information()
        
        # Process the summary conversation
        self.conversation_analysis.update_summary_conversation(last_messages , current_conversation)
        # Obtain the new summary conversation
        summary_conversation = self.conversation_analysis.get_summary_conversation()
        
        # Obtain the response of the chatbot
        eve_message = self.chatbot.response(message = message,
                                            personal_information = personal_info,
                                            previous_conversation_summary = summary_conversation,
                                            last_messages = last_messages)
        
        # Add AI assistant message to memory
        self.conversation_manager.add_message(eve_message, is_ai_message = True)
        
        return eve_message
    

class Eve_v2(Eve_v1):
    
    def __init__(self,):
        super().__init__()
        pass
    
    def response(self, message):
        # We obtain the last messages
        last_messages = self.conversation_manager.get_n_last_messages()
        
        # Add patient message to memory
        self.conversation_manager.add_message(message, is_ai_message = False)
    
        # Obtain the complete current conversation
        current_conversation = self.conversation_manager.get_conversation()
        
        # Init the threads for the personal information and the summary conversation
        personal_info_thread = threading.Thread(target=self._process_personal_information, args=(current_conversation,))
        summary_thread = threading.Thread(target=self._process_summary_conversation, args=(last_messages , current_conversation))
        personal_info_thread.start()
        summary_thread.start()
        personal_info_thread.join()
        summary_thread.join()
        
        # Obtain the new personal information
        personal_info = self.conversation_analysis.get_personal_information()
        # Obtain the new summary conversation
        summary_conversation = self.conversation_analysis.get_summary_conversation()
        
        # Obtain the response of the chatbot
        eve_message = self.chatbot.response(message = message,
                                            personal_information = personal_info,
                                            previous_conversation_summary = summary_conversation,
                                            last_messages = last_messages)
        
        # Add AI assistant message to memory
        self.conversation_manager.add_message(eve_message, is_ai_message = True)
        
        return eve_message
            
    def _process_personal_information(self,current_conversation):
        self.conversation_analysis.update_personal_information(current_conversation)

    def _process_summary_conversation(self,last_messages , current_conversation):
        self.conversation_analysis.update_summary_conversation(last_messages , current_conversation)

