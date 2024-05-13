from fastapi import Depends, FastAPI, Response
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
from fastapi.responses import HTMLResponse
import sermon_meta 

import mistune

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

class SearchRequest(BaseModel):
    item:str
    text_list:List[str]


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


@app.get("/api/sermon/{user_id}/{item}/{changes}")
def get_sermon(user_id:str, item: str, changes:str = None): 
    return sm.sermonManager.get_sermon_detail(user_id,item,changes)

@app.get("/api/permissions/{user_id}/{item}")
def get_permissions(user_id:str,item:str) -> sm.Permission:
    return sm.sermonManager.get_sermon_permissions(user_id, item)

@app.get("/api/sermons/{user_id}")
def get_sermons(user_id:str) -> List[sm.Sermon]:
    return sm.sermonManager.get_sermons(user_id)


@app.post("/api/assign")
def assigned_to(req: AssignRequest):
    return sm.sermonManager.assign(req.user_id, req.item,req.action)

@app.get("/api/bookmark/{user_id}/{item}")
def get_bookmark(user_id:str, item:str):
    return sm.sermonManager.get_bookmark(user_id, item)

@app.put("/api/bookmark/{user_id}/{item}/{index}")
def set_bookmark(user_id:str, item:str, index:str):
    return sm.sermonManager.set_bookmark(user_id, item, index)

@app.get("/api/users")
def get_users():
    return sm.sermonManager.get_users()

@app.put("/api/publish/{user_id}/{item}")
def publish(user_id:str, item:str):
    return sm.sermonManager.publish(user_id, item)

@app.get("/api/final_sermon/{user_id}/{item}/{published}")
def get_sermon(user_id:str, item: str, published:str = None): 
    return sm.sermonManager.get_final_sermon(user_id,item,published)


from fastapi.staticfiles import StaticFiles

static_dir = os.path.join( os.path.dirname(os.path.abspath(__file__)) ,'static')

app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/public/sitemap")
def get_sitemap():
    sitemapXml = sm.sermonManager.get_sitemap()
    return Response(content=sitemapXml, media_type="application/xml")


@app.get("/public/{item}", response_class=HTMLResponse)
def get_sermon_page(item):
    sermon_data = sm.sermonManager.get_final_sermon('junyang168@gmail.com',item,'published')
    metadata = sermon_data['metadata']
    script = sermon_data['script']

    with open( static_dir +  '/template.html', 'r') as file:
        template = file.read()

    html = '\n\n'.join([ f"<p class='py-2' id='{p['start_index']}'>{mistune.markdown(p['text'])}</p>" for p in script])
#    html = mistune.markdown(script_md)

    return template.format(title=metadata.get('title'), html=html)
    

@app.post("/api/search")
def search_script( req : SearchRequest):
    return sm.sermonManager.search_script(req.item, req.text_list)
    



if __name__ == "__main__":
#    save_to_s3(get_file_path('script_review', '2019-2-15 心mp4'), 'dallas-holy-logos', 'script_fixed/2019-2-15 心mp4.txt', 'junyang168@gmail.com')
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
