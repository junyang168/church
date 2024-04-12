from processor import Processor
import re
import jsonlines
from datetime import datetime
import cv2
import math
import os
import json
from image_to_text import ImageToText
from keras.applications.vgg16 import VGG16
from keras.preprocessing import image
from keras.applications.vgg16 import preprocess_input
from keras.models import Model
import numpy as np
from PIL import Image


class ProcessorPullSlide(Processor):
    def get_name(self):
        return "pull_slide"


    def get_input_folder_name(self):
        return "script_processed"

    def get_output_folder_name(self):
        return "slide"

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
            prev_para = None
            for para in paragraphs:  
                if not para or para.isspace():
                    continue   
                index_id = re.findall(r'\[(.*?)\]', para)[-1]
                ts = ts_index[index_id]["end_time"]
                time_in_seconds = self.convert_timestamp_to_seconds(index_id, ts)
                ts_index[index_id]['timestamp'] = time_in_seconds
                snapshots.append(ts_index[index_id])

            for i in range(len(snapshots)):
                snapshots[i]['start_time'] =  snapshots[i-1]['timestamp'] if i > 0 else 0

            video_path = os.path.join('/Users/junyang/Downloads/video', item_name + '.mp4')
            self.extract_frames(video_path, output_folder, item_name, snapshots)  

    def prepare_image(self, frame):
        # convert the color from BGR to RGB then convert to PIL array
        img = frame[:1000, 645:]
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        _, threshold = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
        cvt_image =  cv2.cvtColor(threshold, cv2.COLOR_BGR2RGB)
        im_pil = Image.fromarray(cvt_image)

        # resize the array (image) then PIL image
        im_resized = im_pil.resize((224, 224))
        img_array = image.img_to_array(im_resized)
        image_array_expanded = np.expand_dims(img_array, axis = 0)
        return preprocess_input(image_array_expanded)

    def compare_similarity( self, frame1, frame2):

        base_model = VGG16(weights='imagenet', include_top=False)

        # Create a new model with the output of the last convolutional layer as the output
        model = Model(inputs=base_model.input, outputs=base_model.get_layer('block5_conv3').output)

        x1 = self.prepare_image(frame1)
        x2 = self.prepare_image(frame2)
        # Extract the features from the images using the VGG16 model
        features1 = model.predict(x1)
        features2 = model.predict(x2)

        # Calculate the cosine similarity between the features
        similarity = np.dot(features1.flatten(), features2.flatten()) / (np.linalg.norm(features1) * np.linalg.norm(features2))

        return similarity
    

    def extract_frames(self, video_path:str, output_folder:str, item_name:str,  indices: list[dict]):

        video = cv2.VideoCapture(video_path)

        # Get the duration of the video
        video_duration = int(video.get(cv2.CAP_PROP_FRAME_COUNT) / video.get(cv2.CAP_PROP_FPS))

        frame1 = None
        timer = 0
        snapshots = []
        while timer < video_duration:
            video.set(cv2.CAP_PROP_POS_MSEC, timer * 1000 )
            success, frame2 = video.read()
            if frame1 is not None:
                sim = self.compare_similarity(frame1, frame2)
                if sim <= 0.85:
                    snapshots.append({'time': timer, 'similarity': sim, 'frame': frame2})
                    print(timer, sim)
            else:
                snapshots.append({'time': 0, 'similarity': 0.0 , 'frame': frame2})
            frame1 = frame2
            timer += 2

        text_extractor = ImageToText()
        text_extractor.extract_slides(snapshots)
        text_extractor.save(f"{output_folder}/{item_name}.json")
        
        # Release the video file
        video.release()

if __name__ == '__main__':
    # Example usage
    base_folder = '/Users/junyang/church/data'  
    pipeline = ProcessorPullSlide()
    pipeline.process(base_folder + '/script_processed', '2019-2-15 心mp4', base_folder + '/slide')


