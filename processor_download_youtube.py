from pytubefix import YouTube
import os

def download_youtube_video(url, output_path="."):
    try:
        # Create YouTube object
        yt = YouTube(url)
        
        # Filter for progressive MP4 streams (video + audio)
        video = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc().first()
        
        if not video:
            print("No suitable MP4 stream found")
            return
        
        # Create output directory if it doesn't exist
        if not os.path.exists(output_path):
            os.makedirs(output_path)
        
        # Download the video
        print(f"Downloading: {yt.title}")
        video.download(output_path)
        print(f"Downloaded successfully to {output_path}")
        
    except Exception as e:
        print(f"An error occurred: {str(e)}")

# Example usage
if __name__ == "__main__":
    # Replace with your YouTube video URL
    video_url = "https://www.youtube.com/watch?v=6w7O3LC9Qao&list=PLDn0mdXfe0fswgoeQ7SMzJOZb3mZVetJU&index=4"
    # Specify output directory (optional, defaults to current directory)
    output_directory = "/Volumes/Jun SSD/data/video"
    download_youtube_video(video_url, output_directory)