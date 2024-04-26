from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Union
import boto3
import json
import os
from dotenv import load_dotenv
load_dotenv()
import sermon_manager as sm
from script_delta import ScriptDelta


class Paragraph(BaseModel):
    index:str
    text: str

class Slide(BaseModel):
    time:int
    text:str

class UpdateRequest(BaseModel):
    user_id:str = None
    item:str
    type:str
    data: List[Union[Slide, Paragraph]] 

class AssignRequest(BaseModel):
    user_id:str
    item:str
    action:str


app = FastAPI()
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_file_path(type:str, item:str, ext:str='.txt'):
    api_folder = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(api_folder, '..', f"data/{type}/{item}{ext}")


@app.get("/api/load/{user_id}/{type}/{item}/{ext}")
def load(user_id:str, type:str, item: str, ext:str='txt')->str: 
    permissions = sm.sermonManager.get_sermon_permissions(user_id, item)
    if not permissions.canRead:
        return "You don't have permission to read this item"
    file_path = get_file_path(type, item, '.' + ext)
    with open(file_path, "r") as file:
        data = file.read()
    return data

@app.post("/api/update_script")
def update_script(request: UpdateRequest):
    return sm.sermonManager.update_sermon(request.user_id, request.type, request.item, request.data)

<<<<<<< HEAD

@app.get("/api/sermon/{user_id}/{item}/{changes}")
def get_sermon(user_id:str, item: str, changes:str = None): 
    return sm.sermonManager.get_sermon_detail(user_id,item,changes)
=======
    folder = 'slide' if request.type == 'slides' else 'script_patched'

    file_path = get_file_path(folder, request.item, '.json')

    with open(file_path, "w") as file:
        data_dicts = [p.dict() for p in request.data]
        json.dump(data_dicts, file)    
        
    save_to_s3(file_path, 'dallas-holy-logos', folder + '/' + request.item + '.json', request.user_id)

    return {"message": f"{request.type} updated successfully"}
>>>>>>> 27c710a (add patch processor to fix data issue. add status)

@app.get("/api/permissions/{user_id}/{item}")
def get_permissions(user_id:str,item:str) -> sm.Permission:
    return sm.sermonManager.get_sermon_permissions(user_id, item)

@app.get("/api/sermons/{user_id}")
def get_sermons(user_id:str) -> List[sm.Sermon]:
    return sm.sermonManager.get_sermons(user_id)


@app.post("/api/assign")
def assigned_to(req: AssignRequest):
    return sm.sermonManager.assign(req.user_id, req.item,req.action)



if __name__ == "__main__":
#    save_to_s3(get_file_path('script_review', '2019-2-15 心mp4'), 'dallas-holy-logos', 'script_fixed/2019-2-15 心mp4.txt', 'junyang168@gmail.com')
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
