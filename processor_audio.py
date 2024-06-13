from processor import Processor
from processor_convert_video import ProcessorConvertVideo
import shutil
from metadata import update_metadata
from pydub import AudioSegment

class ProcessorAudio(Processor):
    def get_name(self):
        return "copy audio"

    def get_input_folder_name(self):
        return "/Users/junyang/Downloads/video"

    def get_output_folder_name(self):
        return "audio"

    def get_file_extension(self):
        return ".mp3"

    def process(self, input_folder, item_name:str, output_folder:str, file_name:str = None, is_append:bool = False):
        input_path = self.get_file_full_path_name(input_folder, item_name)
        audio = AudioSegment.from_mp3(input_path)
        segment_duration = 20 * 60 * 1000  # 20 minutes in milliseconds

        start = 0
        i = 1
        while start < len(audio):
            segment = audio[start:start+segment_duration]
            segment_output_path = self.get_file_full_path_name(output_folder, f"{item_name}_{i}")
            segment.export(segment_output_path, format="mp3")
            start += segment_duration
            i += 1


    def setmetadata(self, items, metadata_file: str):       
        update_metadata(metadata_file, items, 'audio')

