import gradio as gr
import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
module_path = os.path.join(current_dir, "modules")
sys.path.append(module_path)

from modules.eves import Eve_v4

if __name__ == "__main__":
    # Initialize Eve
    eve = Eve_v4()
    eve.initialize()

    # Define the function to call in the UI
    def response_text(input_patient, chat_history = None):
        global eve
        # Obtain the response of Eve
        eve_message = eve.response_with_audio(input_patient)
        # Print the response of Eve
        chat_history.append((input_patient, eve_message))
    
        return chat_history
    
    def response_audio(input_patient=None, chat_history = None):
        global eve
        os.rename(input_patient, input_patient + '.wav')
        chat_history.append(((input_patient + '.wav',), None))
        eve_message = eve.response_with_audio(input_patient + '.wav', audio_flag=True)
        chat_history.append((None, eve_message))
        return chat_history
    

    def finish_session( chat_history = None):
        #global eve
        eve.finalize()
        chat_history.append((None, "Session finished"))
        return chat_history

    block = gr.Blocks()
    with block:
        # This is the output
        chatbot = gr.Chatbot()
        
        # Inputs
        patient_message = gr.Textbox(label = "Write a message")
        mic_input = gr.Microphone(label = "Record a message", type="filepath")
        
        patient_message.submit(response_text, [patient_message, chatbot], [chatbot])
        patient_message.submit(lambda x: gr.update(value=''), [],[patient_message])
        
        mic_input.change(response_audio, [mic_input, chatbot], [chatbot])
        
        finish_button = gr.Button(value="Finish session")
        finish_button.click(finish_session, [chatbot], [chatbot])
        
    block.queue().launch(share=True)
        