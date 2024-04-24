import pandas as pd
from utils import get_files
from processor import Processor
from utils import get_files


from processor_transcribe import ProcessorTranscribe
from processor_extract_audio import ProcessorExtractAudio
from processor_fix import ProcessorFix
from processor_process_script import ProcessorProcessScript
from processor_convert_video import ProcessorConvertVideo
from processor_pull_slide import ProcessorPullSlide
from screen_detection import DectectBluescreen
from patch import ProcessorPatch
from processor_audio import ProcessorAudio
import json
import datetime

class ProcessingPipeline:
    def __init__(self, base_folder:str, input_folder:str):
        self.processors = [ProcessorAudio(), 
                           ProcessorConvertVideo(),
                           ProcessorExtractAudio(), 
                           ProcessorTranscribe(),
                           ProcessorProcessScript(), 
                           ProcessorFix(),
                           DectectBluescreen(), 
                           ProcessorPullSlide(), 
                           ProcessorPatch()]
        self.base_folder = base_folder
        self.input_folder = input_folder
        self.control_file = base_folder + '/Processing_stage.xlsx'
    
    def get_item_name(self, fname: str):
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
        for p in self.processors:
            input_folder = self.input_folder if p.get_input_folder_name()[0] == '/' else self.base_folder + '/' + p.get_input_folder_name()
            files = get_files(input_folder, p.get_file_extension())
            files.sort()
            items = [self.get_item_name(f) for f in files]
            p.setmetadata( items, self.base_folder + '/config/sermon.json')
            item_name = ''            
            for fname in files:
                it_name = self.get_item_name(fname)                
                if item_name != it_name:                    
                    item_name = it_name
                    last_item_index = self.get_item_last_index(files, item_name)
                    is_append = False
                else:
                    is_append = True  
                
                status = self.get_cell_value(df, item_name, p.get_name())
                
                if  pd.isna(status) or status == 'In Progress':
                    df.at[item_name, p.get_name()] = 'In Progress'
                    print(f'Processing {item_name} with {p.get_name()}')
                    p.process(input_folder, item_name, self.base_folder + '/' + p.get_output_folder_name(), fname, is_append)
                    if self.get_file_index(fname) == last_item_index:
                        df.at[item_name, p.get_name()] = 'Completed'
                        df.to_excel(self.control_file, index=True)
                elif status == 'Pause':
                    continue




base_folder = '/Users/junyang/church/data'


input_folder = '/Users/junyang/Library/CloudStorage/GoogleDrive-junyang168@gmail.com/My Drive/Church/video'

pipeline = ProcessingPipeline(base_folder,input_folder)

pipeline.process()


