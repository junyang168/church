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

    item_profile = {
        '2019-2-15 心mp4':0,
        '2019-2-18 良心':0,
        '2019-3-17 挽回祭':2,
        '2019-3-24 罗马书3章21至31节':1,
        '2019-04-21 耶稣的空坟墓':0,
        '2019-05-12 圣灵充满':1,
        '2019-05-19 喜乐':0,
        '2019-05-26 罗马书5章1至2节':1,
        '2019-3-31 宗主国与附庸国的约':1,
        '2019-4-14 罗4 1-25 因信成义':1,
        '2019-4-4 神的國 ':0,
        '2019-4-7 罗马书4章1至25节':1,
    }


    def __init__(self) -> None:
        super().__init__()
        base_model = VGG16(weights='imagenet', include_top=False)
        self.model = Model(inputs=base_model.input, outputs=base_model.get_layer('block5_conv3').output)
        self.showImage = True


    def get_name(self):
        return "pull_slide"


    def get_input_folder_name(self):
        return "video"

    def get_output_folder_name(self):
        return "slide"

    def get_file_extension(self):
        return ".mp4"
    
    def convert_timestamp_to_seconds(self,index_id, timestamp):
        section = int(index_id.split('_')[0]) - 1
        hours, minutes, seconds = map(int, timestamp.split(',')[0].split(':'))
        total_seconds = hours * 3600 + minutes * 60 + seconds
        return 20*60*section + total_seconds
    

    def prepare_image(self, frame, img_profile):
        # convert the color from BGR to RGB then convert to PIL array
#        img = frame[:1000, 645:]
        if img_profile :
            min_y = img_profile['min_y']-100
            if min_y < 0:
                min_y = 0
            img = frame[min_y:img_profile['max_y'], img_profile['min_x']:img_profile['max_x']+100]
            gray = 255 - cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            _, threshold = cv2.threshold(gray, 60, 255, cv2.THRESH_BINARY )
        else:
            img = frame[:1000, 645:]
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            _, threshold = cv2.threshold(gray, 60, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)


        if self.showImage:
            cv2.imshow('frame', threshold)
            k = cv2.waitKey(0)
            if k == 99:
                self.showImage = False         # wait for ESC key to exit
                cv2.destroyAllWindows()
            elif k == 27:
                cv2.destroyAllWindows()
                exit(0)

        cvt_image =  cv2.cvtColor(threshold, cv2.COLOR_BGR2RGB)

        im_pil = Image.fromarray(cvt_image)

        # resize the array (image) then PIL image
        im_resized = im_pil.resize((224, 224))
        img_array = image.img_to_array(im_resized)
        image_array_expanded = np.expand_dims(img_array, axis = 0)
        return preprocess_input(image_array_expanded), threshold
    

    def get_image_and_embedding(self, frame, img_config):
        x, threshold = self.prepare_image(frame, img_config)
        return self.model.predict(x), threshold

    def compare_similarity( self, features1, features2):

        # Calculate the cosine similarity between the features
        similarity = np.dot(features1.flatten(), features2.flatten()) / (np.linalg.norm(features1) * np.linalg.norm(features2))

        return similarity
    
    def process(self, input_folder, item_name:str, output_folder:str, file_name:str = None, is_append:bool = False):
            video_path = self.get_file_full_path_name(input_folder,item_name)
            self.load_config(output_folder)
            self.extract_frames(video_path, output_folder, item_name) 

    def load_config(self, slide_folder): 
        self.item_configs = {}
        with jsonlines.open(f"{slide_folder}/bluescreen.jsonl", 'r') as f:
            
            for line in f.iter():
                self.item_configs[ line['item_name'] ] = line


    def extract_frames(self, video_path:str, output_folder:str, item_name:str):

        self.showImage = True


        img_cfg = self.item_configs.get(item_name)

        video = cv2.VideoCapture(video_path)

        # Get the duration of the video
        video_duration = int(video.get(cv2.CAP_PROP_FRAME_COUNT) / video.get(cv2.CAP_PROP_FPS))

        threshold1 = None
        features1 = None
        timer = 0
        snapshots = []
#        video_duration = 60
        while timer < video_duration:
            video.set(cv2.CAP_PROP_POS_MSEC, timer * 1000 )
            success, frame2 = video.read()
            features2, threshold2 = self.get_image_and_embedding(frame2, img_cfg)
            if threshold1 is not None:
                sim = self.compare_similarity(features1, features2)
                if sim <= 0.85:
                    snapshots.append({'time': timer, 'similarity': sim, 'frame': threshold2})
                    print(timer, sim)
            else:
                snapshots.append({'time': 0, 'similarity': 0.0 , 'frame': threshold2})
            threshold1 = threshold2
            features1 = features2
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
    pipeline.process(base_folder + '/' + pipeline.get_input_folder_name(), '2019-3-17 挽回祭', base_folder + '/slide')


