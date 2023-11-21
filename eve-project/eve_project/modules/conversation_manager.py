from langchain.memory import ChatMessageHistory
from functions_auxiliary import convert_messages_in_txt, save_as_txt, read_txt_file

class BaseConversationManager():
    def __init__(self,):
        pass
    
    def load_conversation(self, path):
        pass
    
    def save_conversation(self, path):
        pass
    
    
class ConversationManager_v1(BaseConversationManager):
    def __init__(self,):
        super().__init__()
        
        # Initialize the memory of current conversation
        self.memory_current_conversation = ChatMessageHistory()
        
        pass
    
    def load_conversation(self, path):
        pass
    
    def save_conversation(self, path):
        pass
    
    def add_message(self, message, is_ai_message = False):
        if is_ai_message:
            self.memory_current_conversation.add_ai_message(message)
        else:
            self.memory_current_conversation.add_user_message(message)
    
    def get_conversation(self,):
        return convert_messages_in_txt(self.memory_current_conversation.messages)
    
    def get_n_last_messages(self, n_last_messages = 2):
        # If the number of messages is less than n_last_messages, we obtain all the messages
        if len(self.memory_current_conversation.messages) < n_last_messages:
            messages = self.memory_current_conversation.messages
        else:
            # Obtain the last n messages
            messages = self.memory_current_conversation.messages[-n_last_messages:]
        return convert_messages_in_txt(messages)
    
    
    
    


    
    
