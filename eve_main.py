from chatbots import *


if __name__ == "__main__":

    eve = Chatbot(developer_mode=True)
    continue_chatting = True
    voice_audio = False
    while continue_chatting:
        text_audio = input('\n\nAudio (y/n): ')
        if text_audio.lower() == "y":
            voice_audio = True
        text = input('\n\nUSER: ')
        if text.lower() == "exit":
            continue_chatting = False
            eve.finalize_chatbot()
        else:
            eve.chat(text)
        # Finalize chatbot if user types 'exit'
    a = 20