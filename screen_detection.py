from transformers import MaskFormerFeatureExtractor, MaskFormerForInstanceSegmentation
from PIL import Image
import requests
import cv2

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.colors import ListedColormap, LinearSegmentedColormap
from matplotlib import cm
import torch
import numpy as np
from collections import defaultdict
from processor  import Processor
import jsonlines


class DectectBluescreen(Processor):

    def get_name(self):
        return 'detect_bluescreen'

    def __init__(self):
        self.feature_extractor = MaskFormerFeatureExtractor.from_pretrained("facebook/maskformer-swin-base-ade")
        self.model = MaskFormerForInstanceSegmentation.from_pretrained("facebook/maskformer-swin-base-ade")


    def get_input_folder_name(self):
        return 'video'
    
    def get_output_folder_name(self):
        return 'slide'

    def get_file_extension(self):  
        return '.mp4' 


    def process(self, input_folder, item_name: str, output_folder: str, file_name: str = None, is_append: bool = False):

        video_path = self.get_file_full_path_name(input_folder, item_name)

        video = cv2.VideoCapture(video_path)
        success, frame = video.read()
    

        image = Image.fromarray(frame)

        inputs = self.feature_extractor(images=image, return_tensors="pt")

        outputs = self.model(**inputs)

        # you can pass them to feature_extractor for postprocessing
        # we refer to the demo notebooks for visualization (see "Resources" section in the MaskFormer docs)
        panoptic_segmentation = self.feature_extractor.post_process_panoptic_segmentation(outputs, target_sizes=[image.size[::-1]])[0]

        self.draw_panoptic_segmentation(**panoptic_segmentation)

        # visualize the predicted semantic map  
        min_x, max_x, min_y, max_y = self.get_blue_screen_boundary(**panoptic_segmentation)

        if not min_x:
            return


        blue_screen = frame[min_y:max_y, min_x:max_x]

        cv2.imshow("Display window", blue_screen )
        k = cv2.waitKey(0) # Wait for a keystroke in the window
        video.release()

        if k == 99: # press 'c' to continue
            bluescreen_cfg_file = output_folder + '/bluescreen.jsonl'
            jsonlines.open(bluescreen_cfg_file, 'a').write({'item_name': item_name, 'min_x': min_x, 'max_x': max_x, 'min_y': min_y, 'max_y': max_y})


    def draw_panoptic_segmentation(self, segmentation, segments_info):
        # get the used color map
        viridis = cm.get_cmap('viridis', torch.max(segmentation))
        fig, ax = plt.subplots()
        ax.imshow(segmentation)
        instances_counter = defaultdict(int)
        handles = []
        # for each segment, draw its legend
        for segment in segments_info:
            segment_id = segment['id']
            print(segment)
            segment_label_id = segment['label_id']
            segment_label = self.model.config.id2label[segment_label_id]
            label = f"{segment_label}-{instances_counter[segment_label_id]}"
            instances_counter[segment_label_id] += 1
            color = viridis(segment_id)
            handles.append(mpatches.Patch(color=color, label=label))
            
        ax.legend(handles=handles)

        plt.show(block=True)
        plt.close()


    def calculate_polygon_area(self, vertices):
        n = len(vertices)
        area = 0.0
        for i in range(n):
            x1, y1 = vertices[i]
            x2, y2 = vertices[(i + 1) % n]
            area += (x1 * y2 - x2 * y1)
        area = abs(area) / 2.0
        return area


    def get_blue_screen_boundary(self, segmentation, segments_info):

        segments = [segment['id'] for segment in segments_info if self.model.config.id2label[segment['label_id']].find('screen') >=0 or self.model.config.id2label[segment['label_id']].find('board') >=0]
        if len(segments) == 0:
            return None, None, None, None
        
        segment_id = segments[0]

        blue_screen = np.full(segmentation.shape, 255, dtype=np.uint8)

        for x in range(segmentation.shape[0]):
            for y in range(segmentation.shape[1]):
                pixel_id = segmentation[x, y].item()
                if pixel_id != segment_id: 
                    blue_screen[x, y] = 0

        img = Image.fromarray(blue_screen).convert('L')

        cv2.imwrite('blue_screen.png', np.array(img))

        img_data = cv2.imread('blue_screen.png', cv2.IMREAD_GRAYSCALE)

        contours, hierarchy = cv2.findContours(img_data,  cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE) 

        max_control = None
        max_area = -1
        for contour in contours:
            contour = np.squeeze(contour)
            area = self.calculate_polygon_area(contour)
            if area > max_area:
                max_area = area
                max_control = contour

        # Calculate the bounding rectangle of the polygon
        min_x = np.min(max_control[:, 0])
        max_x = np.max(max_control[:, 0])
        min_y = np.min(max_control[:, 1])
        max_y = np.max(max_control[:, 1])


        return int(min_x), int(max_x), int(min_y), int(max_y)


