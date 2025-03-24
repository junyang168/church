import torch
import clip
from PIL import Image
import numpy as np
import cv2
import os

class ScreenDetector:
    def __init__(self):
        # Determine device - with Metal support for Apple Silicon
        if torch.backends.mps.is_available():
            self.device = "mps"  # Apple Metal Performance Shaders
            print("Using Apple Metal for acceleration")
        elif torch.cuda.is_available():
            self.device = "cuda"
            print("Using CUDA for acceleration")
        else:
            self.device = "cpu"
            print("Using CPU")

        # Load CLIP model and preprocess function
        self.model, self.preprocess = clip.load("ViT-B/32", device=self.device)

    def detect_screen(self, image_path_frame, confidence_threshold=0.7):
        """
        Detect a presentation screen in an image using CLIP with support for CPU, CUDA, and Apple Metal.
        Works with both blue and black background screens.
        
        Args:
            image_path: Path to the JPEG image or a CV2 frame
            confidence_threshold: Minimum confidence to consider a detection valid
            
        Returns:
            (x, y, w, h), confidence: Bounding box of the screen and detection confidence,
                                    or (None, confidence) if no screen is detected
        """
        # Check if input is a path or an image
        if isinstance(image_path_frame, str) and os.path.isfile(image_path):
            # Load image from file using PIL
            pil_image = Image.open(image_path)
            # Convert to OpenCV format for later processing
            frame = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
        else:
            # Assume it's a CV2 frame
            frame = image_path_frame
            # Convert OpenCV frame to PIL Image
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(frame_rgb)
        
        
        
        # Prepare image
        image = self.preprocess(pil_image).unsqueeze(0).to(self.device)
        
        # Define descriptions for what we're looking for - include both blue and black backgrounds
        descriptions = [
            "a projector screen with blue background",
            "a presentation slide with blue background",
            "a monitor screen with black background ",
            "a lecture slide with text on blue background",
            "a blue screen with white text",
            "a black screen with white text"
        ]
        
        # Encode descriptions
        text = clip.tokenize(descriptions).to(self.device)
        
        # Get similarity scores
        with torch.no_grad():
            image_features = self.model.encode_image(image)
            text_features = self.model.encode_text(text)
            
            # Normalize features
            image_features /= image_features.norm(dim=-1, keepdim=True)
            text_features /= text_features.norm(dim=-1, keepdim=True)
            
            # Calculate similarity
            similarity = (100.0 * image_features @ text_features.T).softmax(dim=-1)
        
        # Get highest similarity score
        value, index = similarity[0].max(dim=0)
        confidence = value.item()
        matched_description = descriptions[index]
        
        print(f"Highest similarity: {confidence:.4f} for '{matched_description}'")
        
        # If we're confident enough that we see a slide, find its boundaries
        if confidence > confidence_threshold:
            # Determine which color to search for based on matched description
            is_black_background = "black" in matched_description
            
            # Create masks for different potential background colors
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            
            if is_black_background:
                # For black background - look for very dark areas
                # Note: In HSV, black has low V (value/brightness)
                black_mask = cv2.inRange(hsv, np.array([0, 0, 0]), np.array([180, 255, 50]))
                color_mask = black_mask
            else:
                # For blue background
                blue_mask = cv2.inRange(hsv, np.array([100, 50, 50]), np.array([140, 255, 255]))
                color_mask = blue_mask
            
            # Try a combined approach if the specific color mask doesn't yield good results
            if cv2.countNonZero(color_mask) < 1000:  # Not enough pixels found
                # Try a more general approach - look for rectangular shapes
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                blurred = cv2.GaussianBlur(gray, (9, 9), 0)
                _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
                
                # Look for edge-based detection as a fallback
                edges = cv2.Canny(gray, 50, 150)
                kernel = np.ones((5, 5), np.uint8)
                dilated = cv2.dilate(edges, kernel, iterations=2)
                color_mask = dilated
            
            # Clean up mask with morphological operations
            kernel = np.ones((5, 5), np.uint8)
            color_mask = cv2.morphologyEx(color_mask, cv2.MORPH_CLOSE, kernel)
            color_mask = cv2.morphologyEx(color_mask, cv2.MORPH_OPEN, kernel)
            
            # Find contours in the mask
            contours, _ = cv2.findContours(color_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            if contours:
                # Filter contours by area and aspect ratio to find likely screens
                valid_contours = []
                for contour in contours:
                    area = cv2.contourArea(contour)
                    if area > 5000:  # Minimum size to consider
                        x, y, w, h = cv2.boundingRect(contour)
                        aspect_ratio = float(w) / h
                        # Most screens/slides have aspect ratios between 1:1 and 16:9
                        if 0.5 < aspect_ratio < 2.0:
                            valid_contours.append((contour, area, (x, y, w, h)))
                
                if valid_contours:
                    # Sort by area (largest first)
                    valid_contours.sort(key=lambda x: x[1], reverse=True)
                    _, _, (x, y, w, h) = valid_contours[0]
                    
                    # Check if the contour is reasonably sized relative to the image
                    img_height, img_width = frame.shape[:2]
                    contour_area_ratio = (w * h) / (img_width * img_height)
                    
                    if 0.05 < contour_area_ratio < 0.9:  # Between 5% and 90% of image                        
                        return (x, y, w, h), confidence
        
        return None, confidence

screen_detector = ScreenDetector()

# Example usage for a single frame
if __name__ == "__main__":
    detector = ScreenDetector()
    image_path = "data/test_blackscreen.jpg"  # Replace with your image path
    frame = cv2.imread(image_path)
    bbox, confidence = detector.detect_screen_from_path(frame, confidence_threshold=0.5)
    
    if bbox:
        print(f"Screen detected at {bbox} with confidence {confidence:.4f}")
        
        # Optional: crop and save the detected screen
        x, y, w, h = bbox
        cropped_screen = frame[y:y+h, x:x+w]        
        cv2.imwrite('cropped_screen.jpg', cropped_screen)
        print(f"Cropped screen saved to 'cropped_screen.jpg'")

        cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 0, 0), 3)
        cv2.imshow("Detected Screen", frame)
        cv2.waitKey(0)
        cv2.destroyAllWindows() 
    else:
        print(f"No screen detected. Highest confidence: {confidence:.4f}")


