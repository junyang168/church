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
import re
from llm import call_llm

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
            "[1]聖經強調：[2]你信主要繼續地信，你維持信心到底，你就得救。",
            "[3]有很多人認為說，[4]約翰福音第十章二十六節"
        ]    
        ```
        """

        ai_prompt = f"""作为转录编辑，下面文字是根據基督教牧師講道的錄音轉錄的。請使用繁体中文分段落，改正轉錄錯誤，並保持前後文連貫性。注意
        - 保留索引
        - 保留原意，不要改變講道的內容
        回答符合下面JSON格式：
        {json_format}
        前文上下文：{previous_text} 
        待修改內容：{current_text}                
        """

        res = call_llm('aliyun', ai_prompt)
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
    
    def create_corrected_paragraph(self, original_para:str, corrected_para:list, segments:list, ignore_last_para:bool = True):
        corrected_para = '\n'.join(corrected_para)   
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


    def remove_indexes(self, string:str):
        # Find all patterns matching [number]
        indexes = re.findall(r'\[\d+\]', string)
        indexes = [int(i[1:-1]) for i in indexes]        
        # Remove all indexes
        result = re.sub(r'\[\d+\]', '', string)    
        return indexes, result




    def format_paragraphs(self, paragraphs:list):
        formatted_paragraphs = [{'text':p } for p in paragraphs]
        for p in formatted_paragraphs:
            indexes, p['text'] = self.remove_indexes(p['text'])
            p['index'] = indexes[0]
            p['end_index'] = indexes[-1]
        return formatted_paragraphs
            

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
            prev_index = 0
            while index < len(sorted_data):
                line = sorted_data[index]
                para +=  f"[{line['index']}]{line['text']}" 
                if len(para) < para_limit:
                    index += 1
                    continue
                print('Processing index:{} Prev idx:{}'.format(index, prev_index))
                if prev_index == index:
                    pass
                prev_index = index
                corrected_para = self.correct_paragraph(prev_para, para)
                formatted_para = self.format_paragraphs(corrected_para)
                if len(formatted_para) > 1:
                    para_limit = 1000
                    prev_para = '\n\n'.join( [ p for p in corrected_para[-2:-1]] )
                    paragraphs.extend(formatted_para[:-1])
                    para = ''
                    index = formatted_para[-1]['index'] - 1
                else:
                    index += 1
                    para_limit += 100

            if para:
                corrected_para = self.correct_paragraph(prev_para, para)
                formatted_para = self.format_paragraphs(corrected_para)
                paragraphs.extend(formatted_para)


            self.save(output_file_name, paragraphs)
            return True



    def save(self, output_file_name, paragraphs):

        with open( output_file_name, 'w', encoding='UTF-8') as f:
            json.dump(paragraphs, f, indent=4, ensure_ascii=False)
        




if __name__ == '__main__':
    base_folder = '/Volumes/Jun SSD/data'  
    processor = ProcessorCorrectTranscription()
    processor.process(base_folder + '/' + 'script', 'S 200322 羅10 6-21 以色列人不信福音7', base_folder + '/script_patched')
    pass