from moviepy.editor import VideoFileClip
import math
from utils import get_files

mp4_folder = '/Users/junyang/Downloads/video'
mp3_file_path = '/Users/junyang/Church/data/audio'
script_file_path = '/Users/junyang/Church/data/script'



def extract_audio(mp4_folder, mp4_file_name, mp3_file_folder, duration_in_seconds=300):
    """
    Extracts the first 'duration_in_seconds' of audio from an MP4 file and saves it as an MP3 file.
    
    :param mp4_file_path: Path to the input MP4 file.
    :param mp3_file_path: Path where the output MP3 file will be saved.
    :param duration_in_seconds: Duration in seconds of the audio to be extracted. Defaults to 300 seconds (5 minutes).
    """
    # Load the video file

    video_clip = VideoFileClip(mp4_folder + '/' + mp4_file_name)
    chunks = math.ceil(video_clip.duration / duration_in_seconds)
    video_clip.close()

    for chunk_index in range(chunks):    
        # Cut the first 'duration_in_seconds' of the video clip
        if chunk_index == chunks - 1 :
            end = None
        else:
            end = (chunk_index +1) * duration_in_seconds
        video_clip = VideoFileClip(mp4_folder + '/' + mp4_file_name)
        audio_clip = video_clip.subclip(chunk_index * duration_in_seconds, end).audio
        
        mp3_file_name = mp4_file_name.split('.')[0]
        # Write the audio clip to an MP3 file
        mp3_file_name = f"{mp3_file_folder}/{mp3_file_name}_{chunk_index+1}.mp3"
        audio_clip.write_audiofile(mp3_file_name, codec='mp3')
        # Close the clips to release resources
        audio_clip.close()
        video_clip.close()

def extra_audio(mp4_folder :str, mp3_file_folder:str):
    mp4_files = get_files(mp4_folder,'.mp4')
    for mp4_file in mp4_files:
        extract_audio(mp4_folder, mp4_file, mp3_file_folder, 60*20)


def transcribe(mp3_file_name:str, script_file_name:str,  is_append:bool = False):
    from openai import OpenAI
    client = OpenAI()

    with open(mp3_file_name, "rb") as audio_file:
        transcription = client.audio.transcriptions.create(
            model="whisper-1", 
            file=audio_file
        )

        file1 = open(script_file_name, 'a' if is_append else 'w')
        file1.write(transcription.text)
        file1.close()

def transribe_all_audio(mp3_file_path:str, script_file_path:str):
    mp3_files = get_files(mp3_file_path,'.mp3')
    mp3_files.sort()
    script_name = ''
    for fname in mp3_files:
#        if fname.find('2019-3-24 罗马书3章21至31节') < 0:
#            continue
        if  script_name != fname.split('_')[0]:
            script_name = fname.split('_')[0] 
            is_append = False
        else:
            is_append = True        
        transcribe(f"{mp3_file_path}/{fname}",f'{script_file_path}/{script_name}.txt',is_append=is_append )

    for mp3_file in mp3_files:
        transcribe(mp3_file_path, mp3_file, script_file_path)

#extra_audio(mp4_folder,mp3_file_path)
transribe_all_audio(mp3_file_path, script_file_path)
