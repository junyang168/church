from processor import Processor
from moviepy.video.io.VideoFileClip import VideoFileClip
from utils import get_files
from metadata import update_metadata
import os

mp4_folder = '/Users/junyang/Downloads/video'
mp3_file_path = '/Users/junyang/Church/data/audio'
script_file_path = '/Users/junyang/Church/data/script'

class ProcessorConvertVideo(Processor):


    def get_name(self):
        return "convert h264"

    def get_input_folder_name(self):
        return "/Users/junyang/Downloads/video"

    def get_output_folder_name(self):
        return "video"

    def get_file_extension(self):
        return ".mp4"

    def process(self, input_folder, item_name:str, output_folder:str, file_name:str = None, is_append:bool = False):
        input_file = input_folder + '/' + file_name
        # Convert mp4 to h264 format
        try:
            video = VideoFileClip(input_file)
            video.write_videofile(output_folder + '/' + item_name + '.mp4', codec='libx264')
            video.close() 
                
            # Delete the input file
            os.remove(input_file)
            return True
        except Exception as e:
            print(f"Error converting {input_file} to h264 format: {e}")
            return False

    def setmetadata(self, items, metadata_file: str): 
        update_metadata(metadata_file, items, 'video')      

    def accept_media_type(self):
        return "video"


if __name__ == "__main__":
    # Create an instance of ProcessorConvertVideo
    processor = ProcessorConvertVideo()

    mp4_folder = '/Users/junyang/Downloads/video'

    processor.process(mp4_folder, '2019-2-15 心mp4', '/Users/junyang/Church/data/video')

    # Print a message when the processing is done
    print("Video conversion completed.")