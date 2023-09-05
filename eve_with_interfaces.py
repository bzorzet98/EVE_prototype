import gradio as gr
import random
import time
import whisper
from chatbots import *
from TTS.api import TTS


# Initialize Eve
eve = Chatbot(developer_mode=True)
continue_chatting = True
block = gr.Blocks()



#tts.tts_to_file(text="I love playing Chess", file_path="output.wav")

     


# Definimos las funciones
def finish_session():
    global eve
    eve.finalize_chatbot()
    return "Session finished"

def transcribe_audio(audio_file,):
    model = whisper.load_model("base")
    result = model.transcribe(audio_file)
    return result["text"]

def submit_function(input_audio_patient=None, input_txt_patient=None, chat_history = None):
    global eve
    if input_audio_patient and (input_txt_patient is None):
        input_txt_patient = transcribe_audio(input_audio_patient.read())
    elif input_txt_patient is None and (input_audio_patient is None):
        # Generate a error message
        return "Error: No se ingresó texto ni audio."
    eve_message = eve.chat(input_txt_patient)
    chat_history.append((input_txt_patient, eve_message))
    return chat_history



with block:
    chatbot = gr.Chatbot()
    
    patient_message = gr.Textbox(label = "Write a message")

    audio_input = gr.inputs.Audio(label = "Record a message", source="microphone", type="numpy")
    
    submmit_button = gr.Button(value="Send message")
    
    finish_button = gr.Button(value="Finish session")
    
    submmit_button.click(submit_function, inputs=[audio_input, patient_message, chatbot], outputs=chatbot)
    
    
    
    
    
    # btn.click(combine, inputs=[txt, txt_2], outputs=[txt_3])
    
    # def respond(message, chat_history):
    #     global variable_global
    #     bot_message =  eve.chat(message)
    #     chat_history.append((message, bot_message))
    #     return "", chat_history
    
    # msg.submit(respond, [msg, chatbot], [msg, chatbot])


if __name__ == "__main__":
    block.launch()