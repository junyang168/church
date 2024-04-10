import pandas as pd
from utils import get_files
from processor import Processor
from utils import get_files

from processor_transcribe import ProcessorTranscribe
from processor_extract_audio import ProcessorExtractAudio
from processor_fix import ProcessorFix
from processor_process_script import ProcessorProcessScript


class ProcessingPipeline:
    def __init__(self, base_folder:str):
        self.processors = [ProcessorExtractAudio(), ProcessorTranscribe(),ProcessorProcessScript(), ProcessorFix()]
        self.base_folder = base_folder
        self.control_file = base_folder + '/Processing_stage.xlsx'
    
    def get_item_name(self, fname: str):
        if '_' not in fname:
            return fname.split('.')[0]
        else:
            return fname.split('_')[0]
    
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
            input_folder = p.get_input_folder_name() if p.get_input_folder_name()[0] == '/' else self.base_folder + '/' + p.get_input_folder_name()
            files = get_files(input_folder, p.get_file_extension())
            files.sort()
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
                if status is None:
                    df.at[item_name, p.get_name()] = 'In Progress'
                
                if status == 'In Progress' or pd.isna(status):
                    print(f'Processing {item_name} with {p.get_name()}')
                    p.process(input_folder, item_name, self.base_folder + '/' + p.get_output_folder_name(), fname, is_append)
                    if self.get_file_index(fname) == last_item_index:
                        df.at[item_name, p.get_name()] = 'Completed'
                        df.to_excel(self.control_file, index=True)



base_folder = '/Users/junyang/church/data'

pipeline = ProcessingPipeline(base_folder)

pipeline.process()


