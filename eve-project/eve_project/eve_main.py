from chatbots import *


if __name__ == "__main__":

    eve = Chatbot(developer_mode=True, model_finetune=True)
    continue_chatting = True
    voice_audio = False
    while continue_chatting:
        text = input('\n\nUSER: ')
        if text.lower() == "exit":
            continue_chatting = False
            eve.finalize_chatbot()
        else:
            eve.chat(text)
        # Finalize chatbot if user types 'exit'as
    a = 20