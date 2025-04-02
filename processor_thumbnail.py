import cv2
from PIL import Image
import os
from processor import Processor

class ProcessorGenerateThumbnail(Processor):
    def get_name(self):
        return "Thumbnail"
    def get_input_folder_name(self):
        return "video"
    def get_output_folder_name(self):
        return "thumbnail"
    def get_file_extension(self):
        return ".mp4"
    
    def accept_media_type(self):
        return "video"

    def generate_thumbnail(self, video_path, output_path, size=(160, 100), time_position_sec=60):
        """
        Generate a thumbnail from a video file.
        
        Parameters:
        - video_path: Path to the video file
        - output_path: Path where the thumbnail will be saved
        - size: Tuple of (width, height) for the thumbnail
        - time_position: Where in the video to grab the frame (0.1 = 10% into video)
        """
        try:
            # Open the video file
            video = cv2.VideoCapture(video_path)
            
            # Check if video opened successfully
            if not video.isOpened():
                raise Exception("Error: Could not open video file")
            
            # Get total number of frames
            total_frames = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
            
            # Calculate the frame number to capture (based on percentage)
            frame_number = cv2.CAP_PROP_FPS * time_position_sec
            
            # Set the frame position
            video.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
            
            # Read the frame
            success, frame = video.read()
            
            if not success:
                raise Exception("Error: Could not read frame from video")
            
            # Convert BGR (OpenCV format) to RGB
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Create PIL Image from frame
            image = Image.fromarray(frame_rgb)
            
            # Resize image while maintaining aspect ratio
            image.thumbnail(size, Image.Resampling.LANCZOS)
            
            # Ensure output directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Save the thumbnail
            image.save(output_path, quality=95)
            
            print(f"Thumbnail saved to: {output_path}")
            
            # Release the video capture object
            video.release()
            
        except Exception as e:
            print(f"An error occurred: {str(e)}")

    def process(self, input_folder, item_name:str, output_folder:str, file_name:str = None, is_append:bool = False):
        video_path = os.path.join(input_folder, item_name + self.get_file_extension())
        output_path = os.path.join(output_folder, item_name + ".jpg")
        self.generate_thumbnail(video_path, output_path, size=(160, 100), time_position_sec=60)
        return True
    
# Example usage
if __name__ == "__main__":
    # Example paths
    video_file = "path/to/your/video.mp4"
    thumbnail_file = "path/to/output/thumbnail.jpg"
    
