from pydub import AudioSegment
import os


def get_section_of_mp3(input_file, output_file, start_time, end_time):
    audio = AudioSegment.from_mp3(input_file)
    section = audio[start_time:end_time]
    section.export(output_file, format="mp3")


base_folder = '/Users/junyang/Church/data'
# Example usage
input_file = os.path.join(base_folder,'audio', "2019-2-18 良心_1.mp3")
output_file = os.path.join(base_folder, "2019-2-18-sample__3_min.mp3")
start_time = (0 * 60 + 16) * 1000  # Start time in milliseconds
end_time = start_time + 3 * 60 * 1000  # End time in milliseconds

get_section_of_mp3(input_file, output_file, start_time, end_time)