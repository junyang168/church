import assemblyai as aai
import os
aai.settings.api_key = "5e618aa12a1044178b85b6876ffcfb3b"
config = aai.TranscriptionConfig(language_code="zh", punctuate=True, format_text=True)

transcriber = aai.Transcriber(config=config)
base_dir = os.path.join( os.path.dirname(os.path.abspath(__file__)) ,'..','data')
audio_file_path = os.path.join(base_dir, "audio/2019-2-18 良心_1.mp3")
transcript = transcriber.transcribe(audio_file_path)
print(transcript.text)
