from typing import List, Union, Optional
from pydantic import BaseModel
import json
import os


class QAItem(BaseModel):
    id:str
    question: str
    shortAnswer: str
    fullAnswerMarkdown: str
    category: Optional[str] = None
    relatedScriptures : Optional[List[str]] = None
    createdAt: str = None
    isVerified: bool = False
    related_article: Optional[str] = None



class QAManager:

    def __init__(self) -> None:
        api_folder = os.path.dirname(os.path.abspath(__file__))
        self.base_folder = os.path.join(api_folder, '..', 'data')
        self.load_qas()


    def get_file_path(self) -> str:
        return os.path.join(self.base_folder, 'qa', "FaithQA.json")

    def save_qas(self):
        path = self.get_file_path()
        with open(path, "w",encoding="utf-8") as f:
            json.dump([qa.dict() for qa in self.qas], f, indent=2,ensure_ascii=False)

    def toQA_Item(self, data) -> QAItem:
        return QAItem(**data) if type(data) == dict else data

    def add_qa(self, user_id: str, qa_item: QAItem) -> QAItem:                
        qa_item.id = str(len(self.qas) + 1)
        new_qa_item = self.toQA_Item(qa_item)
        self.qas.append(new_qa_item)
        self.save_qas()
        return new_qa_item

    def get_qas(self, user_id: str) -> List[QAItem]:
        return self.qas

    def get_qa_by_id(self, user_id: str, qa_id: str) -> Optional[QAItem]:
        for item in self.qas:
            if item.id == qa_id:
                return item
        return None

    def load_qas(self):
        try:
            with open(self.get_file_path(), "r",encoding="utf-8") as f:
                data = json.load(f)
                self.qas = [self.toQA_Item(item) for item in data]
        except FileNotFoundError:
            self.qas = []
        except json.JSONDecodeError:
            self.qas = []

    def update_qa(self, user_id: str, qa_item: QAItem) -> QAItem:
        qa_item = self.toQA_Item(qa_item)
        for i, item in enumerate(self.qas):
            if item.id == qa_item.id:
                self.qas[i] = qa_item
                self.save_qas()
                return qa_item
        self.qas.append(qa_item)
        self.save_qas()
        return qa_item

    def delete_qa(self, qa_id: str):
        self.qas = [item for item in self.qas if item['id'] != qa_id]
        self.save_qas()
        return {"message": "QA item deleted successfully"}

qaManager = QAManager()

if __name__ == "__main__":
    item = QAItem(
        id="new-",
        question="What is faith?",
        shortAnswer="Faith is belief in something.",
        fullAnswerMarkdown="Faith is a deeply held belief in something, often without empirical evidence.",
        category="Theology",
        relatedScriptures=["Hebrews 11:1"],
    )
    item = qaManager.add_qa("junyang168@gmail.com", item)
    print(item)
