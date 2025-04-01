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


class ProcessorAddTitle(Processor):
    def get_name(self):
        return "Title"

    def get_input_folder_name(self):
        return "script_patched"

    def get_output_folder_name(self):
        return "config"

    def get_file_extension(self):
        return ".json"
    


    def get_title(self, article: str):
        ai_prompt = f"""給下面基督教牧師的講道加標題,標題要简洁。標題使用繁體中文。
        回答JSON格式:
        {article}  
        """              

        title =  call_llm('deepseek', ai_prompt)
        title_key = next(iter(title))
        return title[title_key]
        

    
    def process(self, input_folder, item_name:str, output_folder:str, meta_file_name:str = 'sermon.json', is_append:bool = False):
        if re.match(r'^S \d{6}.+$', item_name):
            title = item_name[8:].strip()
        else:
            file_name = os.path.join(input_folder, item_name + '.json')
            with open(file_name, 'r') as fsc:
                paragraphs = json.load(fsc)
            article = '\n\n'.join( [ p['text'] for p in paragraphs ] )
            title = self.get_title(article)

        update_metadata_item_title( output_folder + '/' + meta_file_name, item_name, title)


        return True


if __name__ == '__main__':
    base_folder = '/Volumes/Jun SSD/data'  
    processor = ProcessorAddTitle()
    processor.process(base_folder + '/' + processor.get_input_folder_name(), 'S 200503', base_folder + '/' + processor.get_output_folder_name(), 'sermon.json')
    pass