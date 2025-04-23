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


class ProcessorGetKeypoints(Processor):
    def get_name(self):
        return "Keypoints"

    def get_input_folder_name(self):
        return "script_published"

    def get_output_folder_name(self):
        return "script_keypoints"

    def get_file_extension(self):
        return ".json"
    


    def get_keypoints(self, article: str):

        ai_prompt = f"""总结下面牧师讲道的主要观点.回答以下格式例子：
        主题
        1. 观点 1
        2. 观点 2
        牧师讲道内容：{article}
        """              

        kp =  call_llm('deepseek', ai_prompt, model='deepseek-chat')
        return kp
        

    
    def process(self, input_folder, item_name:str, output_folder:str, meta_file_name:str = 'sermon.json', is_append:bool = False):
        with open(meta_file_name, 'r') as fsc:
            metadata = json.load(fsc)
        sermon = next((item for item in metadata if item['item'] == item_name), None)
        title = sermon['title'] if sermon else ''

        with open( output_folder+ '/' + 'keypoints.json' , 'r') as fsc:
            keypoints = json.load(fsc)
        item = next((item for item in keypoints if item['id'] == item_name), None)
        if item and item.get('published_date','') == sermon['published_date']:
            return True
        if item:
            keypoints.remove(item)


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

        kps = self.get_keypoints(article)

        kps =  { 'id': item_name, 'title': title, 'content': kps, 'published_updated': sermon['published_date'] }

        keypoints.append(kps)
        with open( output_folder+ '/' + 'keypoints.json' , 'w') as fsc:
            json.dump(keypoints, fsc, indent=4, ensure_ascii=False)
        return True


if __name__ == '__main__':
    base_folder = '/opt/homebrew/var/www/church/web/data'  
    meta_file_name = base_folder + '/config/' + 'sermon.json'
    processor = ProcessorGetKeypoints()
    listdir = os.listdir(base_folder + '/' + processor.get_input_folder_name())
    with open(meta_file_name, 'r') as fsc:
        metadata = json.load(fsc)
    '''
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
    exit()'
    
    kps = processor.process(
        base_folder + '/' + 'script_review', 
        'S 200322 羅10 6-21 以色列人不信福音7',
        base_folder + '/' + processor.get_output_folder_name(), 
        meta_file_name = base_folder + '/config/' + 'sermon.json')
    '''

    for file in listdir:
        item_name = file.split('.')[0]
        print(item_name)
        kps = processor.process(
            base_folder + '/' + processor.get_input_folder_name(), 
            item_name,
            base_folder + '/' + processor.get_output_folder_name(), 
            meta_file_name = base_folder + '/config/' + 'sermon.json')

