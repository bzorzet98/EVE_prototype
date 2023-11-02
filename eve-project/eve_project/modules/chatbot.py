from langchain.prompts import PromptTemplate
from langchain.chat_models import ChatOpenAI
from langchain.chains import LLMChain

from configurations.config_llm import FT_NAME, CHAT_TEMPERATURE


class BaseChatbot():
    def __init__(self,):
        pass
    
    def response(self, message):
        pass
    
    
class Chatbot_v1(BaseChatbot):
    def __init__(self, model_name = FT_NAME, temperature = CHAT_TEMPERATURE):
        self.prompt = PromptTemplate.from_template("empty {empty}")
        self.model = ChatOpenAI(model_name = model_name, temperature = CHAT_TEMPERATURE)
        self.chain_conversation = LLMChain(llm = self.model, verbose = False, prompt = self.prompt )
        self.required_input_variables = ['personal_information', 'previous_conversation_summary', 'last_messages','patient_message']
        
    def load_prompt(self,prompt):
        # Check if prompt is a PromptTemplate
        if not isinstance(prompt, PromptTemplate):
            raise TypeError("prompt must be a PromptTemplate")
        # Check that the prompt has the required input variables
        for required_input_variable in self.required_input_variables:
            if required_input_variable not in prompt.input_variables:
                raise ValueError(f"The prompt must have the input variable {required_input_variable}")
        self.prompt = prompt
        # Load the prompt
        self.chain_conversation = LLMChain(llm = self.model, verbose = False, prompt = prompt)

    def response(self, message, personal_information = str(None), 
                 previous_conversation_summary = str(None), 
                 last_messages = str(None)):
        
        return self.chain_conversation.predict(personal_information = personal_information,
                                                previous_conversation_summary = previous_conversation_summary,
                                                last_messages=last_messages,
                                                patient_message=message)
