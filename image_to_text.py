import os
from anthropic import Anthropic
import base64
import cv2
import pytesseract
import json
import tqdm

class ImageToText:
    slides = []

    def extract_slides(self,snapshots):
        for i in tqdm.tqdm(range(len(snapshots))):
            ss = snapshots[i]
            threshold = ss['frame']
            text = self.get_text_from_image_claude(threshold)
            self.slides.append({'time': ss['time'], 'text': text})  

    def get_base64_encoded_image(self, image):
        _, im_arr = cv2.imencode('.jpg', image)
        im_bytes = im_arr.tobytes()
        im_b64 = base64.b64encode(im_bytes)
        return im_b64.decode('utf-8')

    client = Anthropic(
        # This is the default and can be omitted
        api_key=os.environ.get("ANTHROPIC_API_KEY"),
    )

    def get_text_from_image_claude(self, image):
        image_data = self.get_base64_encoded_image(image)

        message = self.client.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=1024,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/jpeg",
                                "data": image_data,
                            },
                        },
                        {
                            "type": "text",
                            "text": "get all text from the blue screen in the image. text is in mostly Chinese with some Greek, Hebew and English. respond with text only"
                        }
                    ],
                }
            ],
        )
        return message.content[0].text

    def save(self, file_name):
        json.dump(self.slides, open(file_name,'w',encoding='UTF-8'), ensure_ascii=False )

if __name__ == '__main__':  
    # Create an instance of the ImageToText class
    image_to_text = ImageToText()

    # Specify the path to the image file
    image_path = '/Users/junyang/church/data/image/2019-2-15 心mp4/1_8.jpg'

    img = cv2.imread(image_path)

    # Get the text from the image
#    text = image_to_text.extract_slide('s1',img)

    # Print the extracted text
#    print(text)