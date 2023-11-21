import whisper

class S2T_with_whisper():
    def __init__(self,):
        self.model = whisper.load_model("base.en")
        
    def transcribe(self, audio_file,):
        result = self.model.transcribe(audio_file)
        return result["text"]