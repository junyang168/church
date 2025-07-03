from processor import Processor
import openai
import jsonlines
import difflib
from utils import is_whitespace_or_punctuation, simplified_to_traditional
import os
import json
import math
#from together import Together
#from groq import Groq
import os
from openai import OpenAI
import re
from llm import call_llm
from utils import strip_white_space_or_punctuation

class ProcessorCorrectTranscription(Processor):
    def get_name(self):
        return "Correct"

    def get_input_folder_name(self):
        return "script"

    def get_output_folder_name(self):
        return "script_patched"

    def get_file_extension(self):
        return ".jsonl"
    


    def correct_paragraph(self, previous_text: str, current_text: str):

        json_format = """
        ```json
        [
            "[1]聖經強調：[2]你信主要繼續地信，你維持信心到底，你就得救。",
            "[3]有很多人認為說，[4]約翰福音第十章二十六節"
        ]    
        ```
        """

        ai_prompt = f"""作为转录编辑，下面文字是根據基督教牧師講道的錄音轉錄的。請使用繁体中文分段落，加標點，改正轉錄錯誤，並保持前後文連貫性。注意
        - 僅返回修改後結果
        - 保留索引
        - 保留原意，不要改變講道的內容
        - 每個段落不要超過 1000 字
        - 回答符合下面JSON格式：
        {json_format}
        前文上下文：{previous_text} 
        待修改內容：{current_text}                
        """
        provider = os.getenv("PROVIDER")  
        res = call_llm(provider, ai_prompt)
        return res


    def remove_indexes(self, string:str):
        # Find all patterns matching [number]
        re1 = r'\[(\d+)(?:-(\d+))?\]'
        re2 = r'\[(\d_\d+)(?:-(\d_\d+))?\]'
        use_re2 = False 
        matches = re.findall(re1, string)
        if(len(matches) == 0):
            matches = re.findall(re2, string)
            use_re2 = True
        numbers = []
        for match in matches:
            start = int(match[0])
            numbers.append(start)
            if match[1]:  # If there's a range (e.g., 2-4)
                end = int(match[1])
                numbers.append(end)             
        # Remove all indexes
        if use_re2:
            result = re.sub(re2, '', string)    
        else:
            result = re.sub(re1, '', string)    
        return numbers, result


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
            if isinstance(srt_data['entries'][0]['index'], str):
                for i in range(len(srt_data['entries'])):
                    srt_data['entries'][i]['index'] = i + 1
                sorted_data = srt_data['entries']
                with open(srt_file_name, 'w') as fsc:
                    json.dump(srt_data, fsc, indent=4, ensure_ascii=False)
            else:
                sorted_data = sorted(srt_data['entries'], key=lambda x: x['index'])

            paragraphs = []
            if os.path.exists(output_file_name):
                with open(output_file_name, 'r', encoding='UTF-8') as f:
                    paragraphs = json.load(f)
                index = paragraphs[-1]['end_index'] 
                last_paragraph = paragraphs[-1]
                prev_para = '[{}]{}'.format(last_paragraph['index'],last_paragraph['text'])
            else:
                index = 0
                prev_para = ''

            para = ''
            para_limit = 40000
            prev_index = index
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
#                retries = 0
#                while retries >= 0:
                corrected_para = self.correct_paragraph(prev_para, para)
                formatted_para = self.format_paragraphs(corrected_para)
#                    diff = self.get_diff(formatted_para[:-1], sorted_data)
#                    if diff < 50:
#                        break
#                    print(f"Diff: {diff} Retry: {retries}")
#                    retries -= 1
                if len(formatted_para) > 1:
                    para_limit = 40000
                    prev_para = '\n\n'.join( [ p for p in corrected_para[-2:-1]] )
                    paragraphs.extend(formatted_para[:-1])
                    self.save(output_file_name, paragraphs)
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

    def get_diff(self, modifed_paragraphs: list, original_scripts:list):
        if len(modifed_paragraphs) == 1:
            return 0
        total_diff = 0
        for para in modifed_paragraphs:
            start_indx = para['index']
            end_indx = para['end_index']
            original = ''.join([ p['text'] for p in original_scripts[start_indx-1:end_indx] ])    
            modified = para['text']
            original = strip_white_space_or_punctuation(original)
            original = simplified_to_traditional(original)
            modified = strip_white_space_or_punctuation(modified)
            total_diff += self.calculate_change_percentage(original, modified)
        return total_diff / len(modifed_paragraphs)

    def calculate_change_percentage(self, original, modified):
        """
        Calculate the percentage of changes between two strings using difflib
        Returns a percentage where 0% means identical and 100% means completely different
        """
        if not original and not modified:
            return 0.0
        
        # If one string is empty, compare against length of non-empty string
        if not original or not modified:
            return 100.0
        
        # Use SequenceMatcher to compare the strings
        matcher = difflib.SequenceMatcher(None, original, modified)
        
        # Get similarity ratio (0.0 = completely different, 1.0 = identical)
        similarity_ratio = matcher.ratio()
        
        # Convert to percentage of difference
        difference_percentage = (1 - similarity_ratio) * 100
        return round(difference_percentage, 2)


if __name__ == '__main__':
    
    def change_timestamp_format(chunk, timestamp: str) -> str:
        # Convert "00:00:00.000" to "00:00:00"
        ts_secs =  timestamp.split(':')
        min_secs = int(ts_secs[1])  + (int(chunk)-1) * 20
        return f"{ts_secs[0]}:{min_secs:02}:{ts_secs[2]}"
    
    def convert_to_milliseconds(timestamp: str) -> int:
        # Convert "00:00:00,000" to milliseconds
        hours, minutes, seconds = timestamp.split(':')
        sec, ms = str(seconds).split(',') 
        return (int(hours) * 3600 + int(minutes) * 60 + int(sec)) * 1000 + int(ms)

    base_folder = '/Volumes/Jun SSD/data'  
    base2 = '/opt/homebrew/var/www/church/web/data'

    def convert_script_to_v2(item:str):
        processor = ProcessorCorrectTranscription()
        s1_file = base_folder + '/' + 'script/' + item +'.json'
        s2_file = base2 + '/' + 'script/' + item +'.json'
        with open(s1_file, 'r') as fsc:
            s1_data = json.load(fsc)
        with open(s2_file, 'r') as fsc:
            s2_data = json.load(fsc)
        
        for i in range(len(s1_data['entries'])):
            orig_index = s2_data['entries'][i]['index'] 
            chunk = orig_index.split('_')[0]
            s1_data['entries'][i]['start'] = change_timestamp_format(chunk, s2_data['entries'][i]['start'])
            s1_data['entries'][i]['end'] = change_timestamp_format(chunk, s2_data['entries'][i]['end'])
            s1_data['entries'][i]['start_ms'] = convert_to_milliseconds( s1_data['entries'][i]['start'])
            s1_data['entries'][i]['end_ms'] = convert_to_milliseconds( s1_data['entries'][i]['end'])
            s1_data['entries'][i]['index'] = i + 1

        with open(s1_file, 'w') as fsc:
            json.dump(s1_data, fsc, indent=4, ensure_ascii=False)
    
    def convert_v1_script():
        with open(base2 + '/config/sermon.json', 'r') as fsc:
            sermon_data = json.load(fsc)
        sermon_items = [s  for s in sermon_data if s['item'].startswith('2019-') and s['status'] == 'ready']
        for sermon_item in sermon_items:
            item = sermon_item['item']
        convert_script_to_v2(item)

 #   convert_v1_script()

if __name__ == '__main__':
    base_folder = '/Volumes/Jun SSD/data'  
    processor = ProcessorCorrectTranscription()
    '''
    with open(base2 + '/config/sermon.json', 'r') as fsc:
        sermon_data = json.load(fsc)
    sermon_items = [ s['item']  for s in sermon_data if s['item'].startswith('2019-') and s['status'] == 'ready']
    for sermon_item in sermon_items:
        processor.process(base_folder + '/' + 'script', sermon_item, base_folder + '/script_patched')
    pass
    '''
    processor.process(base_folder + '/' + 'script', '2021 NYSC 專題：馬太福音釋經（八）王守仁 教授 4之1', base_folder + '/script_patched')