import json
import os
from openai import OpenAI
from pydantic import BaseModel
from typing import List

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
        
    def chat(self, sermon:str, history: List[ChatMessage]) -> str:
        history[-1].content = self.map_prompt( history[-1].content )
        
        messages = [
            {
                "role": "system", 
                "content":self.system_prompt.format(context_str=sermon)
             }  
        ]
        for msg in history:
            if msg.role == 'user':
                messages.append({"role": "user", "content": msg.content})
            elif msg.role == 'assistant':
                messages.append({"role": "bot", "content": msg.content})

        messages.extend(history)
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
