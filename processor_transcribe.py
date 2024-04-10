from processor import Processor
import re
import jsonlines

class ProcessorTranscribe(Processor):
    def get_name(self):
        return "transcribe"

    def get_priority(self):
        return 1

    def get_input_folder_name(self):
        return "audio"

    def get_output_folder_name(self):
        return "script"

    def get_file_extension(self):
        return ".mp3"

    def get_index_id(self, file_name, index):
        return  file_name.split('.')[0].split('_')[1] + '_' + str(index)

    def process(self, input_folder, item_name:str, output_folder:str, file_name:str = None, is_append:bool = False):
        mp3_file_name =  input_folder + '/' + file_name
        script_file_name = output_folder + '/' + item_name + '.txt'
        timestamp_file_name = output_folder + '/' + item_name + '.jsonl'

        from openai import OpenAI
        client = OpenAI()

        with open(mp3_file_name, "rb") as audio_file:
#            transcription = self.srt_content

            transcription = client.audio.transcriptions.create(
                model="whisper-1", 
                file=audio_file,
                response_format='srt'
            )

            data = self.parse_srt(file_name, transcription)
            text = ' '.join([f"{d['text']}[{ d['index']}]" for d in data])

            with open(script_file_name, 'a' if is_append else 'w') as file1:
                file1.write(text)

            with jsonlines.open(timestamp_file_name, mode='a' if is_append else 'w') as writer:
                for d in data:
                    writer.write(d)




    def parse_srt(self, file_name, file_content):
        # Split the content by double newlines
        segmentgs = file_content.strip().split('\n\n')

        data = []
        for segment in segmentgs:
            # Split the section into lines
            lines = segment.split('\n')

            # The first line is the index
            index = int(lines[0])

            # The second line is the time range
            time_range = lines[1]
            start_time, end_time = time_range.split(' --> ')

            # The remaining lines are the text
            text = ' '.join(lines[2:])

            # Add the data to the list
            data.append({
                'index': self.get_index_id(file_name, index),
                'start_time': start_time,
                'end_time': end_time,
                'text': text,
            })

        return data



if __name__ == "__main__":
    import os
    import jsonlines
    from utils import get_files, find_last_index_of_whitespace_or_punctuation, clean_string
    import utils

    base_folder = '/Users/junyang/church/data'
    script_folder = os.path.join(base_folder, 'script')

    files = get_files(script_folder, '.jsonl')

    for file_name in files:
        item_name = file_name.split('.')[0]
        if item_name != '2019-3-24 罗马书3章21至31节':
            continue

        script_path = os.path.join(base_folder,'script_processed', item_name + '.txt')
        with open(script_path) as file_script:
            script = file_script.read()
            paragraphs = [ {'text': p } for p in  script.split('\n\n') ]

        file_path = os.path.join(script_folder, file_name)        
        with jsonlines.open(file_path) as reader:
            script_ts = [ line for line in reader]
        i = 0
        j = 0 
        for i in range( len(paragraphs) ):
            p = paragraphs[i]['text']
            idx = find_last_index_of_whitespace_or_punctuation(p)
            sub = clean_string(p[idx+1:])[-5:]   
#            sub = utils.convert_to_traditional_chinese(sub)
            while j < len(script_ts):
                ts = script_ts[j]
#                ts['text'] = utils.convert_to_traditional_chinese(ts['text'])
                j += 1
                if  ( script_ts[j-2]['text'] +  ts['text'] ).rfind(sub) >= 0 :
                    paragraphs[i]['timeline_index'] = ts['index']
                    break
            if j == len(script_ts) :
                pass



        
        script_processed_path = os.path.join(base_folder,'script_processed', item_name + '.txt1')
        with open(script_processed_path,'w') as fp:
            for para in paragraphs:
                fp.write(para['text'])
                fp.write(f" [{para['timeline_index']}]" if 'timeline_index' in para else '')
                fp.write('\n\n')
                



