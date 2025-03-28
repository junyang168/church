from abc import ABC, abstractmethod

class Processor(ABC):


    @abstractmethod
    def get_name(self):
        pass

    def get_input_folder_name(self):
        pass

    def get_output_folder_name(self):
        pass

    def get_file_extension(self):
        pass

    @abstractmethod
    def process(self,input_folder, item_name:str, output_folder:str, file_name:str = None, is_append:bool = False):
        pass


    def get_file_full_path_name(self, folder_name:str, item_name:str):
        return folder_name + '/' + item_name + self.get_file_extension()
    
    def setmetadata(self, items:list, metadata_file:str):
        pass

    def accept_media_type(self):
        return None

