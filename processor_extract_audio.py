from processor import Processor
from moviepy.editor import VideoFileClip
import math
from utils import get_files


mp4_folder = '/Users/junyang/Downloads/video'
mp3_file_path = '/Users/junyang/Church/data/audio'
script_file_path = '/Users/junyang/Church/data/script'

class ProcessorExtractAudio(Processor):


    def get_name(self):
        return "extract audio"

    def get_priority(self):
        return 0

    def get_input_folder_name(self):
        return "/Users/junyang/Downloads/video"

    def get_output_folder_name(self):
        return "audio"

    def get_file_extension(self):
        return ".mp4"

    def process(self, input_folder, item_name:str, output_folder:str):
        # Load the video file
        fname = self.get_input_file_name(input_folder, item_name)   
        video_clip = VideoFileClip(fname)
        chunks = math.ceil(video_clip.duration / self.duration_in_seconds)
        video_clip.close()

        for chunk_index in range(chunks):    
            # Cut the first 'duration_in_seconds' of the video clip
            if chunk_index == chunks - 1 :
                end = None
            else:
                end = (chunk_index +1) * self.duration_in_seconds
            video_clip = VideoFileClip(fname)
            audio_clip = video_clip.subclip(chunk_index * self.duration_in_seconds, end).audio
            
            # Write the audio clip to an MP3 file
            mp3_file_name = f"{output_folder}/{item_name}_{chunk_index+1}.mp3"
            audio_clip.write_audiofile(mp3_file_name, codec='mp3')
            # Close the clips to release resources
            audio_clip.close()
            video_clip.close()
