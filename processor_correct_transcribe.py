from processor import Processor
import openai
import jsonlines
import difflib
from utils import is_whitespace_or_punctuation
import os
import json
import math
#from together import Together
#from groq import Groq
import os
from openai import OpenAI

class ProcessorCorrectTranscription(Processor):
    def get_name(self):
        return "Correct"

    def get_input_folder_name(self):
        return "script"

    def get_output_folder_name(self):
        return "script_patched"

    def get_file_extension(self):
        return ".jsonl"
    
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


    def correct_paragraph(self, previous_text: str, current_text: str):
        json_format = """
        ```json
        [
            {
                "start_index": 1
                "end_index": 3
                "content": "第一段"
            },
            {
                "start_index": 2
                "end_index": 4
                "content": "第二段"
            }
        ]    
        ```
        """

        ai_prompt = f"""作为转录编辑，下面文字是根據基督教牧師講道的錄音轉錄的。請分段落，改正轉錄錯誤，並保持前後文連貫性。注意
        - 保留索引
        - 保留原意，不要改變講道的內容
        - 段落儘量不要太短 
        回答符合下面JSON格式：
        {json_format}
        前文上下文：{previous_text} 
        待修改內容：{current_text}                
        """
#        client = Together()
#        model="deepseek-ai/DeepSeek-R1",
#        model = "qwen-qwq-32b"

        # Initialize the client with the API key from the environment variable
#        client = Groq(api_key=os.getenv("GROQ_API_KEY"))
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
#            max_tokens=10000,
#            temperature=0.6,
#            top_p=0.95,
#            top_k=50,
#            repetition_penalty=1,
#            stop=["<｜end▁of▁sentence｜>"],
#            stream=False

        )
        res = response.choices[0].message.content
        return self.markdown_to_json(res)
        
        
    
    def find_closest_segment(self, segments:list, prev_seg:int, next_idx:int ):
        min_d = 100000
        min_i = -1
        for i in range(prev_seg, len(segments)):
            d =  abs(segments[i]['position'] - next_idx )
            if d < min_d:
                min_d = d
                min_i = i
        return min_i
    
    def create_corrected_paragraph(self, original_para:str, corrected_para:str, segments:list, ignore_last_para:bool = True):
        corrected_para = corrected_para.replace('\n\n', '\n')
        if not ignore_last_para:
            corrected_para = corrected_para + '\n'

        diff = difflib.Differ().compare(original_para, corrected_para)
        org_idx = 0
        new_idx = 0
        current_seg = 0
        paragraphs = []
        new_para_idx = 0
        for ele in diff:
            if ele.startswith('-'):
                org_idx += len(ele[2:])
            elif ele.startswith('+'):  
                if(ele[2:] == '\n'):
                    seg = self.find_closest_segment(segments, current_seg, org_idx)
                    paragraphs.append( {
                        'index' : segments[seg]['index'],
                        'text' : corrected_para[new_para_idx:new_idx],
                        'line_no' : segments[seg]['line_no']
                        }
                    )
                    new_para_idx = new_idx + 1

                new_idx += len(ele[2:])
            else:
                org_idx += len(ele[2:])
                new_idx += len(ele[2:])
        return paragraphs

    def format_paragraph(self, paragraph:str, is_end:bool = False):
        paragraphs = paragraph.split('\n\n')
        index = 0
        if not is_end and len(paragraphs) > 1:
            p = paragraphs[-1]
            first_index1 = p.find('[')
            first_index2 = p.find(']', first_index1+1)
            index = int(p[first_index1+1:first_index2])            
            return paragraphs[:-1] , index
        else:
            return paragraphs, index

    
    def process(self, input_folder, item_name:str, output_folder:str, file_name:str = None, is_append:bool = False):
        srt_file_name = os.path.join(input_folder, item_name + '.json')
        output_file_name = os.path.join(output_folder, item_name + '.json')

        with open(srt_file_name, 'r') as fsc:
            srt_data = json.load(fsc)
        sorted_data = sorted(srt_data['entries'], key=lambda x: x['index'])
        segments = []
        curr_line = 0
        para = ''
        para_limit = 1000
        prev_para = ''
        paragraphs = []
        index = 0
        while index < len(sorted_data):
            line = sorted_data[index]
            para +=  f"[{line['index']}]{line['text']}" 
            if len(para) < para_limit:
                index += 1
                continue
            print('Processing index:', index)
            corrected_para = self.correct_paragraph(prev_para, para)
            prev_para = '\n\n'.join( [ f"{p['content']}" for p in corrected_para[-3:-1]] )
            paragraphs.extend(corrected_para[:-1])
            para = ''
            index = corrected_para[-1]['start_index'] - 1
        if para:
            corrected_para = self.correct_paragraph(prev_para, para)
            paragraphs.extend(corrected_para)


        self.save(output_file_name, paragraphs)
        return True


    def save(self, output_file_name, paragraphs):
        for entry in paragraphs:
            entry['index'] = entry.pop('start_index')
            entry['text'] = entry.pop('content')        

        with open( output_file_name, 'w', encoding='UTF-8') as f:
            json.dump(paragraphs, f, indent=4, ensure_ascii=False)
        

if __name__ == '__main__':
    base_folder = '/Volumes/Jun SSD/data'  
    processor = ProcessorCorrectTranscription()
    processor.process(base_folder + '/' + 'script', 'S 200405 羅11 1-10 揀選2', base_folder + '/script_corrected')
    pass