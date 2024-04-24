from processor  import Processor
import openai
import re
import tqdm
import os
import jsonlines
from pydantic import BaseModel
from typing import List, Optional, Union
import json
import utils
import difflib

class Paragraph(BaseModel):
    index: Optional[str]
    text :str

class ProcessorPatch(Processor):
    def get_name(self):
        return "patch"

    def get_input_folder_name(self):
        return "script_fixed"

    def get_output_folder_name(self):
        return "script_patched"

    def get_file_extension(self):
        return ".txt"
    
    def load_timeline_file(self, file_path:str):
        segments = {}
        with jsonlines.open(file_path, 'r') as f:
            self.timeline_segments = list(  f.iter() )
            for i in range(len(self.timeline_segments)):
                s = self.timeline_segments[i]
                s['next_segment'] = self.timeline_segments[i+1] if i+1 < len(self.timeline_segments) else None
                s['prev_segment'] = self.timeline_segments[i-1] if i > 0 else None
            self.timeline_index = { s['index']:s for s in self.timeline_segments}
    

    def closest_match(self, long_string, short_string):
        best_ratio = 0
        best_pos = 0
        match_length = len(short_string)

        for i in range(len(long_string) - match_length + 1):
            sub_long = long_string[i:i + match_length]
            matcher = difflib.SequenceMatcher(None, sub_long, short_string)
            ratio = matcher.ratio()  # Calculate similarity as a float
            if ratio > best_ratio:
                best_ratio = ratio
                best_pos = i

        return best_pos, best_ratio


    def build_long_string(self, timeline_start, timeline_end):
        segments = []
        timeline = timeline_start
        length = 0
        positions = []
        while timeline != timeline_end:
            s = utils.convert_to_traditional_chinese(timeline['text'])
            segments.append(s)
            positions.append((length, timeline))
            timeline = timeline['next_segment']
            length += (len(s) + 1)
        positions.append((length, timeline))

        return ' '.join( segments ), positions

    def get_timeline_from_positions(self, positions, pos):
        for i in range(len(positions) -  1):
            if pos >= positions[i][0] and pos < positions[i+1][0]:
                return positions[i][1]
        return positions[-1][1]


    def compare_sentense(self, s1, s2):
        s1 = utils.strip_white_space_or_punctuation(s1)
        s1 = utils.convert_to_traditional_chinese(s1)
        s2 = utils.strip_white_space_or_punctuation(s2)
        s2 = utils.convert_to_traditional_chinese( s2 )
        if s1 == s2:
            return True
        elif s1.endswith(s2) or s2.endswith(s1):
            return True
        else:
            s1_py = utils.convert_to_pinyin(s1)
            s2_py = utils.convert_to_pinyin(s2)
            if s1_py.endswith(s2_py) or s2_py.endswith(s1_py):
                return True
            print(s1)
            print(s2)
            user_input = input("are the above two string similar:[Y/N]")
            return user_input.upper() == "Y"


    def get_timeline(self, paragraphs, i:int):
        if i < 0:
            return  self.timeline_segments[0]
        if i >= len(paragraphs):
            return self.timeline_segments[-1]
        else:
            index =  paragraphs[i].index
            return self.timeline_index.get(index)
    


    
    def process(self, input_folder, item_name:str, output_folder:str, file_name:str = None, is_append:bool = False):
        fixed_file_name = self.get_file_full_path_name(input_folder, item_name)
        base_folder = input_folder + '/..'
        timeline_file_name = base_folder + '/script/' +  item_name + '.jsonl'
        

        patch_file_name = output_folder + '/' + item_name +  '.json'

        with open(fixed_file_name, 'r') as file1:            
            txt = file1.read()
        paragraphs_raw = txt.split('\n\n')

        self.load_timeline_file(timeline_file_name)

        paragraphs : List[Paragraph] = []        

        for i in range(len(paragraphs_raw)) :
            paragraph = paragraphs_raw[i]
            if( not paragraph):
                continue

            index_right = paragraph.rfind(']')
            if index_right == -1:
                para =  Paragraph(index= None, text = paragraph)
            else:
                index_left = paragraph.rfind('[', 0, index_right)
                para = Paragraph(index= paragraph[index_left+1:index_right], 
                        text = paragraph[:index_left] + paragraph[index_right+1:])                 
            para.text = re.sub(r'\[[\d_]+\]', '', para.text)
            paragraphs.append(para)

        for i in range(len(paragraphs)):
            paragraph = paragraphs[i]
            timeline = self.timeline_index.get(paragraph.index, None)
            if timeline:
                i1, i2 = utils.find_last_index_of_whitespace_or_punctuation(paragraph.text)
                last_sentense = paragraph.text[i1:i2+1]
                print(paragraph.index)
                if self.compare_sentense(last_sentense, timeline.get('text')):
                    continue
            paragraph.index = self.find_paragraph_index(paragraphs, i, paragraph)


        with open(patch_file_name, 'w') as file2:
            paragraph_dicts = [p.dict() for p in paragraphs]
            json.dump(paragraph_dicts, file2)    
                



    def find_paragraph_index(self, paragraphs, i, paragraph):
        timline_start = self.get_timeline(paragraphs, i-1)
        timline_start = timline_start['next_segment']   
        i_end = i + 1     
        timline_end = self.get_timeline(paragraphs, i+1)
        while not timline_end and i_end < len(paragraphs):
            i_end += 1
            timline_end = self.get_timeline(paragraphs, i_end)

        long_string, positions = self.build_long_string(timline_start, timline_end)

        i1, i2 = utils.find_last_index_of_whitespace_or_punctuation(paragraph.text)
        last_sentense = paragraph.text[i1:i2+1]

        i1, i2 = utils.find_first_index_of_whitespace_or_punctuation(paragraphs[i+1].text)
        first_sentense_next_para = paragraphs[i+1].text[i1:i2+1]

        last_sentense = utils.convert_to_traditional_chinese(last_sentense)
        first_sentense_next_para = utils.convert_to_traditional_chinese(first_sentense_next_para)

        pos, ratio =  self.closest_match(long_string, last_sentense + ' ' + first_sentense_next_para)
        if ratio > 0.8:
            tl = self.get_timeline_from_positions(positions, pos + len(last_sentense) - 1)
            return tl['index']
        else:
            pos, ratio =  self.closest_match(long_string, first_sentense_next_para)
            if ratio > 0.8:
                s = long_string[ pos - len(last_sentense) - 5 if pos >= len(last_sentense) + 5 else 0 :pos]
                pos2, ratio =  self.closest_match( s , last_sentense)
                if ratio > 0.5:
                    tl = self.get_timeline_from_positions(positions, pos -2)
                    return tl['index']
                



        


    def process2(self, input_folder, item_name:str, output_folder:str, file_name:str = None, is_append:bool = False):
        fixed_file_name = self.get_file_full_path_name(input_folder, item_name)
        base_folder = input_folder + '/..'
        script_file_name = self.get_file_full_path_name(base_folder + '/script', item_name)

        patch_file_name = self.get_file_full_path_name(output_folder, item_name)
        with open(fixed_file_name, 'r') as file1:            
            txt = file1.read()
        paragraphs = txt.split('\n\n')

        with open(script_file_name, 'r') as file1:            
            script = file1.read()


        change = False
        for i in reversed( range(len(paragraphs)) ):
            paragraph = paragraphs[i]
            if( not paragraph):
                paragraphs.pop(i)
                continue

            if(paragraph[-1] == ']'):
                continue

            index_right = paragraph.rfind(']')
            if index_right == -1:
                continue
            change = True
            index_left = paragraph.rfind('[', 0, index_right)
            new_paragraph = paragraph[:index_left] + paragraph[index_right+1:] + paragraph[index_left:index_right+1]
            paragraphs[i] = new_paragraph
        if change:
            with open(patch_file_name, 'w') as file2:
                file2.write('\n\n'.join(paragraphs))

if __name__ == '__main__':
    processor = ProcessorPatch()
    base_folder = '/Users/junyang/Church/data'
#    processor.process( base_folder + '/script_fixed', '2019-2-15 心mp4', base_folder +  '/script_patched')
  
