import gradio as gr
import random
import time
import whisper
from chatbots import *
from TTS.api import TTS


# Initialize Eve
eve = Chatbot(developer_mode=True)
continue_chatting = True

# Definimos las funciones
def finish_session( chat_history = None):
    #global eve
    eve.finalize_chatbot()
    chat_history.append((None, "Session finished"))
    return chat_history

def transcribe_audio(audio_file,):
    model = whisper.load_model("base")
    result = model.transcribe(audio_file)
    return result["text"]

def submit_text(input_txt_patient=None, chat_history = None):
    global eve
    eve_message = eve.chat(input_txt_patient)
    #eve_message = f"Hola, {input_txt_patient}"
    #tts.tts_to_file(text=eve_message, file_path="eve_message.wav")
    
    chat_history.append((input_txt_patient, eve_message))
    #chat_history.append((None, ("eve_message.wav",)))
    
    return chat_history

def submit_mic(input_mic_patient=None, chat_history = None):
    global eve
    os.rename(input_mic_patient, input_mic_patient + '.wav')
    chat_history.append(((input_mic_patient + '.wav',), None))
    input_txt_patient = transcribe_audio(input_mic_patient + '.wav')
    #eve_message = f"Hola-111"
    eve_message = eve.chat(input_txt_patient)
    chat_history.append((input_txt_patient, eve_message))
    
    return chat_history



block = gr.Blocks()
with block:
    # This is the output
    chatbot = gr.Chatbot()
    
    # Inputs
    patient_message = gr.Textbox(label = "Write a message")
    mic_input = gr.Microphone(label = "Record a message", source="microphone", type="filepath")
    
    patient_message.submit(submit_text, [patient_message, chatbot], [chatbot])
    patient_message.submit(lambda x: gr.update(value=''), [],[patient_message])
    
    mic_input.change(submit_mic, [mic_input, chatbot], [chatbot])
    
    finish_button = gr.Button(value="Finish session")
    finish_button.click(finish_session, [chatbot], [chatbot])
    
block.launch(share=True)
    