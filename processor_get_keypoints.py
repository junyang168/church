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
        {
            "theme": "空坟墓",
            "keypoints": "1. 觀點 1 \n\n 2. 觀點 2",
            "core_bible_verse": [
                {
                    "book": "羅馬書",
                    "chapter_verse": "1:1-3",
                    "text": "耶穌基督的僕人保羅，奉召為使徒，特派傳神的福音。這福音是神從前藉眾先知在聖經上所應許的, 論到他兒子我主耶穌基督。按肉體說，是從大衛後裔生的"
                }
            ] 
        }
        ```
        """

        ai_prompt = f"""你是一位基督教福音派的教授。总结下面讲道的主題(theme)，主要观点(keypoints)及聖經的核心章節(core_bible_verse). 注意：
        1。回答繁體中文。 
        2. 聖經核心章節使用和合本聖經。
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

        return kps
        


if __name__ == '__main__':
    import time    
    base_folder = '/opt/homebrew/var/www/church/web/data'  
    meta_file_name = base_folder + '/config/' + 'sermon.json'
    processor = ProcessorGetKeypoints()
    with open(meta_file_name, 'r') as fsc:
        metadata = json.load(fsc)
    

    user_id = 'junyang168@gmail.com'

    url = "http://127.0.0.1:8000/sc_api/final_sermon/junyang168@gmail.com/" 

    for idx, sermon in enumerate( metadata):
        item_name = sermon['item']
        if sermon['status'] == 'in development':
            continue


        if sermon.get('keypoints'):
            print(f"Keypoints for {item_name} already exists.")
            continue
 
        print(f"{idx}: {item_name}")

        response = requests.get(url + item_name)
        sermon_detail = response.json()

        kp = processor.process(
            sermon,
            sermon_detail)

        sermon['keypoints'] = kp['keypoints']
        sermon['core_bible_verse'] = kp['core_bible_verse']
        sermon['theme'] = kp['theme']

        with open(meta_file_name, 'w') as fsc:
            json.dump(metadata, fsc, indent=4, ensure_ascii=False)
        
        # pause for 10 seconds to avoid rate limit
        time.sleep(10)
        


