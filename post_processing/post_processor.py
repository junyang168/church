
from sermon_summarizer import Summarizer
import os
import json
import requests
import time


def get_sermon_meta(sermon_meta, item:str):
    return next((s for s in sermon_meta if s['item'] == item), None)

def save_sermon_meta(sermon_meta, file_path):
    with open(file_path, 'w') as fsc:
        json.dump(sermon_meta, fsc, indent=2, ensure_ascii=False)

def main():
    base_folder = '/Users/junyang/church/web/data'  
    processor = Summarizer()
    sermon_content_folder = base_folder + '/sermon_content'
    cfg_file_name = base_folder + '/config/' + 'sermon.json'
    with open(cfg_file_name, 'r') as fsc:
        sermon_meta = json.load(fsc)

    sermon_files = [f for f in os.listdir(sermon_content_folder) if f.endswith('.json')]
    for file_name in sermon_files:
        with open(os.path.join(sermon_content_folder, file_name), 'r') as sf:
            sermon = json.load(sf)
            article = '\n\n'.join([p.get('text', '') for p in sermon.get('script', [])])
            article = sermon['metadata']['title'] + '\n\n' + article
            summary_info = processor.get_summary(article)
            time.sleep(1)  # 避免过快调用API导致限制
            meta = get_sermon_meta(sermon_meta, sermon['metadata']['item'])
            if meta:
                meta['summary'] = summary_info['summary']
                meta['keypoints'] = summary_info['keypoints']
                meta['core_bible_verse'] = summary_info['core_bible_verse']
                meta['theme'] = summary_info['theme']
                save_sermon_meta(sermon_meta, cfg_file_name)

if __name__ == "__main__":
    main()