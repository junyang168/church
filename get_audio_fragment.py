from pydub import AudioSegment

# Load audio file
audio = AudioSegment.from_file("/Users/junyang/Documents/2019-06-23.mp3")

# Define start and end times (in milliseconds)
start_time = 67000  # 10 seconds
end_time = 80000    # 20 seconds

# Cut the segment
cut_audio = audio[start_time:end_time]

# Save the segment
cut_audio.export("/Users/junyang/Documents/prompt.wav", format="wav")