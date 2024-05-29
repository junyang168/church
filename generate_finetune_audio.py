import os
import requests
import json
import jsonlines
from moviepy.editor import VideoFileClip
import sys

from  web.api.script_delta import ScriptDelta


class FineTuneDataGenerator:
    def __init__(self, base_dir:str, gen_audio:bool=True):
        self.base_dir = base_dir
        self.gen_audio = gen_audio

    def get_sentences(self, start_time:int, sentences:list):
        return [
            {
                "text": sentence['text'],
                "start": sentence['start_time'] - start_time ,
                "end": sentence['end_time'] - start_time
            } for sentence in sentences
        ]

    def get_sections(self, item_name:str, chunks:list):
            return [
                {
                    "audio": {
                        "path": f"dataset/{item_name}/{chunk['para_start_index']}_{i}.wav"
                    },
                    "sentence": chunk['text'],
                    "language": "Chinese",
                    "duration": int(chunk['end_time']) - int(chunk['start_time']) + 1,
                    "sentences": self.get_sentences(chunk['start_time'],chunk['sentences'])
                } for i, chunk in enumerate(chunks)
            ]
           

    
    def generate_audio_sections(self, item_name:str, chunks:list,train_test_ratio:float=0.8):
        sections = self.get_sections(item_name, chunks)    
        if self.gen_audio:
            video_path =  os.path.join(self.base_dir,'video' , item_name + '.mp4')
            for chunk, section in zip(chunks,sections):
                video_clip = VideoFileClip(video_path)
                audio_path = os.path.join(self.base_dir, section['audio']['path'] )
                audio_clip = video_clip.subclip(chunk['start_time'], chunk['end_time']).audio
                audio_clip.write_audiofile(audio_path, codec='pcm_s16le', fps=16000, ffmpeg_params=["-ac", "1"])
                audio_clip.close()
                video_clip.close()

        with open(os.path.join(self.base_dir, 'dataset', item_name +  '.json'), 'w', encoding='UTF-8') as f:
            json.dump(chunks, f, indent=4, ensure_ascii=False)    

        training_file = os.path.join(self.base_dir, 'dataset/train.jsonl' )
        training_len = int(len(sections) * train_test_ratio)
        with jsonlines.open(training_file, mode='w') as writer:
            for setion in sections[:training_len]:
                writer.write(setion)
        test_file = os.path.join(self.base_dir, 'dataset/test.jsonl' )
        with jsonlines.open(test_file, mode='w') as writer:
            for setion in sections[training_len:]:
                writer.write(setion)
    
if __name__ == '__main__':
    base_dir = os.path.join( os.path.dirname(os.path.abspath(__file__)),'data')

    item = '2019-2-18 良心'

    script = ScriptDelta(base_dir, item )
    chunks = script.get_chunks()

    generator = FineTuneDataGenerator(base_dir, gen_audio=False)
    generator.generate_audio_sections(item, chunks)
    
