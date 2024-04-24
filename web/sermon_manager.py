import os
from access_control import AccessControl
from typing import List, Union, Optional
from pydantic import BaseModel
from enum import Enum, auto
import glob
import datetime
import boto3
import json

class Sermon(BaseModel):
    item :str
    author: Optional[str]
    author_name: Optional[str]
    last_updated: str

class Permission(BaseModel):
    canRead: bool
    canWrite: bool
 
class SermonManager:

    def load_surmons_from_s3(self):
        aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID")
        aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")
        s3 = boto3.client('s3', aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key)
        bucket_name = 'dallas-holy-logos'
        response = s3.list_objects_v2(Bucket=bucket_name, Prefix='script_fixed')
        
        self.sermons = []
        for obj in response['Contents']:
            file_name = obj['Key']
            last_updated = self.convert_datetime_to_cst_string(obj['LastModified'])
            metadata = s3.head_object(Bucket=bucket_name, Key=file_name)['Metadata']
            author = metadata.get('author')
            author_name = self._acl.get_user(author).get('name')
            self.sermons.append( Sermon( item = file_name.split('/')[-1].split('.')[0].strip(), last_updated=last_updated, author=author, author_name=author_name))
        

    def __init__(self) -> None:
        self._acl = AccessControl()
        self.load_surmons_from_s3()

    
    def get_surmons(self, user_id:str):
        return self.sermons
    

    def convert_datetime_to_cst_string(self, dt: datetime.datetime) -> str:
        cst_timezone = datetime.timezone(datetime.timedelta(hours=-6))
        cst_dt = dt.astimezone(cst_timezone)
        cst_string = cst_dt.strftime('%Y-%m-%d %H:%M')
        return cst_string


    def get_sermon_permissions(self, user_id:str, item:str):
        sermon = next((s for s in self.sermons if s.item == item.strip()), None)
        if not sermon:
            return Permission(canRead=False, canWrite=False)
        permissions = self._acl.get_user_permissions(user_id)        
        if not permissions:
            return Permission(canRead=False, canWrite=False)
        
        readPermissions = [p for p in permissions if p.find('read') >= 0]

        canRead = len(readPermissions) > 0

        writePermissions = [p for p in permissions if p.find('write') >= 0]
        if user_id == sermon.author:
            canWrite =  'write_owned_item' in writePermissions or 'write_any_item' in writePermissions
                
        else:
            canWrite =  'write_any_item' in writePermissions
        
        return Permission(canRead=canRead, canWrite=canWrite) 

sermonManager = SermonManager()

if __name__ == '__main__':
    permission = sermonManager.get_sermon_permissions('junyang168@gmail.com', '2019-2-15 心mp4')
    print('junyang', permission)
    permission = sermonManager.get_sermon_permissions('junyang168@gmail.com', '2019-4-4 神的國 ')
    print('junyang', permission)
    
    permission = sermonManager.get_sermon_permissions('jianwens@gmail.com', '2019-2-15 心mp4')
    print('jianwen', permission)
    permission = sermonManager.get_sermon_permissions('dallas.holy.logos@gmail.com', '2019-2-15 心mp4')
    print('admin', permission)
    


