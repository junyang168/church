import pandas as pd
from utils import get_files
from processor import Processor
from utils import get_files


from processor_transcribe import ProcessorTranscribe
from processor_extract_audio import ProcessorExtractAudio
from processor_fix import ProcessorFix
from processor_process_script import ProcessorProcessScript
from processor_convert_video import ProcessorConvertVideo
#from processor_pull_slide import ProcessorPullSlide
#from screen_detection import DectectBluescreen
from patch import ProcessorPatch
from processor_audio import ProcessorAudio
from processor_correct_transcribe import ProcessorCorrectTranscription
from processor_add_title import ProcessorAddTitle
import json
import datetime

class ProcessingPipeline:
    def __init__(self, base_folder:str, input_folder:str):
        self.processors = [
#                            ProcessorAudio(), 
#                            ProcessorConvertVideo(),
                            ProcessorExtractAudio(),                            
                            ProcessorTranscribe(),
                            ProcessorCorrectTranscription(),
                            ProcessorAddTitle()
                        ]
        self.base_folder = base_folder
        self.input_folder = input_folder
        self.control_file = base_folder + '/Processing_stage.xlsx'
    
    def get_item_name(self, fname: str):
        fname = fname.replace('/', '-')
        if '_' not in fname:
            return fname.split('.')[0].strip()
        else:
            return fname.split('_')[0].strip()
    
    def get_cell_value(self, dataframe, row_name, column_name):
        try:
            return dataframe.loc[row_name, column_name]
        except KeyError:
            return pd.NA
    
    def get_file_index(self, fname:str):
        if '_' not in fname:
            return 1
        else:
            return int(fname.split('_')[1].split('.')[0])
        
    def get_item_last_index(self, files:list, item_name:str):
        files_for_item = [f for f in files if item_name in f]
        return self.get_file_index(files_for_item[-1])
    
    def process(self):

        df = pd.read_excel(self.control_file, index_col=0)    

        with open(self.base_folder + '/config/sermon.json') as master_file:
            sermon_data = json.load(master_file)
        
        for p in self.processors:
            input_folder = self.input_folder if p.get_input_folder_name()[0] == '/' else self.base_folder + '/' + p.get_input_folder_name()
            for sermon in sermon_data:
                item_name = sermon['item'] 
                if p.accept_media_type() and sermon['type'] != p.accept_media_type():
                    continue
                status = self.get_cell_value(df, item_name, p.get_name())
                
                if  pd.isna(status) or status == 'In Progress':
                    df.at[item_name, p.get_name()] = 'In Progress'
                    print(f'Processing {item_name} with {p.get_name()}')
                    if p.process(input_folder, item_name, self.base_folder + '/' + p.get_output_folder_name()):
                        df.at[item_name, p.get_name()] = 'Completed'
                        df.to_excel(self.control_file, index=True)
                elif status == 'Pause':
                    continue

            if p.get_name() == 'Title': 
                status = self.get_cell_value(df, sermon['item'], 'Title')
                if status == 'Completed' :
                    sermon['status'] = 'ready'
                    with open(self.base_folder + '/config/sermon.json', 'w', encoding='UTF-8') as json_file:  
                        json.dump(sermon_data, json_file, indent=4, ensure_ascii=False)



base_folder = '/Volumes/Jun SSD/data'
input_folder = "/Volumes/Jun SSD/HLC"

pipeline = ProcessingPipeline(base_folder,input_folder)

pipeline.process()


