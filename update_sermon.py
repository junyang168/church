import json

base_dir = '/Volumes/Jun SSD/data/config'

def get_item_date(video_file:str):
    if video_file.startswith('S '):
        return '20{}-{}-{}'.format(video_file[2:4], video_file[4:6], video_file[6:8])
    elif video_file[:6].isdigit():
        return '20{}-{}-{}'.format(video_file[:2], video_file[2:4], video_file[4:6])
    elif video_file.startswith('2019-'):
        return video_file[5:10]
    else:
        raise ValueError('Invalid video file name: {}'.format(video_file))

def get_item_title(video_file:str):
    if video_file.startswith('S ') and video_file[2:8].isdigit():
        return video_file[8:-4].strip()
    else:
        return ''

with open(base_dir + '/master_video.json') as f:
    master_data = json.load(f)

with open(base_dir + '/sermon.json') as json_file:
    sermon_data = json.load(json_file)

for video_file in master_data:
    sermon = next((item for item in sermon_data if item['item'] + '.mp4' == video_file), None)
    if not sermon:
        sermon =   {
        "item": video_file[:-4],
        "status": "in development",
        "last_updated": "2025-03-07T22:20:11Z",
        "author": "dallas.holy.logos@gmail.com",
        "type": "video",
        "deliver_date": get_item_date(video_file),
        "title": get_item_title(video_file)
        }
        sermon_data.append(sermon)
    elif not sermon['item'].startswith('2019-'):
        sermon['title'] = get_item_title(video_file)

sermon_data = [sermon for sermon in sermon_data if sermon['item'].startswith('2019-') or sermon['item'] + '.mp4' in master_data]

with open(base_dir + '/sermon.json', 'w') as json_file:
    json.dump(sermon_data, json_file, indent=4, ensure_ascii=False)

