from processor import Processor
import openai
import os
import json
#from together import Together
#from groq import Groq
import os
from openai import OpenAI
from metadata import update_metadata_item_title


class ProcessorAddTitle(Processor):
    def get_name(self):
        return "Title"

    def get_input_folder_name(self):
        return "script_patched"

    def get_output_folder_name(self):
        return "config"

    def get_file_extension(self):
        return ".json"
    
    def markdown_to_json(self, markdown: str, is_json: bool = False) -> dict:
        """Convert markdown-formatted JSON string to Python dictionary.
        
        Args:
            markdown: String containing JSON wrapped in markdown code block
            
        Returns:
            Parsed dictionary from JSON content
        """
        if is_json:
            return json.loads(markdown)
        
        json_tag = "```json"
        start_idx = markdown.find(json_tag)
        if start_idx < 0:
            raise ValueError("No JSON content found in markdown")
        end_idx = markdown.find("```", start_idx + len(json_tag))
        if end_idx == -1:
            raise ValueError("No closing code block found in markdown")
        json_str = markdown[start_idx + len(json_tag):end_idx].strip()
        return json.loads(json_str)


    def add_title(self, article: str):
        ai_prompt = f"""給下面基督教牧師的講道加標題,標題要剪短。回答JSON格式:
        {article}  
        """              
        model="deepseek-r1"

        client = OpenAI(
            api_key=os.getenv("DASHSCOPE_API_KEY"),  # 如何获取API Key：https://help.aliyun.com/zh/model-studio/developer-reference/get-api-key
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
        )


        response = client.chat.completions.create(
            model=model,
            messages=[        
                {
                    "role": "user",
                    "content": ai_prompt
                }
            ],

        )
        res = response.choices[0].message.content
        title = self.markdown_to_json(res)
        title_key = next(iter(title))
        return title[title_key]
        

    
    def process(self, input_folder, item_name:str, output_folder:str, meta_file_name:str = None, is_append:bool = False):
        file_name = os.path.join(input_folder, item_name + '.json')

        with open(file_name, 'r') as fsc:
            paragraphs = json.load(fsc)

        article = '\n\n'.join( [ p['text'] for p in paragraphs ] )

        title = self.add_title(article)
        update_metadata_item_title( output_folder + '/' + meta_file_name, item_name, title)


        return True


if __name__ == '__main__':
    base_folder = '/Volumes/Jun SSD/data'  
    processor = ProcessorAddTitle()
    processor.process(base_folder + '/' + processor.get_input_folder_name(), 'S 190512-GH010035', base_folder + '/' + processor.get_output_folder_name(), 'sermon.json')
    pass