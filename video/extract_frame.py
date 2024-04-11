import cv2
import pytesseract
import math



def extract_frames(video_path, output_dir, interval):
    # Open the video file
    video = cv2.VideoCapture(video_path)
    # Get the video codec format
    h = int(video.get(cv2.CAP_PROP_FOURCC))

    codec = chr(h&0xff) + chr((h>>8)&0xff) + chr((h>>16)&0xff) + chr((h>>24)&0xff)

    # Initialize variables
    frame_count = 0
    success = True
    frame_rate = video.get(cv2.CAP_PROP_FPS)

    while success:
        # Read the next frame
        success, frame = video.read()

        # Get the frame rate of the video

        # Extract frame at the specified interval
        if frame_count % int( interval * frame_rate ) == 0:
            # Save the frame as an image
            image_path = f"{output_dir}/frame_{ math.ceil(frame_count/ frame_rate)  }.jpg"
            cv2.imwrite(image_path, frame)
        frame_count += 1

    # Release the video file
    video.release()



def extract_text_from_image(image_path):
    # Read the image
    image = cv2.imread(image_path)

    image = image[::, 645:]
    # Convert the image to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    # Apply thresholding to preprocess the image
    _, threshold = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)

    threshold = threshold[200:900, ::]

    cv2.imshow("Display window", threshold)
    k = cv2.waitKey(0) # Wait for a keystroke in the window   
    # Perform OCR using Tesseract
    text = pytesseract.image_to_string(threshold, lang='chi_sim')
    return text


import os
import boto3
os.environ['TESSDATA_PREFIX'] = '/opt/homebrew/share/tessdata'

extract_frames('/Users/junyang/church/data/video/2019-2-15 心.mp4', '/Users/junyang/church/data/image/2019-2-15 心mp4', 10  )

# Example usage
base_folder = '/Users/junyang/church/data'
image_path = base_folder + '/image/2019-2-15 心mp4/'  + "frame_990.jpg"

# Example usage
image_path = base_folder + '/image/2019-2-15 心mp4/'  
print(extract_text_from_image(image_path+ "1_8.jpg") )
#print('------------')
#print( extract_text_from_image(image_path+ "1_22.jpg") )
#print('------------')
#print( extract_text_from_image(image_path+ "1_31.jpg") )
#print('------------')
#print( extract_text_from_image(image_path+ "1_46.jpg") )
