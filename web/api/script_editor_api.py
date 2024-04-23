from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List

import json
import os

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

@app.get("/api/load/{type}/{item}/{ext}")
def load(type:str, item: str, ext:str='txt')->str: 
    file_path = get_file_path(type, item, '.' + ext)

    with open(file_path, "r") as file:
        data = file.read()
    return data

@app.post("/api/update_script")
def update_script(paragraphs: UpdateRequest):

    file_path = get_file_path('script_fixed', paragraphs.item)

    with open(file_path, "w") as file:
        new_script_fixed = '\n\n'.join([f"{p.text}[{p.index}]" for p in paragraphs.paragraphs])
        file.write(new_script_fixed)

    return {"message": "Paragraph updated successfully"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
