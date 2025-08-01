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
from sermon_comment import SermonCommentManager
from image_to_text import ImageToText
from copilot import Copilot, ChatMessage, Document
from typing import List
import requests


class Permission(BaseModel):
    canRead: bool
    canWrite: bool
    canAssign: bool
    canUnassign: bool
    canAssignAnyone: bool
    canPublish: bool 
    canViewPublished: bool 
 

#SermanManager is responsible for managing 
# Sermon => sermon metadata
# Sermon Script and Slide  => SermonDelta
# Sermon Permissions => AccessControl
class SermonManager:

    def __init__(self) -> None:


        api_folder = os.path.dirname(os.path.abspath(__file__))
        self.base_folder = os.path.join(api_folder, '..', 'data')
        self.config_folder =  os.path.join(self.base_folder, "config")
        self._acl = AccessControl(self.base_folder)
        self._sm = SermonMetaManager(self.base_folder, self._acl.get_user)
        self._scm = SermonCommentManager()
        self.semantic_search_url = os.getenv('SEMANTIC_SEARCH_API_URL')




        refreshers = [self._acl.get_refresher(), self._sm.get_refresher()]
        event_handler = ConfigFileEventHandler(refreshers)
        observer = Observer()
        observer.schedule(event_handler, os.path.dirname(self.config_folder + '/config.json'), recursive=False)
        observer.start()


    def get_file_path(self,type:str, item:str):
        return os.path.join(self.base_folder, type, item + '.json')

  

    def get_sermon_detail(self, user_id:str, item:str, changes:str = None):
        permissions = self.get_sermon_permissions(user_id, item)
        if not permissions.canRead:
            return "You don't have permission to read this item"

        sermon = self._sm.get_sermon_metadata(user_id, item)

        sd = ScriptDelta(self.base_folder, item)
        script =  sd.get_script( changes == 'changes')
        for p in script:
            if p.get('type') == 'comment':
                ui = self.get_user_info( p.get('user_id') )
                if ui:
                    p['user_name'] = ui.get('name')
        return sermon, script
    
    def get_slide_text(self, user_id:str, item:str, timestamp:int):
        permissions = self.get_sermon_permissions(user_id, item)
        if not permissions.canRead:
            return {"message": "You don't have read permission"}
        
        i2t = ImageToText(item)
        txt = i2t.extract_slide(timestamp)
        return {'text': txt}
        
    def get_slide_image(self, user_id:str, item:str, timestamp:int):
        permissions = self.get_sermon_permissions(user_id, item)
        if not permissions.canWrite:
            return {"message": "You don't have read permission"}
        
        i2t = ImageToText(item)
        img_url = i2t.get_slide_image_url(self.base_folder, timestamp)
        return {'image_url': img_url}


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
    

    def get_no_permission(self):
        return Permission(canRead=False, canWrite=False, canAssign=False, canUnassign=False, canAssignAnyone=False)
    
    


    def get_sermon_permissions(self, user_id:str, item:str):
        sermon = self._sm.get_sermon_metadata(user_id, item)
        if not sermon:
            return self.get_no_permission()
        
        permissions = self._acl.get_user_permissions(user_id)        
        if not permissions:
            return self.get_no_permission()
        
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
        canPublish = False
        canViewPublished = sermon.status == 'published' 
        if self._acl.get_status_order(sermon.status)  >  self._acl.get_status_order('in development'):
            canAssignAnyone = 'assign_any_item' in permissions
            if canAssignAnyone: #admin
                canAssign = False
                canUnassign = True
                canPublish = False
            elif 'assign_item' not in permissions: #reader
                canAssign = False
                canUnassign = False
                canPublish = False
            else: #editor
                if sermon.assigned_to:  
                    if user_id == sermon.assigned_to:
                        canUnassign = True
                        canAssign = False
                        canPublish =  self._acl.get_status_order(sermon.status) >= self._acl.get_status_order('ready')
                    else:
                        canUnassign = False
                        canAssign = False
                else:
                    canUnassign = False
                    canAssign = True    
        
        return Permission(canRead=canRead, canWrite=canWrite, canAssign=canAssign, canUnassign=canUnassign, 
                          canAssignAnyone=canAssignAnyone, canPublish=canPublish, canViewPublished=canViewPublished) 
    

    def assign(self, user_id:str, item:str, action:str) -> Permission: 
        sermon = self._sm.get_sermon_metadata(user_id, item) 
        permissions = self.get_sermon_permissions(user_id, item)
        if action == 'assign' and permissions.canAssign:
            sermon.assigned_to = user_id       
            sermon.assigned_to_name = self._acl.get_user(user_id).get('name')  
            sermon.status = 'assigned'  
            sermon.assigned_to_date = self._sm.convert_datetime_to_cst_string(datetime.datetime.now())

        elif action == 'unassign' and permissions.canUnassign:
            sermon.assigned_to = None
            sermon.assigned_to_name = None
            sermon.status = 'ready'
            sermon.assigned_to_date = None
        else:
            return None
        
        self._sm.save_sermon_metadata()
        

        return self.get_sermon_permissions(user_id, item)
    
    def get_bookmark(self, user_id:str, item:str):
        permissions = self.get_sermon_permissions(user_id, item)
        if not permissions.canRead:
            return  {"message": "You don't have permission to update this item"}
        
        return self._scm.get_bookmark(user_id, item)

    def set_bookmark(self, user_id:str, item:str, index:str):
        permissions = self.get_sermon_permissions(user_id, item)
        if not permissions.canWrite:
            return  {"message": "You don't have permission to update this item"}
        
        self._scm.set_bookmark(user_id, item, index)
        return {"message": "bookmark has been set"}
    
    def get_users(self):
        return self._acl.users

    def get_user_info(self, user_id:str):   
        return self._acl.get_user(user_id)


    def publish(self, user_id:str, item:str):
        permissions = self.get_sermon_permissions(user_id, item)
        if not permissions.canPublish:
            return  {"message": "You don't have permission to publish this item"}
        
        sermon = self._sm.get_sermon_metadata(user_id, item)
        sermon.status = 'published'
        sermon.published_date = self._sm.convert_datetime_to_cst_string(datetime.datetime.now())
        self._sm.save_sermon_metadata()
        ScriptDelta(self.base_folder, item).publish(sermon.assigned_to)
        return {"message": "sermon has been published"}
    
    def get_final_sermon(self, user_id:str, item:str,  remove_tags:bool = True) -> dict:
        permissions = self.get_sermon_permissions(user_id, item)
        if not permissions.canRead:
            return  {"message": "You don't have permission to update this item"}

        sermon = self._sm.get_sermon_metadata(user_id, item)
        status = sermon.status
        sd = ScriptDelta(self.base_folder, item)
        sermon_data =  sd.get_final_script( status == 'published', remove_tags)
        sermon_data['metadata']['last_updated'] = sermon.published_date if status == 'published' else sermon.last_updated            
        sermon_data['metadata']['item'] = sermon.item
        sermon_data['metadata']['title'] = sermon.title if sermon.title else sermon.item
        sermon_data['metadata']['summary'] = sermon.summary
        sermon_data['metadata']['type'] = sermon.type
        sermon_data['metadata']['deliver_date'] = sermon.deliver_date
        sermon_data['metadata']['theme'] = sermon.theme if sermon.theme else sermon.title
        sermon_data['metadata']['assigned_to_name'] = sermon.assigned_to_name
        sermon_data['metadata']['author'] = sermon.author_name if sermon.author_name else '王守仁'
        sermon_data['metadata']['status'] = sermon.status
        sermon_data['metadata']['core_bible_verse'] = sermon.core_bible_verse
        sermon_data['metadata']['keypoints'] = sermon.keypoints if sermon.keypoints else ''

        return sermon_data
    
    def get_sitemap(self):
        return self._sm.get_sitemap()

    def search_script(self, item , text_list) -> dict:
        sd = ScriptDelta(self.base_folder, item)
        return sd.search(text_list)

    def chat( self, user_id : str, item :str, history:List[ChatMessage], is_published=False ) -> str:
        permissions = self.get_sermon_permissions(user_id, item)
        if not permissions.canRead:
            return  {"message": "You don't have permission to update this item"}
        
        sermon = self._sm.get_sermon_metadata(user_id, item)
        if not sermon:
            return  {"message": "sermon not found"}
        
        sd = ScriptDelta(self.base_folder, item)
        script = sd.get_final_script(is_published)
        article = sermon.title + '\n '
        if sermon.summary: 
            article +=  '簡介：' + sermon.summary + '\n'
        article +=  '\n'.join([ f"[{p['index']}] {p['text']}" for p in script['script'] ])
        copilot = Copilot()
        docs = [Document(item=item, document_content=article)]
        return copilot.chat(docs, history)
    
    def summarize(self, title, items:List[str]) -> str:
        doc = ""
        for item in items:
            sd = ScriptDelta(self.base_folder, item)
            script = sd.get_final_script(False)
            article =  '\n\n'.join([ p['text'] for p in script['script'] ])
            doc += article + '\n\n'
        copilot = Copilot()
        history = [  ChatMessage(role='user',content='寫一段關於馬太福音 24 章簡介和講道的開場白') ]
        docs = [Document(item=title, document_content=doc)]
        return copilot.chat(docs, history)

    def save_sermon_series(self,  series_name:str, items:List[str]) -> str:
        """
        Save sermon series to the file.
        """
        doc = ""
        for item in items:
            sd = ScriptDelta(self.base_folder, item)
            script = sd.get_final_script(False)
            article =  '\n\n'.join([ p['text'] for p in script['script'] ])
            doc += article + '\n\n'
        with open(os.path.join(self.base_folder,'output', series_name +'.txt'), 'w') as f:
            f.write(doc)
        return doc

    def get_relevant_items(self, question)->set:
        url = f"{self.semantic_search_url}/semantic_search/{question}"
        response = requests.get(url)
        if response.status_code == 200:
            search_data = response.json()
            content_items = set([ d['content_id'] for d in search_data ])
            return content_items
        else:
            return set()


    def qa(self, user_id:str, history:List[ChatMessage]):        
        question = history[-1].content
        relevant_items = self.get_relevant_items(question)

        docs =[]
        for index, item in enumerate(relevant_items):
            meta = self._sm.get_sermon_metadata(user_id, item)        
            sd = ScriptDelta(self.base_folder, item)
            script = sd.get_final_script(meta.status == 'published')
            sermon = self._sm.get_sermon_metadata(user_id, item)
            article = sermon.title + '\n '
            if sermon.summary: 
                article +=  '簡介：' + sermon.summary + '\n'
                article +=  '\n'.join([ f"[{p['index']}] {p['text']}" for p in script['script'] ])
            docs.append(Document(item=item, document_content=article))
        copilot = Copilot()
        return copilot.chat(docs, history)
    
    def get_sermon_series(self):
        series_meta_file = os.path.join(self.config_folder, 'sermon_series.json')
        if not os.path.exists(series_meta_file):
            return []
        with open(series_meta_file, 'r', encoding='utf-8') as fsc:
            series_meta = json.load(fsc)
        for series in series_meta:
            sermons = []
            for item in series.get('sermons', []):
                sermon_meta = self._sm.get_sermon_metadata('junyang168@gmail.com', item)
                if sermon_meta:
                    sermons.append(sermon_meta)
            series['sermons'] = sermons
        return series_meta



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
    items = [
        '2021 NYSC 專題：馬太福音釋經（八）王守仁 教授 4之1',
        '2021 NYSC 專題：馬太福音釋經（八）王守仁 教授 4之2',
        '2021 NYSC 專題：馬太福音釋經（八）王守仁 教授 4之3',
        '2021 NYSC 專題：馬太福音釋經（八）王守仁 教授 4之4'   
    ]

    items = [
        '011WSR01',
        '011WSR02',
        '011WSR03',
        '2022年 NYSC 專題 馬太福音釋經（九）王守仁 教授  第二堂'
    ]
    resp = sermonManager.save_sermon_series('2022 NYSC 專題：馬太福音釋經（九）', items)
    print(resp)

    """
你是基督教福音派的資深基督徒。以下是週五團契的講稿。为以上讲稿生成 PPT。Slide 数量不要太多，中文用繁体。PPT 要包括讲稿中提到的圣经原文。
講稿：
    
    """


    resp = sermonManager.chat('junyang168@gmail.com', '2021 NYSC 專題：馬太福音釋經（八）王守仁 教授 4之1', [  ChatMessage(role='user',content='總結主题') ])
    print(resp)
    exit(0)
    

    sermons = sermonManager.get_sermons('junyang168@gmail.com')
    print(sermons)
    msg = sermonManager.get_sermon_detail('junyang168@gmail.com', '2019-2-15 心mp4', 'changes')
    print(msg)

    msg = sermonManager.get_sermon_detail('junyang168@gmail.com', '2019-2-15 心mp4', '')
    print(msg)


    permission = sermonManager.get_sermon_permissions('junyang168@gmail.com', '2019-2-15 心mp4')
    print('junyang', permission)
    permission = sermonManager.get_sermon_permissions('junyang168@gmail.com', '2019-4-4 神的國 ')
    print('junyang', permission)
    
    permission = sermonManager.get_sermon_permissions('jianwens@gmail.com', '2019-2-15 心mp4')
    print('jianwen', permission)
    permission = sermonManager.get_sermon_permissions('dallas.holy.logos@gmail.com', '2019-2-15 心mp4')
    print('admin', permission)
    


