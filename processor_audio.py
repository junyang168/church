from processor import Processor
from processor_convert_video import ProcessorConvertVideo
import shutil
from metadata import update_metadata

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
        output_path = self.get_file_full_path_name(output_folder, item_name)
        shutil.copy(input_path, output_path)

    def setmetadata(self, items, metadata_file: str):       
        update_metadata(metadata_file, items, 'audio')

