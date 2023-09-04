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




def voice_chat(user_voice):

    messages = [
    {"role": "system", "content": "You are a kind helpful assistant."},
    ]
    user_message = model.transcribe(user_voice)["text"]

    #reply = user_message
    messages.append(
        {"role": "user", "content": user_message},
    )
    print(messages)
    chat = openai.ChatCompletion.create(
        model="gpt-3.5-turbo", messages=messages
    )
    
    reply = chat.choices[0].message.content
    
    messages.append({"role": "assistant", "content": reply})

    tts.tts_to_file(text=reply, file_path="output.wav") 

    return(reply, 'output.wav')


text_reply = gr.Textbox(label="ChatGPT Text")
voice_reply = gr.Audio('output.wav')

gr.Interface(
    title = 'AI Voice Assistant with ChatGPT AI', 
    fn=voice_chat, 
    inputs=[
        gr.inputs.Audio(source="microphone", type="filepath")
    ],

    outputs=[
        text_reply,  voice_reply
    ], live = True).launch(debug = True)

     

