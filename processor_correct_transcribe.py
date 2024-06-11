from processor import Processor
import openai
import jsonlines
import difflib
from utils import is_whitespace_or_punctuation
import os
import json
import math

class ProcessorCorrectTranscription(Processor):
    def get_name(self):
        return "Correct"

    def get_input_folder_name(self):
        return "script"

    def get_output_folder_name(self):
        return "script_corrected"

    def get_file_extension(self):
        return ".jsonl"
    


    def correct_paragraph(self, para:str):

        system_prompt = "下面文字是根據基督教牧師講道的錄音轉錄的。请分段落，改正错别字。回答使用中文繁體。儘返回改正結果"

        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": system_prompt
                },                
                {"role": "user", 
                 "content": para
                }],
            max_tokens=1500
        )
        res = response.choices[0].message.content
        print(res)
        return res
    
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


    def process(self, input_folder, item_name:str, output_folder:str, file_name:str = None, is_append:bool = False):
        script_file_name = self.get_file_full_path_name(input_folder, item_name)
        output_file_name = os.path.join(output_folder, item_name + '.json')

        if  os.path.exists(output_file_name):
            with open(output_file_name,'r') as f:
                paragraphs = json.load(f)
        else:
            paragraphs = []
        with jsonlines.open(script_file_name) as reader:
            lines = [ line for line in reader ]
        
        segments = []
        if paragraphs:
            curr_line = next( ( curr_line for curr_line, line in enumerate(lines) if line['index'] == paragraphs[-1]['index'] ),-1) + 1
        else:
            curr_line = 0
        para = ''
        while curr_line < len(lines):
            line = lines[curr_line]
            para +=  line['text']
            line['position'] = len(para)
            line['line_no'] = curr_line
            segments.append( line )
            curr_line += 1
            if len(para) < 500:
                continue
            corrected_para = self.correct_paragraph(para)
            paragraphs.extend(self.create_corrected_paragraph(para, corrected_para, segments, ignore_last_para = True))
            curr_line = paragraphs[-1]['line_no'] + 1
            para = ''
            segments = []

            self.save(output_file_name, paragraphs)


        corrected_para = self.correct_paragraph(para)
        paragraphs.extend(self.create_corrected_paragraph(para, corrected_para, segments, ignore_last_para=False))
        self.save(output_file_name, paragraphs)


    def save(self, output_file_name, paragraphs):
        for p in paragraphs:
            if 'line_no' in p:
                p.pop('line_no')
        with open( output_file_name, 'w', encoding='UTF-8') as f:
            json.dump(paragraphs, f, indent=4, ensure_ascii=False)
        

if __name__ == '__main__':
    base_folder = '/Users/junyang/church/data'  
    processor = ProcessorCorrectTranscription()
    processor.process(base_folder + '/' + 'script', '2019-07-28 罗马书六章1节', base_folder + '/script_corrected')
    pass