from processor import Processor
import openai
import os
import json
#from together import Together
#from groq import Groq
import os
from openai import OpenAI
from metadata import update_metadata_item_title
from llm import call_llm
import re
import requests





class ProcessorGetKeypoints:
    def get_name(self):
        return "Keypoints"

    def get_input_folder_name(self):
        return "script_published"

    def get_output_folder_name(self):
        return "script_keypoints"

    def get_file_extension(self):
        return ".json"
    


    def get_keypoints(self, article: str):
        json_format = """
        ```json
        [
            {
                "keypoint": "觀點 1",
                "related_bible_verse": [
                    {
                        "book": "羅馬書",
                        "chapter_verse": "1:1-3",
                        "content": "論到他兒子─我主耶穌基督。按肉體說，是從大衛後裔生的"
                    }
                ] 
            }
        ]
        ```
        """

        ai_prompt = f"""你是一位資深基督教牧師。請总结下面牧师讲道主要观点(keypoint)及和每个观点相关的最重要的圣经章节(related_bible_verse). 注意：
        1. 每个观点返回最多两个相关圣经章节。
        2。回答繁體中文。 
        3. 回答符合以下JSON格式:
        {json_format}
        牧師講道內容：{article}
        """              
        provider = os.getenv("PROVIDER")

        kp =  call_llm(provider, ai_prompt)
        return kp
        

    
    def process(self, sermon_meta, script):

        paragraphs = script['script']

        theme = sermon_meta['theme'] if sermon_meta['theme'] else sermon_meta['title']

        article = theme + '\n\n' + '\n\n'.join( [ p['text'] for p in paragraphs ] )

        kps = self.get_keypoints(article)

        kps =  { 'id': item_name, 'title': sermon_meta['title'], 'them': theme, 'kps': kps, 'published_updated': script['metadata']['last_updated'] }

        return kps
        


if __name__ == '__main__':
    base_folder = '/opt/homebrew/var/www/church/web/data'  
    meta_file_name = base_folder + '/config/' + 'sermon.json'
    processor = ProcessorGetKeypoints()
    with open(meta_file_name, 'r') as fsc:
        metadata = json.load(fsc)
    
    kpfile = base_folder + '/' + processor.get_output_folder_name() + '/keypoints.json'
    with open(kpfile, 'r') as fsc:
        keypoints = json.load(fsc)

    user_id = 'junyang168@gmail.com'

    url = "http://127.0.0.1:8000/sc_api/final_sermon/junyang168@gmail.com/" 

    for sermon in metadata:
        item_name = sermon['item']
        if sermon['status'] == 'in development':
            continue

        print(item_name)

        kp_item = next((item for item in keypoints if item['id'] == item_name), None)

        response = requests.get(url + item_name)
        sermon_detail = response.json()

        if kp_item and kp_item.get('published_updated','') == sermon_detail['metadata']['last_updated']:
                continue

        if kp_item:
            keypoints.remove(kp_item)


        kp = processor.process(
            sermon,
            sermon_detail)
        keypoints.append(kp)

        with open(kpfile, 'w') as fsc:
            json.dump(keypoints, fsc, indent=4, ensure_ascii=False)
        


