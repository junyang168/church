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


class ProcessorGetBibleVerse(Processor):
    def get_name(self):
        return "Title"

    def get_input_folder_name(self):
        return "script_published"

    def get_output_folder_name(self):
        return "script_summarized"

    def get_file_extension(self):
        return ".json"
    


    def get_bible_verses(self, article: str):
        json_format = """
        ```json
        {
            "theme":"耶稣的空坟墓",
            "key_bible_verse": [
            { 
                "book": "罗马书",
                "chapter_verse": "1:1-3",
                "content": "耶稣基督是大卫的后裔，按肉体说是大卫的后裔，按圣灵说是神的儿子。"
            }
            ]
        }
        ```
        """

        ai_prompt = f"""你是一位资深的基督教神学牧师。用一句话总结以下牧师讲道的中心思想(theme)，然后找出讲道的中心思想是围绕圣经中哪些章节(key_bible_verse)展开的。只返回最重要的三个章节。回答符合以下JSON格式:
        {json_format}
        牧师讲道内容：{article}
        """              

        bible =  call_llm('deepseek', ai_prompt, model='deepseek-chat')
        return bible
        

    
    def process(self, input_folder, item_name:str, output_folder:str, meta_file_name:str = 'sermon.json', is_append:bool = False):
        with open(meta_file_name, 'r') as fsc:
            metadata = json.load(fsc)
        sermon = next((item for item in metadata if item['item'] == item_name), None)
        if sermon.get('core_bible_verse'):
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

        bible_verse = self.get_bible_verses(article)

        print(title, bible_verse)

        sermon['theme'] = bible_verse['theme']

        sermon['core_bible_verse'] = bible_verse['key_bible_verse']

        with open(meta_file_name, 'w') as fsc:
            json.dump(metadata, fsc, indent=4, ensure_ascii=False)

        return True


if __name__ == '__main__':
    base_folder = '/opt/homebrew/var/www/church/web/data'  
    meta_file_name = base_folder + '/config/' + 'sermon.json'
    processor = ProcessorGetBibleVerse()
    with open(meta_file_name, 'r') as fsc:
        metadata = json.load(fsc)


#    metadata = [sermon for sermon in metadata if sermon['item'] == 'S 200712']
    
    for sermon in metadata:
        item_name = sermon['item']
        if sermon['status'] == 'in development':
            continue
        elif sermon['status'] == 'published':
            input_folder = base_folder + '/script_published'
        else:
            input_folder = base_folder + '/script_review'
        processor.process(
            input_folder, 
            item_name,
            base_folder + '/' + processor.get_output_folder_name(), 
            meta_file_name = base_folder + '/config/' + 'sermon.json')
