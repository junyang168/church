
from openai import OpenAI
import os
import json
import math
from together import Together
from groq import Groq

def call_llm(provider:str, ai_prompt:str):
    if provider == 'together':        
        client = Together()
        model="deepseek-ai/DeepSeek-R1"
    elif provider == 'groq':
        client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        model = "qwen-qwq-32b"
    elif provider == 'aliyun':
        model="deepseek-r1"
        client = OpenAI(
            api_key=os.getenv("DASHSCOPE_API_KEY"),  # 如何获取API Key：https://help.aliyun.com/zh/model-studio/developer-reference/get-api-key
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
        )
    elif provider == 'deepseek':
        model='deepseek-reasoner'
        client = OpenAI(
            api_key=os.getenv("DEEPSEEK_API_KEY"),  
            base_url="https://api.deepseek.com"
        )
    else:
        raise ValueError(f"Invalid provider: {provider}")
    response = client.chat.completions.create(
        model=model,
        messages=[        
            {
                "role": "user",
                "content": ai_prompt
            }
        ]
    )
    res = response.choices[0].message.content
    return res
