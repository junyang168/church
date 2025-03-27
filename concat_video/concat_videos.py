import ffmpeg
import os
from collections import defaultdict
import json

# Get all mp4 files from a folder
folder_path = '/Volumes/Jun SSD/data/video'
video_files = [file for file in os.listdir(folder_path) if file.endswith(".mp4")]

# Filter files that contain a hyphen in their name
video_folder_name = [file.split('-') for file in video_files if file.startswith("S ") and '-' in file]

# Group files by folder name
grouped_videos = defaultdict(list)
for nt in video_folder_name:
    folder, file = nt[0], nt[1]
    grouped_videos[folder].append( folder + '-' + file)

video_files = [file for file in os.listdir(folder_path) if file.endswith(".mp4")]

processed_videos = [file.split(' ')[0].split('-') for file in video_files if file.startswith("2019")]

processed_videos = [f"{int(file[0]):02d}{int(file[1]):02d}{int(file[2]):02d}" for file in processed_videos]
processed_videos.sort()

master_list=  [file for file in video_files if not ( file.startswith('S ') and len( file.split('-')[0]) == 8 )  ]

for folder in grouped_videos:
    if len(folder) != 8:
        continue
    if folder.startswith("S ") and f'20{folder[2:]}'  in processed_videos:
        print(f"{folder} already processed. Skipping.")
        continue    
    input_files = grouped_videos[folder]
    if len(input_files) == 1:
        master_list.append(folder + '/' + input_files[0])
        continue
    input_files.sort()
    input_files = [os.path.join(folder_path, file) for file in input_files] 
    # Create stream objects
    streams = [ffmpeg.input(file) for file in input_files]


    full_name = f"{folder[2:]}.mp4"
    master_list.append(full_name)
    concat_file_name = os.path.join('/Volumes/Jun SSD/data/full_video', )

    if os.path.exists(concat_file_name):
        print(f"File {concat_file_name} already exists. Skipping concatenation.")
        continue

    # Concatenate and output
    (ffmpeg
        .concat(*streams)
        .output( concat_file_name , c="copy",vcodec='libx264', acodec='aac')
        .run()
    )

master_list.sort()

with open('/Volumes/Jun SSD/data/config/master_video.json', 'w') as f:
    json.dump(master_list, f, indent=4, ensure_ascii=False)

print('Master list saved to /Volumes/Jun SSD/data/config/master_video.json with {} files'.format(len(master_list)))
