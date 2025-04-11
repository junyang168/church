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
        return "script_published"

    def get_output_folder_name(self):
        return "script_summarized"

    def get_file_extension(self):
        return ".json"
    


    def get_summary(self, article: str):
        json_format = """
        ```json
        {
            "theme": "耶稣的空坟墓",
            "content": "通过分析历史文献和圣经记载，强调耶稣的空坟墓是复活的关键证据。指出犹太传说与福音书记载的一致性，以及罗马兵丁的证词矛盾，反驳了门徒偷尸体的说法，论证了复活的历史真实性。"
        }
        ```
        """

        ai_prompt = f"""请为以下牧师讲道写一个简洁的摘要。摘要先点出主题，再加核心内容。简介不要超过 100 字。回答符合以下JSON格式:
        {json_format}
        牧师讲道内容：{article}
        """              

        summary =  call_llm('deepseek', ai_prompt, model='deepseek-chat')
        return summary
        

    
    def process(self, input_folder, item_name:str, output_folder:str, meta_file_name:str = 'sermon.json', is_append:bool = False):
        with open(meta_file_name, 'r') as fsc:
            metadata = json.load(fsc)
        sermon = next((item for item in metadata if item['item'] == item_name), None)
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
    base_folder = '/opt/homebrew/var/www/church/web/data'  
    meta_file_name = base_folder + '/config/' + 'sermon.json'
    item_name = '191013'
    processor = ProcessorSummarize()
    processor.process(
        base_folder + '/' + processor.get_input_folder_name(), 
        item_name,
        base_folder + '/' + processor.get_output_folder_name(), 
        meta_file_name = base_folder + '/config/' + 'sermon.json')


    listdir = os.listdir(base_folder + '/' + processor.get_input_folder_name())
    with open(meta_file_name, 'r') as fsc:
        metadata = json.load(fsc)
    for file in listdir:
        item_name = file.split('.')[0]
        with open(base_folder + '/' + processor.get_input_folder_name() + '/' + file, 'r') as fsc:
            surmon = json.load(fsc)
        sermon_meta = next((item for item in metadata if item['item'] == item_name), None)
        with open(base_folder + '/' + processor.get_output_folder_name() + '/' + item_name + '.json', 'r') as fsc:
            summary = json.load(fsc)
        sermon_meta['theme'] = summary['theme']
        sermon_meta['summary'] = summary['content']
        if not isinstance(surmon, dict):
            surmon = { 'script': surmon, 'metadata': sermon_meta}
        else:
            surmon['metadata'] = sermon_meta
        with open(base_folder + '/' + processor.get_input_folder_name() + '/' + file, 'w') as fsc:
            json.dump(surmon, fsc, indent=4, ensure_ascii=False)
    with open(meta_file_name, 'w') as fsc:
        json.dump(metadata, fsc, indent=4, ensure_ascii=False)
    exit()
    for file in listdir:
        item_name = file.split('.')[0]
        processor.process(
            base_folder + '/' + processor.get_input_folder_name(), 
            item_name,
            base_folder + '/' + processor.get_output_folder_name(), 
            meta_file_name = base_folder + '/config/' + 'sermon.json')
