import os
import io
from google.cloud import speech_v2 as speech
from google.cloud.speech_v2.types import  RecognitionConfig

# Set up the Google Cloud Speech-to-Text client
#os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'path/to/your/google-cloud-credentials.json'
client = speech.SpeechClient()

# Set the audio file path
base_folder = '/Users/junyang/church'
#audio_file = '2019-06-02 罗五章二节.mp3'
audio_file = 'data/2019-2-18-sample_2.mp3'
audio_file = os.path.join(base_folder, audio_file)

# Set the language code for Chinese
language_code = 'zh-CN'

# Configure the recognition request
config = RecognitionConfig(    
    auto_decoding_config=speech.AutoDetectDecodingConfig(),
     model="chirp_2",
    language_codes=[language_code]
)

# Load the audio file
with io.open(audio_file, 'rb') as audio:
    audio_content = audio.read()

# Create the recognition audio object
audio_file = RecognitionAudio(content=audio_content)

# Transcribe the audio
response = client.recognize(config=config, audio=audio_file)

# Write the transcription to a file with timestamps
with open('transcription.txt', 'w', encoding='utf-8') as f:
    for result in response.results:
        alternative = result.alternatives[0]
        start_time = alternative.start_time.total_seconds()
        end_time = alternative.end_time.total_seconds()
        f.write(f"[{start_time:.2f} - {end_time:.2f}] {alternative.transcript}\n")