import json
import os
from openai import OpenAI
from pydantic import BaseModel
from typing import List
from image_to_text import ImageToText

class ChatMessage(BaseModel):
    role: str
    content: str



class Copilot:
    def map_prompt(self, question:str) -> str:
        if question == "總結主题":
            return """总结下面牧师讲道的主要观点.回答以下格式例子：
        主题
        1. 观点 1
        2. 观点 2"""
        else:
            return question
        
    def chat(self, item:str,  sermon:str, history: List[ChatMessage]) -> str:
        question = history[-1].content
        prefix = "提取文字 at "
        if question.startswith(prefix):
            i2t = ImageToText(item)
            timestamp = int(question[len(prefix):])
            res = i2t.extract_slide(timestamp)
        else:
            history[-1].content = self.map_prompt( question )
            
            messages = [
                {
                    "role": "system", 
                    "content":self.system_prompt.format(context_str=sermon)
                }  
            ]
            # Add the history messages ignoring text extraction
            i = 0
            while i < len(history):
                msg = history[i]
                if msg.role =='user' and msg.content.startswith(prefix) :
                    i += 1
                else:
                    if msg.role in [ 'user','assistant' ]:
                        messages.append({"role": msg.role , "content": msg.content})
                i += 1
            
#            return "**你是一个资深的基督教牧师。你现在要回答与下面讲道有关的问题. \n 1. 回答符合讲道的圣经观点\n2. 回答直接引用讲道的内容\n3. 遇到以下情况时明确说明：\n   - 资料未提及 → \"根据现有资料无法回答该问题\"\n   - 信息冲突 → \"不同资料中存在以下观点：...\"\n4. 禁止任何推测和编造\n\n讲道内容:开始对话："
            model='deepseek-chat'
            client = OpenAI(
                    api_key=os.getenv("DEEPSEEK_API_KEY"),  
                    base_url="https://api.deepseek.com"
                )
            response = client.chat.completions.create(
                model=model,
                messages=messages
            )
            res =  response.choices[0].message.content
        return  res 


    def __init__(self):
        self.system_prompt = """你是一个资深的基督教牧师。你现在要回答与下面讲道有关的问题. 
Follow these rules:
1. 回答符合讲道的圣经观点
2. 回答直接引用讲道的内容
3. 遇到以下情况时明确说明：
   - 资料未提及 → "根据现有资料无法回答该问题"
   - 信息冲突 → "不同资料中存在以下观点：..."
4. 禁止任何推测和编造

讲道内容:
{context_str}

请开始对话："""
