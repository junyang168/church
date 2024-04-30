import json
import difflib
import jsonlines
import boto3
import os
import math

class ScriptDelta:

    def __init__(self, base_folder:str, item_name:str) -> None:
        self.base_folder = base_folder
        self.item_name = item_name

    def loadPatchedScript(self):
        with open( self.base_folder +  '/script_patched/' + self.item_name + '.json', 'r') as file1:
            self.patched = json.load(file1)
            return [ p.get('text') for p in  self.patched ]

    def loadReviewScript(self):
        with open( self.base_folder +  '/script_review/' + self.item_name + '.json', 'r') as file1:
            self.review = json.load(file1)
            return [ p.get('text') for p in  self.review ]
    
    def loadTimeline(self):
        with jsonlines.open(self.base_folder +  '/script/' + self.item_name + '.jsonl', 'r') as f:            
            timelineData =list(f.iter())   
            for i in range(1, len(timelineData)):
                timelineData[i-1]['next_item'] = timelineData[i]['index'] if i < len(timelineData) else None

            return  { t['index'] : t  for t in  timelineData }
            

    def get_end_tag(self, tag:str):
        if len(tag) > 0:
            return '</>'
        else:
            return ''
    
    def set_tag(self, current_tag, line, new_tag):
        if  current_tag != new_tag:
            line.append(self.get_end_tag(current_tag))
            line.append(new_tag)
        return new_tag
    

    def calcuateTime(self, index, timestamp):
        sec = index.split('_')[0]
        ts = timestamp.split(',')[0].split(':')
        return (int(sec) - 1) * 60 * 20 + int(ts[0]) * 60 * 60 + int(ts[1]) * 60 + int(ts[2])

    def formatTime(self, time):
        h = time // 3600
        m = (time % 3600) // 60
        s = time % 60
        return f'{h:02}:{m:02}:{s:02}'

    def add_timeline(self, paragraphs):
        timelineDictionary = self.loadTimeline()
        for i in range(0, len(paragraphs)):
            para = paragraphs[i]
            timelineItem = timelineDictionary[  paragraphs[i-1]['index'] ] if i > 0 else None
            if timelineItem:
                start_item =  timelineDictionary[timelineItem['next_item']]
                para['start_time'] = self.calcuateTime( start_item['index'] , start_item['start_time'])
                para['start_timeline'] = self.formatTime(para['start_time'])
            else:
                para['start_timeline'] = '00:00:00'
                para['start_time'] = 0

            this_timeline = timelineDictionary[ para['index'] ]
            if this_timeline: 
                para['end_time'] = self.calcuateTime( this_timeline['index'], this_timeline['end_time']);
            else:
                para['end_time'] = 9999999999

    def create_paragraph(self, paragraph, text):
        new_paragraph = paragraph.copy()
        new_paragraph['text'] = text
        return new_paragraph
    


    def get_script(self, with_chanages:bool):
        if with_chanages:
            return self.getChanges()
        else:
            with open( self.base_folder +  '/script_review/' + self.item_name + '.json', 'r') as file1:
                self.patched = json.load(file1)
            self.add_timeline(self.patched)
            return self.patched
        

    def compare_text(self, patched_i: int , review_i:int):
        p1 = self.patched[patched_i]
        p2 = self.review[review_i]
        ratio = difflib.SequenceMatcher(None, p1['text'], p2['text']).ratio() 
        if ratio > 0.8:        
            return True
        return  p1['index'] == p2['index']



    def getChanges(self):

        paragraphs_patched = self.loadPatchedScript()
        paragraphs_review = self.loadReviewScript()
        self.add_timeline(self.patched)

        iPatched = 0
        iReview = 0
        len_patched = len(paragraphs_patched)
        len_review = len(paragraphs_review)
        script_changes = []
        while iPatched < len_patched and iReview < len_review:    
            while iPatched < len_patched and iReview < len_review and  self.compare_text(iPatched, iReview):
                diff = difflib.Differ().compare(paragraphs_patched[iPatched], paragraphs_review[iReview])
                line = []
                change_tag = ''
                for ele in diff:
                    if ele.startswith('-'):
                        change_tag = self.set_tag(change_tag, line,'<->')
                        line.append( ele.replace('-','').strip() )  
                    elif ele.startswith('+'):
                        change_tag = self.set_tag(change_tag, line,'<+>')
                        line.append( ele.replace('+','').strip() )  
                    else:
                        change_tag = self.set_tag(change_tag, line,'')
                        line.append( ele.strip() )  
                para = self.create_paragraph(self.patched[iPatched], ''.join(line) ) 
                script_changes.append(para)
                iPatched += 1
                iReview += 1

            j = iReview + 1        
            #difflib.SequenceMatcher(None, paragraphs_patched[iPatched], paragraphs_review[j]).ratio() < 0.8
            while iPatched < len_patched and j < len_review and not self.compare_text(iPatched, j) :
                j += 1
            
            if j >= len_review:
                if iPatched < len_patched:
                    p = self.create_paragraph(self.patched[iPatched], '<->' + self.patched[iPatched]['text'] + '</>')
                    script_changes.append(p)
                iPatched += 1
            else:
                for k in range(iReview, j):
                    p = self.create_paragraph(self.patched[iPatched-1],  '<+>' + paragraphs_review[k] + '</>' )
                    script_changes.append(p)
                iReview = j
        

        for k in range(iPatched, len_patched):
            p = self.patched[k]
            p['text'] = '<->' + p['text'] + '</>'
            script_changes.append(p)

        for k in range(iReview, len_review):
            p = { 'text': '<+>' + paragraphs_review[k] + '</>', 'index': self.patched[iPatched-1].get('index') }
            script_changes.append(p)

        return script_changes
    
    def save_to_s3(self, file_path: str, bucket_name: str, object_key: str, author:str):
        # Load the environment variables from .env file

        # Get the AWS access key and secret key from environment variables
        aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID")
        aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")

        # Use the access key and secret key in the save_to_s3 function
        s3 = boto3.client('s3', aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key)
        s3.upload_file(file_path, bucket_name, object_key, ExtraArgs={'Metadata': {'author': author}})
    
  
    def save_script(self,user_id:str, type:str, item:str, data):
        #update local file        
        folder = 'slide' if type == 'slides' else 'script_review'
        file_path = os.path.join(self.base_folder, folder, item + '.json')  
        with open(file_path, "w", encoding='UTF-8') as file:
            data_dicts = [p.dict() for p in data]
            json.dump(data_dicts, file, ensure_ascii=False, indent=4)    

        #update s3
        self.save_to_s3(file_path, 'dallas-holy-logos', f"{folder}/{item}.json", user_id)
        return {"message": f"{folder} updated successfully"}


if __name__ == '__main__':
    delta = ScriptDelta('/Users/junyang/church/data', '2019-2-15 心mp4')
    changes = delta.getChanges()
    for p in changes:
        print(p.get('start_timeline'), p.get('text'))
        print('\n')

