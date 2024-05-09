import os

from google.cloud.speech_v2 import SpeechClient
from google.cloud.speech_v2.types import cloud_speech, OutputFormatConfig
from google.api_core.client_options import ClientOptions

# Instantiates a client
client = SpeechClient(
  client_options=ClientOptions(
              api_endpoint="us-central1-speech.googleapis.com",
          )    
)

base_folder = '/Users/junyang/church/data'
audio_file = base_folder + '/2019-2-18-sample.wav'
# Reads a file as bytes
with open(audio_file, "rb") as f:
    content = f.read()

# The output path of the transcription result.
workspace = "gs://dallas-holylogos/transcripts"

# The name of the audio file to transcribe:
gcs_uri = "gs://dallas-holylogos/audio-files/2019-06-02 罗五章二节.mp3"


# Recognizer resource name:
recognizer = "projects/united-idea-420514/locations/us-central1/recognizers/_"

config = cloud_speech.RecognitionConfig(
  auto_decoding_config=cloud_speech.AutoDetectDecodingConfig(),
  model="chirp",
  language_codes=["zh-Hans-CN"],
  features=cloud_speech.RecognitionFeatures(
    enable_automatic_punctuation=True,
    enable_word_time_offsets = True
  ),
)

output_config = cloud_speech.RecognitionOutputConfig(
  gcs_output_config=cloud_speech.GcsOutputConfig(
    uri=workspace)
)

files = [cloud_speech.BatchRecognizeFileMetadata(
    uri=gcs_uri
)]

request = cloud_speech.BatchRecognizeRequest(
    recognizer=recognizer, config=config, 
    recognition_output_config=output_config,
    files = files
)
operation = client.batch_recognize(request=request)
print(operation.result())