from processor import Processor
from moviepy.editor import VideoFileClip
import math
from utils import get_files


mp4_folder = '/Users/junyang/Downloads/video'
mp3_file_path = '/Users/junyang/Church/data/audio'
script_file_path = '/Users/junyang/Church/data/script'

class ProcessorExtractAudio(Processor):
    duration_in_seconds = 20*60 # 20 mins

    def get_name(self):
        return "extract audio"

    def get_priority(self):
        return 0

    def get_input_folder_name(self):
        return "video"

    def get_output_folder_name(self):
        return "audio"

    def get_file_extension(self):
        return ".mp4"

    def process(self, input_folder, item_name:str, output_folder:str, file_name:str = None, is_append:bool = False):
        # Load the video file
        fname = self.get_file_full_path_name(input_folder, item_name)   
        video_clip = VideoFileClip(fname)

        # Extract audio into mp3 file
#        mp3_file_name = f"{output_folder}/{item_name}.mp3"
#        video_clip.audio.write_audiofile(mp3_file_name, codec='mp3')
#        return


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

if __name__ == '__main__':
    base_folder = '/Users/junyang/church/data'  
    processor = ProcessorExtractAudio()
    processor.process(base_folder + '/' + 'video', '2019-07-28 罗马书六章1节', base_folder + '/audio')
    pass