from processor import Processor
import openai
import pandas as pd


class ProcessorProcessScript(Processor):
    def get_name(self):
        return "process"

    def get_input_folder_name(self):
        return "script"

    def get_output_folder_name(self):
        return "script_processed"

    def get_file_extension(self):
        return ".txt"

    def is_whitespace_or_punctuation(self, char):
        return  char.isspace()  or  char in string.punctuation or char in ['，','。','、','；','：','「','」','『','』','（','）','《','》','？','！','“','”','‘','’','—','…','．','～','〈','〉','﹑','﹔','﹕','﹖','﹗','﹘','﹙','﹚','﹛','﹜','﹝','﹞','﹟','﹠','﹡','﹢','﹣','﹤','﹥','﹦','﹨','﹩','﹪','﹫','！','？','；','：','、','，','。','．','〈','〉','《','》','「','」','『','』','（','）','［','］','｛','｝','【','】','—','…','～','﹏','﹋','﹌','﹍','﹎','﹏','﹐','﹑','﹒','﹔','﹕','﹖','﹗','﹘','﹙','﹚','﹛','﹜','﹝','﹞','﹟','﹠','﹡','﹢','﹣','﹤','﹥','﹦','﹨','﹩','﹪','﹫','！','？','；','：','、','，','。','．','〈','〉','《','》','「','」','『','』','（','）','［','］','｛','｝','【','】','—','…','～','﹏','﹋','﹌','﹍','﹎','﹏','﹐','﹑','﹒','﹔','﹕','﹖','﹗','﹘','﹙','﹚','﹛','﹜','﹝','﹞','﹟','﹠','﹡','﹢','﹣','﹤',']']
    
    def clean_find(self, text, sub_string):
        if not sub_string:
            return len(text)
        cleaned_sub_string = [ch for ch in sub_string if not self.is_whitespace_or_punctuation(ch)]
        cleaned_sub_string = cleaned_sub_string[:10]
        j = len(cleaned_sub_string) - 1  
        for i in range(len(text)-1, -1, -1):
            ch1 = text[i]
            if self.is_whitespace_or_punctuation(ch1):
                continue
            if ch1 == cleaned_sub_string[j]:
                if j == 0:
                    return i
                j -= 1
            else:
                j = len(cleaned_sub_string) - 1
        return -1
    
    def process(self, input_folder, item_name:str, output_folder:str, file_name:str = None, is_append:bool = False):
        script_file_name = self.get_file_full_path_name(input_folder, item_name)
        script_processed_file_name = self.get_file_full_path_name(output_folder, item_name)

        with open(script_file_name, 'r') as file1:
            txt = file1.read()
        chunk_index = 0
        chunk_size = 2048
        file2 = open( script_processed_file_name, 'w')
        while chunk_index < len(txt):
            print(f'processing {script_file_name} {chunk_index}')
            chunk = txt[chunk_index: chunk_index + chunk_size]
            processed_chunk = self.process_text_chunk(chunk)  

            if chunk_index + chunk_size < len(txt):
                last_para_indx = processed_chunk.rfind('\n') 
                last_para = processed_chunk[last_para_indx+1:]
                in_chunk_indx = self.clean_find(chunk, last_para) 
                processed_chunk_cut = processed_chunk[:last_para_indx]
                chunk_index += in_chunk_indx
            else:
                chunk_index = len(txt)
                processed_chunk_cut = processed_chunk
            file2.write( processed_chunk_cut)
            file2.flush()
        file2.close()
    
    def process_text_chunk(self, chunk):
        response = openai.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": f"给下面基督教牧师的讲道加标点，分段落.其他不要改动\n\n{chunk}"}],
                temperature=0.5,
                max_tokens=4000,
                top_p=1.0,
                frequency_penalty=0.0,
                presence_penalty=0.0,
                stream=True
            )
        print('generating response ...')
        processed_chunk = ''
        for ch in response:
            delta_content = ch.choices[0].delta.content
            if delta_content:
                processed_chunk += delta_content
        return processed_chunk
