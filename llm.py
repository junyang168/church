
from openai import OpenAI
import os
import json
import math
from together import Together
from groq import Groq
from google import genai
from google.genai import types

def markdown_to_json(markdown: str, is_json: bool = False) -> dict:
    """Convert markdown-formatted JSON string to Python dictionary.
    
    Args:
        markdown: String containing JSON wrapped in markdown code block
        
    Returns:
        Parsed dictionary from JSON content
    """    
    json_tag = "```json"
    start_idx = markdown.find(json_tag)
    if start_idx < 0:
        return json.loads( markdown )
    
    end_idx = markdown.find("```", start_idx + len(json_tag))
    if end_idx == -1:
        raise ValueError("No closing code block found in markdown")
    json_str = markdown[start_idx + len(json_tag):end_idx].strip()
    json_str = json_str.replace("\\'", "'")
    return json.loads(json_str)

def gemini_generate(prompt: str):
    client = genai.Client(
#        api_key=os.environ.get("GEMINI_API_KEY"),
    )

    model = "gemini-2.5-pro"
    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_text(text=prompt),
            ],
        ),
    ]
    generate_content_config = types.GenerateContentConfig(
        thinking_config = types.ThinkingConfig(
            thinking_budget=-1,
        ),
        response_mime_type="application/json",
    )
    
    response =  client.models.generate_content(
        model=model,
        contents=contents,
        config=generate_content_config,
    )
#    print(response.usage_metadata)
    return response.text

def call_llm(provider:str, ai_prompt:str,  model:str = None) -> dict:
    if provider == 'gemini':
        resp = gemini_generate(ai_prompt)
        return json.loads(resp)

    if provider == 'together':        
        client = Together()
        if model is None:
            model="deepseek-ai/DeepSeek-R1"
    elif provider == 'groq':
        client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        model = "qwen-qwq-32b"
    elif provider == 'aliyun':
        if model is None:
            model="deepseek-r1"
        client = OpenAI(
            api_key=os.getenv("DASHSCOPE_API_KEY"),  # 如何获取API Key：https://help.aliyun.com/zh/model-studio/developer-reference/get-api-key
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
        )
    elif provider == 'deepseek':
        if model is None:
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
    return markdown_to_json(res)
