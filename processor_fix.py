from processor  import Processor
import openai
import re
import tqdm
import os

class ProcessorFix(Processor):
    def get_name(self):
        return "fix"

    def get_input_folder_name(self):
        return "script_processed"

    def get_output_folder_name(self):
        return "script_fixed"

    def get_file_extension(self):
        return ".txt"

    def cleanup_index(self, txt):
        paras :list[str] = txt.split('\n\n')
        paragraphs = []
        for p in paras:
            paragraphs.extend(p.split('\n'))
        clean_paragraphs = []
        for p in paragraphs:
            last_index_left = p.rfind('[')
            last_index_right = p.rfind(']')
            last_index = p[last_index_left:last_index_right+1]
            clean_paragraphs.append( {'text': re.sub(r'\[[\d_]+\]', '', p),'last_index': last_index} ) 
        return clean_paragraphs
            
    def no_change(self, para_txt):
        verbs = ['沒有提及任何需要更正的聖經','无需进行更改','没有需要更正的圣经','如果有其他需要幫助','没有内容需要更正','請提供相關信息','请提供详细信息','无需更正的内容','没有可改正的圣经','没有具体的圣经章节引用','您提供的文本内容并未包含任何圣经章节' ,'没有提到任何圣经经文' , '如果有其他关于圣经的问题或需要帮助' ,'沒有包含任何需要更正的聖經' ,'没有提到具体的圣经经文章' ,'我將很樂意幫助您進行更正' , '没有提到圣经经文章节名称' ,'没有可改正的圣经' ,'我将很乐意帮助您进行更正' ,'我將很樂意為您更正' ,'我將很樂意幫助您進行修正']
        matches = [ v for v in verbs if v in para_txt ]
        return len(matches) > 0

    def process(self, input_folder, item_name:str, output_folder:str, file_name:str = None, is_append:bool = False):
        script_file_name = self.get_file_full_path_name(input_folder, item_name)
        fixed_file_name = self.get_file_full_path_name(output_folder, item_name)
    

        with open(script_file_name, 'r') as file1:
            txt = file1.read()

        paragraphs = self.cleanup_index(txt)

        if os.path.exists(fixed_file_name):
            with open(fixed_file_name, 'r') as file2:
                fixed_text = file2.read()
                i_left = fixed_text.rfind('[') 
                i_right = fixed_text.rfind(']')
                last_idx = fixed_text[i_left: i_right+1]
                for i in range(len(paragraphs)):
                    if  paragraphs[i]['last_index'] == last_idx:
                        paragraphs = paragraphs[i+1:]
                        break

        with  open(fixed_file_name, 'a') as file2:
            for i in tqdm.tqdm(range(len(paragraphs))):
                para = paragraphs[i]['text']

                if not para:
                    continue


                prompt = f"""
        你是圣经专家，请改正下面基督教牧师的讲道中提到的圣经经文章节名称，和圣经中人物名字。除此之外，不要做任何改动. 如无需改动，请回答“没有可改正的圣经”。
        例如：天上羅尼迦前世五章二十三節改为帖撒罗尼迦5章23节，耶華改为耶和华。
        请使用中文繁体回答，格式为Markdown

        {para}
            """

                response = openai.chat.completions.create(
                    model="gpt-4-turbo",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.5,
                    max_tokens=1000,
                    top_p=1.0,
                    frequency_penalty=0.0,
                    presence_penalty=0.0
                )

                msg = response.choices[0].message.content
                if msg.startswith('```'):
                    msg = msg[3:-3].replace('markdown','').replace('\n','')
                if self.no_change(msg): 
                    msg = para 
                file2.write( msg + paragraphs[i]['last_index'] + '\n\n')
                file2.flush()

if __name__ == '__main__':
    from utils import get_files
    base_folder = '/Users/junyang/church/data'
    files = get_files(base_folder + '/script_fixed', '.txt')
    for file in files:
        processor = ProcessorFix()
        with open(file, 'r') as file1:
            txt_fixed = file1.read()
        fixed_paragraphs = processor.cleanup_index(txt_fixed)

        item_name = file.split('/')[-1].split('.')[0]

        with open(base_folder + '/script_processed/' + item_name + '.txt', 'r') as file2:
            txt = file2.read()        
        paragraphs = processor.cleanup_index(txt)

        hasFix = False

        for i in range(len(fixed_paragraphs)):
            para_text = fixed_paragraphs[i]['text']
            if processor.no_change(para_text):
                hasFix = True
                if fixed_paragraphs[i]['last_index'] == paragraphs[i]['last_index']:
                    fixed_paragraphs[i]['text'] = paragraphs[i]['text']
                else:
                    print(fixed_paragraphs[i]['last_index'], paragraphs[i]['last_index'])
                    pass

        if hasFix:
            with open(file, 'w') as file1:
                for p in fixed_paragraphs:
                    if not p['text'] :
                        continue
                    file1.write(p['text'] + p['last_index'] + '\n\n')
                    file1.flush()




