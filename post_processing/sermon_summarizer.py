import os
import json
#from together import Together
#from groq import Groq
import os
from openai import OpenAI
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from llm import call_llm
import re
import requests


class Summarizer:

    def get_summary(self, article: str):
        json_format = """
        ```json
        {
            "theme": "空坟墓",
            "summary":"讲道通过分析圣经记载与历史背景，强调耶稣的空坟墓是复活的核心证据。指出犹太传说与福音书的一致性，揭露罗马兵丁证词的矛盾（如承认睡觉却声称门徒偷尸），反驳了门徒偷尸体的虚假说法。同时阐明哥林多前书15章虽未直接提及空坟墓，但隐含耶稣身体转变的连续性，论证复活是真实历史事件，奠定基督教信仰根基。",
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

        ai_prompt = f"""你是一位資深的基督教福音派的教授。你的任務是
        1. 总结下面讲道的主題(theme)，
        2. 一個不超過 100 字的簡介，
        3. 主要观点(keypoints)
        4. 聖經的核心章節(core_bible_verse). 
        注意：
        1。回答繁體中文。 
        2. 聖經核心章節使用和合本聖經。
        3. 回答符合以下JSON格式:
        {json_format}
        牧師講道內容：{article}
        """              
        provider = os.getenv("PROVIDER")

        kp =  call_llm(provider, ai_prompt)
        return kp

if __name__ == '__main__':
    import time    
    base_folder = '/opt/homebrew/var/www/church/web/data'  
    meta_file_name = base_folder + '/config/' + 'sermon.json'
    processor = Summarizer()
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
        sermon['summary'] = kp['summary']

        with open(meta_file_name, 'w') as fsc:
            json.dump(metadata, fsc, indent=4, ensure_ascii=False)
        
        # pause for 10 seconds to avoid rate limit
        time.sleep(10)
        


