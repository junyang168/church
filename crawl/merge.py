import os
import json

base_dir = '/Volumes/Jun SSD/data'

from pydub import AudioSegment
import os

def merge_audio_files(file1_path, file2_path, output_path):
    # Load the two audio files
    audio1 = AudioSegment.from_file(file1_path)
    audio2 = AudioSegment.from_file(file2_path)
    
    # Merge the audio files
    merged_audio = audio1 + audio2
    
    # Export the merged audio as MP3
    merged_audio.export(output_path, format="mp3")
    print(f"Merged audio saved to {output_path}")


with open(base_dir + '/config/sermon.json', 'r') as f:
    metadata = json.load(f)

metadata_gtl = [sermon for sermon in metadata if 'type' not in sermon]
input_folder = os.path.join(base_dir, 'audio_rm')
output_folder = os.path.join(base_dir, 'audio')

for i, sermon in enumerate(metadata_gtl):
    if sermon['item'][-1] =='b':
        continue
    sermon2 = metadata_gtl[i+1]
#    merge_audio_files(
#        os.path.join(input_folder, f"{sermon['item']}.rm"),
#        os.path.join(input_folder, f"{sermon2['item']}.rm"),
#        os.path.join(output_folder, f"{sermon['item'][:-1]}.mp3")
#    )
    sermon['item'] = sermon['item'][:-1]
    sermon['type'] = 'audio'
    sermon['source'] = 'http://www.gtl.org'

metadata = [sermon for sermon in metadata if 'type' in sermon  ]
with open(base_dir + '/config/sermon.json', 'w') as f:
    json.dump(metadata, f, indent=4, ensure_ascii=False)
