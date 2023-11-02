import gradio as gr
import whisper
from chatbots import *



def transcribe_audio(audio_file,):
    model = whisper.load_model("base")
    result = model.transcribe(audio_file)
    return result["text"]


# Define una función de Gradio que manejará la interacción del chatbot
def eve_interface(input_audio_patient=None, input_txt_patient=None):
    
    if input_audio_patient and (input_txt_patient is None):
        input_txt_patient = transcribe_audio(input_audio_patient.read())
    elif input_txt_patient is None and (input_audio_patient is None):
        # Generate a error message
        return "Error: No se ingresó texto ni audio."
    
    return eve.chat(input_txt_patient)
    
import os

def get_chatbot_response(x):
    os.rename(x, x + '.wav')
    return [((x + '.wav',), "Your voice sounds nice!")]

with gr.Blocks() as demo:
    chatbot = gr.Chatbot()
    mic = gr.Audio(source="microphone", type="filepath")
    mic.change(get_chatbot_response, mic, chatbot)
    
demo.launch()


if __name__ == "__main__":

    eve = Chatbot(developer_mode=False)
    continue_chatting = True

    audio_input = gr.inputs.Audio(source="microphone", type="numpy")
    button_convert_voice_2_speech = gr.Button(label="Convert voice to text")
    
    
    text_input = gr.inputs.Textbox(label="")
    
    # Crea una interfaz Gradio para hablar por micrófono o escribir texto
    iface = gr.Interface(
        fn=eve_interface,
        inputs=[audio_input, text_input],
        outputs=["text"],
        title="Chatbot de Audio a Texto o Texto a Respuesta",
        description="Habla por micrófono o ingresa texto para obtener respuestas del chatbot.",
    )
    if continue_chatting:
        iface.launch()
        
        











# def transcribe_audio(audio_file,):
#     model = whisper.load_model("base")
#     result = model.transcribe(audio_file)
#     return result["text"]


# def main():
#     audio_input = gr.inputs.Audio(source="microphone", type="numpy")
#     text_input = gr.inputs.Textbox(label="")
#     output_text = gr.outputs.Textbox()
    
#     iface = gr.Interface(fn=transcribe_audio, inputs=[audio_input,text_input], 
#                          outputs=output_text, title="Audio Transcription App",
#                          description="Upload an audio file and hit the 'Submit'\
#                              button")
    
#     iface.launch()


# if __name__ == '__main__':
#     main()