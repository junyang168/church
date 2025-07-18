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


class ProcessorSummarize(Processor):
    def get_name(self):
        return "Title"

    def get_input_folder_name(self):
        return "script_review"

    def get_output_folder_name(self):
        return "script_summarized"

    def get_file_extension(self):
        return ".json"
    


    def get_summary(self, article: str):
        json_format = """
        ```json
        {
            "title":"空坟墓",
            "theme": "耶稣的空坟墓",
            "content": "通过分析历史文献和圣经记载，强调耶稣的空坟墓是复活的关键证据。指出犹太传说与福音书记载的一致性，以及罗马兵丁的证词矛盾，反驳了门徒偷尸体的说法，论证了复活的历史真实性。"
        }
        ```
        """

        ai_prompt = f"""请給下面基督教福音派教授的講道加標題,然後写一个简洁的摘要。
        1. 標題要简洁
        2. 摘要先点出主题，再加核心内容。简介不要超过 100 字。
        3. 使用繁體中文
        回答符合以下JSON格式:
        {json_format}
        牧师讲道内容：{article}
        """              
        provider = os.getenv("PROVIDER")

        summary =  call_llm(provider, ai_prompt)
        return summary
        

    
    def process(self, input_folder, item_name:str, output_folder:str, meta_file_name:str = 'sermon.json', is_append:bool = False):
        with open(meta_file_name, 'r') as fsc:
            metadata = json.load(fsc)
        sermon = next((item for item in metadata if item['item'] == item_name), None)
        if sermon.get('summary'):
            return True

        title = sermon['title'] if sermon else ''

        file_name = input_folder + '/' + item_name + '.json'
        if not os.path.exists(file_name):
            print(f"File {file_name} does not exist.")
            return False

        with open(file_name, 'r') as fsc:
            data = json.load(fsc)

        if  isinstance(data, dict):
            paragraphs = data['script']
        else:
            paragraphs =  data

        article = title + '\n\n' + '\n\n'.join( [ p['text'] for p in paragraphs ] )

        summary = self.get_summary(article)

        print(title, summary)

        sermon['summary'] = summary['content']
        sermon['theme'] = summary['theme']

        with open(meta_file_name, 'w') as fsc:
            json.dump(metadata, fsc, indent=4, ensure_ascii=False)

        return True


if __name__ == '__main__':
    import requests
    import time    
    base_folder = '/opt/homebrew/var/www/church/web/data'  
    meta_file_name = base_folder + '/config/' + 'sermon.json'
    processor = ProcessorSummarize()

    with open(meta_file_name, 'r') as fsc:
        metadata = json.load(fsc)
    url = "http://127.0.0.1:8000/sc_api/final_sermon/junyang168@gmail.com/" 

    for idx, sermon in enumerate( metadata):
        item_name = sermon['item']
        if sermon['status'] == 'in development':
            continue

        if sermon.get('summary'):
            print(f"summary for {item_name} already exists.")
            continue

        print(f"{idx}: {item_name}")

        response = requests.get(url + item_name)
        sermon_detail = response.json()

        paragraphs = sermon_detail['script']

        theme = sermon['theme'] if sermon['theme'] else sermon['title']

        article = theme + '\n\n' + '\n\n'.join( [ p['text'] for p in paragraphs ] )

        summary = processor.get_summary(article)

        sermon['summary'] = summary['content']        

        with open(meta_file_name, 'w') as fsc:
            json.dump(metadata, fsc, indent=4, ensure_ascii=False)

        time.sleep(10)  # pause for 10 seconds to avoid rate limit

