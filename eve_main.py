from chatbots import *


if __name__ == "__main__":

    eve = Chatbot()
    continue_chatting = True
    while continue_chatting:

        text = input('\n\nUSER: ')
        
        if text.lower() == "exit":
            continue_chatting = False
            eve.finalize_chatbot()
        else:
            eve.chat(text)
        # Finalize chatbot if user types 'exit'
        
        
        
    a = 20



