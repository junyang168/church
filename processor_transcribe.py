from processor import Processor

class ProcessorTranscribe(Processor):
    def get_name(self):
        return "transcribe"

    def get_priority(self):
        return 1

    def get_input_folder_name(self):
        return "audio"

    def get_output_folder_name(self):
        return "script"

    def get_file_extension(self):
        return ".mp3"

    def process(self, input_folder, item_name:str, output_folder:str, file_name:str = None, is_append:bool = False):
        mp3_file_name = input_folder + '/' + file_name
        script_file_name = self.get_file_full_path_name(output_folder, item_name)

        from openai import OpenAI
        client = OpenAI()

        with open(mp3_file_name, "rb") as audio_file:
            transcription = client.audio.transcriptions.create(
                model="whisper-1", 
                file=audio_file
            )

            file1 = open(script_file_name, 'a' if is_append else 'w')
            file1.write(transcription.text)
            file1.close()
