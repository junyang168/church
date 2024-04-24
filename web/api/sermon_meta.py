
from typing import List, Union, Optional
from pydantic import BaseModel
import os
import json
import boto3
import pytz
import datetime

class Sermon(BaseModel):
    item :str
    author: Optional[str] = None
    author_name: Optional[str] = None
    last_updated: Optional[str] = None
    status: Optional[str] = None
    assigned_to: Optional[str] = None
    assigned_to_name: Optional[str] = None
    title: Optional[str] = None
    deliver_date: Optional[str] = None
    summary: Optional[str] = None
    type: Optional[str] = None

class SermonMetaManager:

    def __init__(self, base_folder, user_getter) -> None:
        self.base_folder = base_folder
        self.config_folder =  os.path.join(self.base_folder, "config")
        self.metadata_file_path =  os.path.join(self.config_folder,"sermon.json")
        self.user_getter = user_getter
        self.load_sermon_metadata()
        self.load_sermons_from_s3()

    def load_sermons_from_s3(self):
        aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID")
        aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")
        s3 = boto3.client('s3', aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key)
        bucket_name = 'dallas-holy-logos'
        response = s3.list_objects_v2(Bucket=bucket_name, Prefix='script_review')
        
        for obj in response['Contents']:
            file_name = obj['Key']
            last_updated = self.convert_datetime_to_cst_string(obj['LastModified'])
            metadata = s3.head_object(Bucket=bucket_name, Key=file_name)['Metadata']
            author = metadata.get('author')
            author_name = self.user_getter(author).get('name')

            item_name = file_name.split('/')[-1].split('.')[0].strip()
            sermon = next((s for s in self.sermons if s.item == item_name ), None)
            if sermon:
                sermon.last_updated = last_updated
                sermon.author = author
                sermon.author_name = author_name

    def get_refresher(self):
        return ('sermon.json', self.load_sermon_metadata)

    def load_sermon_metadata(self):        
        with open(self.metadata_file_path) as f:
            sermon_meta = json.load(f)
        self.sermons = [Sermon( item=m.get('item'),
                               assigned_to= m.get('assigned_to'), 
                               status= m.get('status'), 
                               summary=m.get('summary'), 
                               title=m.get('title') ,
                               deliver_date=m.get('deliver_date'),
                               type=m.get('type')
                                 ) for m in sermon_meta]
        for s in self.sermons:
            s.assigned_to_name = self.user_getter(s.assigned_to).get('name')

    def convert_datetime_to_cst_string(self, dt: datetime.datetime) -> str:
        central = pytz.timezone('America/Chicago')
        cst_dt = dt.astimezone(central)
        cst_string = cst_dt.strftime('%Y-%m-%d %H:%M')
        return cst_string

    
    def get_sermon_metadata(self, user_id:str, item:str) -> Sermon:
        sermon = next((s for s in self.sermons if s.item == item.strip()), None)
        return sermon
  
    def update_sermon_metadata(self, user_id:str, item:str):
        sermon = self.get_sermon_metadata(user_id, item)
        sermon.last_updated = self.convert_datetime_to_cst_string(datetime.datetime.now())
        sermon.author = user_id
        sermon.author_name = self.user_getter(user_id).get('name')

    def save_sermon_metadata(self):
        with open(self.metadata_file_path, "w") as f:
            json.dump([s.dict() for s in self.sermons], f, ensure_ascii=False, indent=4)

