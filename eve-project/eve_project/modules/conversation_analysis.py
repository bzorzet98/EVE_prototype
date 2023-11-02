from configurations.config_llm import CAMBALACHE_TEMPERATURE
from langchain.prompts import PromptTemplate 
from langchain.chains import LLMChain
from langchain.chat_models import ChatOpenAI

class BaseConversationAnalysis(object):
    """
    Base class for conversation analysis modules.
    """

    def __init__(self, ):
        pass

    def run(self):
        """
        Run the analysis.
        """
        raise NotImplementedError
    
class ConversationAnalysis_v1(BaseConversationAnalysis):
    def __init__(self):
        # Model for the conversation analysis
        self.cambalache_model = ChatOpenAI(model_name = 'gpt-3.5-turbo', temperature = CAMBALACHE_TEMPERATURE)
        
        # Personal information updater
        self.personal_information_updater = PersonalInformationUpdater_v1()
        
        # Summary conversation updater
        self.summary_conversation_updater = SummaryConversation_v1()
        pass
    
    def load_personal_information(self, personal_information):
        # Check if personal_information is a string
        if not isinstance(personal_information, str):
            raise TypeError("personal_information must be a string")
        
        self.personal_information_updater.load_personal_information(personal_information)
    
    def load_prompt_personal_information(self, prompt):
        self.personal_information_updater.load_prompt(prompt, self.cambalache_model)
        
    def update_personal_information(self, conversation):
        self.personal_information_updater.update(conversation)
        
    def get_personal_information(self,):
        return self.personal_information_updater.get_information()
    
    def load_prompt_summary_conversation(self, prompt):
        self.summary_conversation_updater.load_prompt(prompt, self.cambalache_model)
        
    def update_summary_conversation(self, n_messages_before, conversation):
        self.summary_conversation_updater.update(n_messages_before, conversation)
        
    def get_summary_conversation(self,):
        return self.summary_conversation_updater.get_information()
    


class PersonalInformationUpdater_v1():
    def __init__(self,):
        # Define the personal information
        self.personal_information = ""
        # Define the updater
        self.updater = None
        self.prompt = None
        # Define the requiered inputs variables
        self.required_input_variables = ['conversation', 'previous_information']
        pass
    
    def load_personal_information(self, personal_information):
        # Check that personal_information is a string
        if not isinstance(personal_information, str):
            raise TypeError("personal_information must be a string")
        
        self.personal_information = personal_information
        
    def load_prompt(self, prompt, model): 
        # Check if prompt is a PromptTemplate
        if not isinstance(prompt, PromptTemplate):
            raise TypeError("prompt must be a PromptTemplate")
        
        #Check that model is in chat_models 
        if not isinstance(model, ChatOpenAI):
            raise TypeError("model must be a ChatOpenAI")
        
        # Check that the prompt has the required input variables
        for required_input_variable in self.required_input_variables:
            if required_input_variable not in prompt.input_variables:
                raise ValueError(f"The prompt must have the input variable {required_input_variable}")
            
        self.prompt = prompt
        
        # Load the prompt
        self.updater = LLMChain(llm = model, verbose = False, prompt = prompt)
        
    def update(self, conversation):
        # Check that the updater is not None
        if self.updater is None:
            raise ValueError("The updater has not been loaded")
        
        # Check that the conversation is a string
        if not isinstance(conversation, str):
            raise TypeError("conversation must be a string")
        
        # Check that the previous_information is a string
        if not isinstance(self.personal_information, str):
            raise TypeError("previous_information must be a string")
        
        # Obtain the new personal information
        self.personal_information = self.updater.predict(conversation = conversation, previous_information = self.personal_information)
        
    def get_information(self):
        return self.personal_information

class SummaryConversation_v1():
    def __init__(self,):
        # Define the summary
        self.summary = None
        # Define the updater
        self.updater = None
        self.prompt = None
        # Define the requiered inputs variables
        self.required_input_variables = ['n_messages_before', 'conversation']
        
    def load_prompt(self, prompt, model): 
        # Check if prompt is a PromptTemplate
        if not isinstance(prompt, PromptTemplate):
            raise TypeError("prompt must be a PromptTemplate")
        
        #Check that model is in chat_models 
        if not isinstance(model, ChatOpenAI):
            raise TypeError("model must be a ChatOpenAI")
        
        # Check that the prompt has the required input variables
        for required_input_variable in self.required_input_variables:
            if required_input_variable not in prompt.input_variables:
                raise ValueError(f"The prompt must have the input variable {required_input_variable}")
            
        self.prompt = prompt
        
        # Load the prompt
        self.updater = LLMChain(llm = model, verbose = False, prompt = prompt)
        
    def update(self,n_messages_before, conversation):
        # Check that the updater is not None
        if self.updater is None:
            raise ValueError("The updater has not been loaded")
        
        # Check that the conversation is a string
        if not isinstance(conversation, str):
            raise TypeError("conversation must be a string")
        
        # Check that the previous_information is a string
        if not isinstance(n_messages_before, str):
            raise TypeError("n_messages_before must be a string")
        
        # Obtain the new personal information
        self.summary = self.updater.predict(n_messages_before = n_messages_before, conversation = conversation)
        
    def get_information(self):
        return self.summary


    
    