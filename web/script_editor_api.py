from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List

import json
import os
<<<<<<< HEAD
=======
from dotenv import load_dotenv
load_dotenv()
import sermon_manager as sm

>>>>>>> 529357f (access control, index page styled with tailwind. fixed script fixed issue)

class Paragraph(BaseModel):
    index:str
    text: str

class UpdateRequest(BaseModel):
    user_id:str = None
    item:str
    paragraphs: List[Paragraph]

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

<<<<<<< HEAD
@app.get("/api/load/{type}/{item}/{ext}")
def load(type:str, item: str, ext:str='txt')->str: 
=======
def save_to_s3(file_path: str, bucket_name: str, object_key: str, author:str):
    # Load the environment variables from .env file

    # Get the AWS access key and secret key from environment variables
    aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID")
    aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")

    # Use the access key and secret key in the save_to_s3 function
    s3 = boto3.client('s3', aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key)
    s3.upload_file(file_path, bucket_name, object_key, ExtraArgs={'Metadata': {'author': author}})

@app.get("/api/load/{user_id}/{type}/{item}/{ext}")
def load(user_id:str, type:str, item: str, ext:str='txt')->str: 
    permissions = sm.sermonManager.get_sermon_permissions(user_id, item)
    if not permissions.canRead:
        return "You don't have permission to read this item"
>>>>>>> 529357f (access control, index page styled with tailwind. fixed script fixed issue)
    file_path = get_file_path(type, item, '.' + ext)
    with open(file_path, "r") as file:
        data = file.read()
    return data

@app.post("/api/update_script")
<<<<<<< HEAD
def update_script(paragraphs: UpdateRequest):
=======
def update_script(request: UpdateRequest):
    permissions = sm.sermonManager.get_sermon_permissions(request.user_id, request.item)
    if not permissions.canWrite:
        return {"message": "You don't have permission to update this item"}
>>>>>>> 529357f (access control, index page styled with tailwind. fixed script fixed issue)

    file_path = get_file_path('script_fixed', paragraphs.item)

    with open(file_path, "w") as file:
<<<<<<< HEAD
        new_script_fixed = '\n\n'.join([f"{p.text}[{p.index}]" for p in paragraphs.paragraphs])
        file.write(new_script_fixed)
=======
        if request.type == 'slides':
            json.dump([{'time': p.time, 'text': p.text} for p in request.data], file)
        else:            
            new_script_fixed = '\n\n'.join([f"{p.text}[{p.index}]" for p in request.data])
            file.write(new_script_fixed)

    save_to_s3(file_path, 'dallas-holy-logos', folder + '/' + request.item + '.txt', request.user_id)

    return {"message": f"{request.type} updated successfully"}

@app.get("/api/permissions/{user_id}/{item}")
def get_permissions(user_id:str,item:str) -> sm.Permission:
    return sm.sermonManager.get_sermon_permissions(user_id, item)

@app.get("/api/surmons/{user_id}")
def get_surmons(user_id:str) -> List[sm.Sermon]:
    return sm.sermonManager.get_surmons(user_id)
>>>>>>> 529357f (access control, index page styled with tailwind. fixed script fixed issue)

    return {"message": "Paragraph updated successfully"}

if __name__ == "__main__":
<<<<<<< HEAD
=======
#    save_to_s3(get_file_path('script_fixed', '2019-2-15 心mp4'), 'dallas-holy-logos', 'script_fixed/2019-2-15 心mp4.txt', 'junyang168@gmail.com')
>>>>>>> 529357f (access control, index page styled with tailwind. fixed script fixed issue)
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
