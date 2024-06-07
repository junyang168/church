import os
import cv2
import base64
import requests


class ImageToText:
    def __init__(self, base_dir:str, item_name:str) -> None:
        self.video_path = os.path.join(base_dir, 'video', item_name + '.mp4')
        self.api_key = os.getenv('OPENAI_API_KEY')
    def get_base64_encoded_image(self, image):
        _, im_arr = cv2.imencode('.jpg', image)
        im_bytes = im_arr.tobytes()
        im_b64 = base64.b64encode(im_bytes)
        return im_b64.decode('utf-8')


    def extract_slide(self, timestamp:int):
#        return "this is a test"
    
        video = cv2.VideoCapture(self.video_path)
        video.set(cv2.CAP_PROP_POS_MSEC, timestamp )
        success, frame = video.read()
        base64_image = self.get_base64_encoded_image(frame)

        headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {self.api_key}"
        }

        payload = {
            "model": "gpt-4o",
            "messages": [
                {
                "role": "user",
                "content": [
                    {
                    "type": "text",
                    "text": "get all text from the blue screen in the image. text is in mostly Chinese with some Greek, Hebew and English. respond with text only"
                    },
                    {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{base64_image}"
                    }
                    }
                ]
                }
            ],
            "max_tokens": 300
        }     

        response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)

        data = response.json()
        text =  data['choices'][0]['message']['content']  
        return text


if __name__ == '__main__' :
    base_dir = '/Users/junyang/church/data'
    item_name = '2019-3-17 挽回祭'
    extractor = ImageToText(base_dir, item_name)
    text = extractor.extract_slide(30000)
    print(text)
