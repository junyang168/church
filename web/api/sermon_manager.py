import os
from access_control import AccessControl
from enum import Enum, auto
import glob
import datetime
import boto3
import json
from script_delta import ScriptDelta
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import boto3
from pydantic import BaseModel
from sermon_meta import Sermon, SermonMetaManager

<<<<<<< HEAD
=======
class Sermon(BaseModel):
    item :str
    author: Optional[str] = None
    author_name: Optional[str] = None
    last_updated: Optional[str] = None
    status: Optional[str] = None
    assigned_to: Optional[str] = None
    assigned_to_name: Optional[str] = None
    title: Optional[str] = None
    summary: Optional[str] = None

>>>>>>> 27c710a (add patch processor to fix data issue. add status)

class Permission(BaseModel):
    canRead: bool
    canWrite: bool
    canAssign: bool
    canUnassign: bool
    canAssignAnyone: bool
 

#SermanManager is responsible for managing 
# Sermon => sermon metadata
# Sermon Script and Slide  => SermonDelta
# Sermon Permissions => AccessControl
class SermonManager:

<<<<<<< HEAD
    def __init__(self) -> None:
        api_folder = os.path.dirname(os.path.abspath(__file__))
        self.base_folder = os.path.join(api_folder, '..', 'data')
        self.config_folder =  os.path.join(self.base_folder, "config")
        self._acl = AccessControl(self.base_folder)
        self._sm = SermonMetaManager(self.base_folder, self._acl.get_user)
=======
    def load_surmons_from_s3(self):
        aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID")
        aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")
        s3 = boto3.client('s3', aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key)
        bucket_name = 'dallas-holy-logos'
        response = s3.list_objects_v2(Bucket=bucket_name, Prefix='script_patched')
        
        for obj in response['Contents']:
            file_name = obj['Key']
            last_updated = self.convert_datetime_to_cst_string(obj['LastModified'])
            metadata = s3.head_object(Bucket=bucket_name, Key=file_name)['Metadata']
            author = metadata.get('author')
            author_name = self._acl.get_user(author).get('name')

            item_name = file_name.split('/')[-1].split('.')[0].strip()
            sermon = next((s for s in self.sermons if s.item == item_name ), None)
            if sermon:
                sermon.last_updated = last_updated
                sermon.author = author
                sermon.author_name = author_name
        
    def load_sermon_metadata(self):
        api_folder = os.path.dirname(os.path.abspath(__file__))
        self.file_path =  os.path.join(api_folder, '..', f"data/config/sermon.json")
        with open(self.file_path) as f:
            sermon_meta = json.load(f)
        self.sermons = [Sermon( item=item,
                               assigned_to= m.get('assigned_to'), 
                               status= m.get('status'), 
                               summary=m.get('summary'), 
                               title=m.get('title')  )  for item, m in sermon_meta.items()]
        for s in self.sermons:
            s.assigned_to_name = self._acl.get_user(s.assigned_to).get('name')

    def __init__(self) -> None:
        self._acl = AccessControl()
        self.load_sermon_metadata()
        self.load_surmons_from_s3()
>>>>>>> 27c710a (add patch processor to fix data issue. add status)


        refreshers = [self._acl.get_refresher(), self._sm.get_refresher()]
        event_handler = ConfigFileEventHandler(refreshers)
        observer = Observer()
        observer.schedule(event_handler, os.path.dirname(self.config_folder), recursive=False)
        observer.start()


    def get_file_path(self,type:str, item:str):
        return os.path.join(self.base_folder, type, item + '.json')

  

    def get_sermon_detail(self, user_id:str, item:str, changes:str = None):
        permissions = self.get_sermon_permissions(user_id, item)
        if not permissions.canRead:
            return "You don't have permission to read this item"

        sd = ScriptDelta(self.base_folder, item)
        return sd.get_script( changes == 'changes')
    


    def update_sermon(self, user_id:str, type:str,  item:str, data:dict):

        permissions = self.get_sermon_permissions(user_id, item)
        if not permissions.canWrite:
            return {"message": "You don't have permission to update this item"}
        
        #update last updated and author
        self._sm.update_sermon_metadata(user_id, item)

        sd = ScriptDelta(self.base_folder, item)
        return sd.save_script(user_id, type, item,data)


    def get_sermons(self, user_id:str):
        return self._sm.sermons


    def get_sermon_permissions(self, user_id:str, item:str):
        sermon = self._sm.get_sermon_metadata(user_id, item)
        if not sermon:
            return Permission(canRead=False, canWrite=False)
        permissions = self._acl.get_user_permissions(user_id)        
        if not permissions:
            return Permission(canRead=False, canWrite=False)
        
        readPermissions = [p for p in permissions if p.find('read') >= 0]

        canRead = len(readPermissions) > 0

        writePermissions = [p for p in permissions if p.find('write') >= 0]
        if user_id == sermon.assigned_to:
            canWrite =  'write_owned_item' in writePermissions or 'write_any_item' in writePermissions
                
        else:
            canWrite =  'write_any_item' in writePermissions

        #admin can assign to anyone any item      
        #editor can assign to himself item that is not assigned
        #author can unassign item that's assigned to him, but can't unasign item that's assigned to others 
        # reader can't assign or unassign
        #assignment is not allowed if sermon is in development
        canAssign = False
        canUnassign = False
        canAssignAnyone = False
        if sermon.status == 'ready':
            canAssignAnyone = 'assign_any_item' in permissions
            if canAssignAnyone: #admin
                canAssign = False
                canUnassign = False
            elif 'assign_item' not in permissions: #reader
                canAssign = False
                canUnassign = False
            else: #editor
                if sermon.assigned_to:  
                    if user_id == sermon.assigned_to:
                        canUnassign = True
                        canAssign = False
                    else:
                        canUnassign = False
                        canAssign = False
                else:
                    canUnassign = False
                    canAssign = True
        
        return Permission(canRead=canRead, canWrite=canWrite, canAssign=canAssign, canUnassign=canUnassign, canAssignAnyone=canAssignAnyone) 
    

    def assign(self, user_id:str, item:str, action:str) -> Permission: 
        sermon = self._sm.get_sermon_metadata(user_id, item) 
        permissions = self.get_sermon_permissions(user_id, item)
        if action == 'assign' and permissions.canAssign:
            sermon.assigned_to = user_id       
            sermon.assigned_to_name = self._acl.get_user(user_id).get('name')  
            sermon.status = 'assigned'               
        elif action == 'unassign' and permissions.canUnassign:
            sermon.assigned_to = None
            sermon.assigned_to_name = None
            sermon.status = 'ready'
        else:
            return None
        
        self._sm.save_sermon_metadata()
        

        return self.get_sermon_permissions(user_id, item)
    



class ConfigFileEventHandler(FileSystemEventHandler):
    def __init__(self, refreshers: list):
        self._refresheres = refreshers

    def on_modified(self, event):
        if event.is_directory:
            return
        for refresher in self._refresheres:
            if event.src_path.endswith(refresher[0]):
                refresher[1]()
                break




sermonManager = SermonManager()

if __name__ == '__main__':
<<<<<<< HEAD
    sermons = sermonManager.get_sermons('junyang168@gmail.com')
    print(sermons)
    msg = sermonManager.get_sermon_detail('junyang168@gmail.com', '2019-2-15 心mp4', 'changes')
    print(msg)

    msg = sermonManager.get_sermon_detail('junyang168@gmail.com', '2019-2-15 心mp4', '')
    print(msg)


=======
    sermons = sermonManager.get_surmons('junyang168@gmail.com')
    print(sermons)
>>>>>>> 27c710a (add patch processor to fix data issue. add status)
    permission = sermonManager.get_sermon_permissions('junyang168@gmail.com', '2019-2-15 心mp4')
    print('junyang', permission)
    permission = sermonManager.get_sermon_permissions('junyang168@gmail.com', '2019-4-4 神的國 ')
    print('junyang', permission)
    
    permission = sermonManager.get_sermon_permissions('jianwens@gmail.com', '2019-2-15 心mp4')
    print('jianwen', permission)
    permission = sermonManager.get_sermon_permissions('dallas.holy.logos@gmail.com', '2019-2-15 心mp4')
    print('admin', permission)
    


