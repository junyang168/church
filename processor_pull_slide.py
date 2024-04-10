from processor import Processor
import re
import jsonlines
from datetime import datetime
import cv2
import pytesseract
import math
import os
import pytesseract
import json


class ProcessorPullSlide(Processor):
    def get_name(self):
        return "pull_slide"


    def get_input_folder_name(self):
        return "script_processed"

    def get_output_folder_name(self):
        return "image"

    def get_file_extension(self):
        return ".txt"
    
    def convert_timestamp_to_seconds(self,index_id, timestamp):
        section = int(index_id.split('_')[0]) - 1
        hours, minutes, seconds = map(int, timestamp.split(',')[0].split(':'))
        total_seconds = hours * 3600 + minutes * 60 + seconds
        return 20*60*section + total_seconds

    def process(self, input_folder, item_name:str, output_folder:str, file_name:str = None, is_append:bool = False):
        script_file_name = self.get_file_full_path_name(input_folder, item_name)
        ts_index_file_name = os.path.join( input_folder , '../script' , item_name + '.jsonl')
        # Load all entries from jsonl file into a dictionary
        ts_index = {}
        with jsonlines.open(ts_index_file_name, 'r') as json_file:
            for entry in json_file:
                index = entry['index']
                ts_index[index] = entry

        with open(script_file_name, 'r') as file1:
            txt = file1.read()
            paragraphs = txt.split('\n\n')
            snapshots = []
            for para in paragraphs:  
                if not para or para.isspace():
                    continue              
                index_id = re.findall(r'\[(.*?)\]', para)[-1]
                ts = ts_index[index_id]["end_time"]
                time_in_seconds = self.convert_timestamp_to_seconds(index_id, ts)
                ts_index[index_id]['timestamp'] = time_in_seconds
                snapshots.append(ts_index[index_id])
            video_path = os.path.join('/Users/junyang/Downloads/video', item_name + '.mp4')
            self.extract_frames(video_path, output_folder, item_name, snapshots)  

    def extract_text_from_frame(self, frame):
        image = frame[::, 645:]
        # Convert the image to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        # Apply thresholding to preprocess the image
        _, threshold = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
        # Perform OCR using Tesseract
        text = pytesseract.image_to_string(threshold, lang='chi_tra+grc+heb')
        return text  

    def extract_frames(self, video_path:str, output_folder:str, item_name:str,  indices: list[dict]):
        # Open the video file
        video = cv2.VideoCapture(video_path)

        slide_text = []
        for idx in indices:
            video.set(cv2.CAP_PROP_POS_MSEC, idx['timestamp'] * 1000 )
            success, frame = video.read()
            if success:
                print(f'Processing {item_name} with index {idx["index"]}')
                image_path = f"{output_folder}/{item_name}/{idx['index']}.jpg"
                cv2.imwrite(image_path, frame)
                text = self.extract_text_from_frame(frame)
                slide_text.append({'index': idx['index'], 'text': text})
        json.dump(slide_text, open(f"{output_folder}/{item_name}/slide_text.json",'w',encoding='UTF-8'), ensure_ascii=False )
        # Release the video file
        video.release()

if __name__ == '__main__':
    # Example usage
    base_folder = '/Users/junyang/church/data'  
    pipeline = ProcessorPullSlide()
    pipeline.process(base_folder + '/script_processed', '2019-2-15 心mp4', base_folder + '/image')


