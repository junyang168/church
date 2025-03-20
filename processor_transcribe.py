from processor import Processor
import re
import jsonlines
import os
from pydub import AudioSegment
from pydub.silence import split_on_silence
import openai
from pathlib import Path
import json
from datetime import timedelta
from audio_transcriber import AudioTranscriber


class ProcessorTranscribe(Processor):
    def get_name(self):
        return "transcribe"

    def get_priority(self):
        return 1

    def get_input_folder_name(self):
        return "audio"

    def get_output_folder_name(self):
        return "script"

    def get_file_extension(self):
        return ".mp3"

    
    def process(self, input_folder, item_name:str, output_folder:str, file_name:str = None):
        trancriber = AudioTranscriber(os.path.join(output_folder,item_name))
        return trancriber.transcribe(os.path.join(input_folder,item_name + self.get_file_extension()) )




if __name__ == "__main__":
    pass