import json
import os
from openai import OpenAI
from pydantic import BaseModel
from typing import List
from image_to_text import ImageToText
import xml.etree.ElementTree as ET

class ChatMessage(BaseModel):
    role: str
    content: str

from pydantic import BaseModel
from typing import List,Optional



class Reference(BaseModel):
    Id : str
    Title: Optional[str] = None
    Link : Optional[str] = None
    Index : str

class ChatResponse(BaseModel):
    quotes: List[Reference]
    answer: Optional[str] = None


class Copilot:
    def map_prompt(self, question:str) -> str:
        if question == "總結主题":
            return """总结下面牧师讲道的主要观点.回答以下格式例子：
        主题
        1. 观点 1
        2. 观点 2""", "deepseek-reasoner"        
        else:
            return question, "deepseek-chat"
    


    def parse_quotes(self, quotes) -> List[Reference]:
        if quotes is None:
            return []
        results = []
        for q in quotes:
            for child in q:
                if child.tag == 'para_index':
                    index = child.text
                elif child.tag == 'text':
                    text = child.text
            results.append( Reference(Id=q.attrib['index'], Title=text, Link=q.attrib['source'], Index=index) )
        return results


    def parse_response(self, response:str) -> dict:
        root = ET.fromstring("<root>" + response + "</root>")
        quotes = root.findall('.//quotes/quote')
        quotes = self.parse_quotes(quotes)
        answer_node = root.find('.//answer')
        return ChatResponse(quotes=quotes, answer=answer_node.text if answer_node is not None else None)

        
    def chat(self, item:str,  sermon:str, history: List[ChatMessage]) -> str:
        question = history[-1].content
        prefix = "提取文字 at "
        if question.startswith(prefix):
            i2t = ImageToText(item)
            timestamp = int(question[len(prefix):])
            res = i2t.extract_slide(timestamp)
            return ChatResponse(quotes=[], answer=res)
        else:
            history[-1].content, model = self.map_prompt( question )
            
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
            
#            res = '<quotes>\n    <quote index=\'1\' source=\'/article?i=2019-05-19 喜乐\'>\n        <text>良心需以圣经真理为校准标准，而非单纯依赖主观感受</text>\n        <para_index>1_10-1_24</para_index>\n    </quote>\n    <quote index=\'2\' source=\'/article?i=2019-05-19 喜乐\'>\n        <text>基督徒行为的核心原则是"不叫人跌倒"</text>\n        <para_index>1_193-1_227</para_index>\n    </quote>\n    <quote index=\'3\' source=\'/article?i=2019-05-19 喜乐\'>\n        <text>良心的衡量标准需要与圣经真理校对方可靠</text>\n        <para_index>3_398-3_413</para_index>\n    </quote>\n</quotes>\n<answer>\n主题：基督徒良心的正确运用与圣经真理的关系\n\n1. 传统教会教导"凭良心平安行事"的观点与圣经真理相冲突，良心必须以圣经真理为校准标准，而非单纯依赖主观感受[1]。\n2. 基督徒行为的核心原则是"不叫人跌倒"，这体现在处理吃祭偶像之物等具体问题上需要根据圣经原则灵活应用[2]。\n3. 良心的作用包括衡量能力（神所赐）和衡量标准（受文化教育影响），必须通过深度解经使良心标准与圣经真理一致才能可靠运用[3]。\n</answer>'
#            return self.parse_response(res)

            client = OpenAI(
                    api_key=os.getenv("DEEPSEEK_API_KEY"),  
                    base_url="https://api.deepseek.com"
                )
            response = client.chat.completions.create(
                model=model,
                messages=messages
            )
            res =  response.choices[0].message.content
        return  self.parse_response(res) 


    def __init__(self):
        self.system_prompt = """你是資深的基督教牧師。現在要回答與下面講道相關的問題。回答符合講道的聖經觀點。
1. 下面提供了幾篇相關的講道。講道的每個段落前都有一個索引號碼。（例如[1]或[1_1])
2. 回答問題時，應將答案放在<answer></answer>標籤中。不要直接引用或逐字重複引文內容。回答時，不要說“根據Quote 1”。若答案中某部分與特定引文相關，在回答每個相關部分的句子末尾，僅透過添加帶括號的數字來引用相關的引文。（例如：這是一個示例句子[1]。）
3. 從講道中找出與回答問題最相關的引文。將引文按編號順序放在<quotes></quotes> 的<text></text>標籤中，引文應相對簡短。講道文章source放在<quote>的<source>標籤中. 
4. 引用段落的索引號碼應放在<quote>的<para_index>標籤中。索引號碼應該是講道的段落索引號碼，這些索引號碼應該與講道內容中的段落索引號碼相對應。
4. The format of your overall response should look like what’s shown between the examples></examples> tags. Make sure to follow the formatting and spacing exactly. If the question cannot be answered by the document, say so.
<examples>
	<quotes>
		<quote index='1' source='http://localhost:8000/public/2019-05-19 喜乐'>
			<text>保羅說，A.如果你吃祭偶像的東西，參與祭偶像，就不可以吃。</text>
			<para_index>1_1-1_3</para_index>
	</quote>
	<quote index='2 source='http://localhost:8000/public/2019-05-19 喜乐'>
		<text>所以保羅說你們只管吃，不要為良心的緣故問什麼話</text>
		<para_index>2_1-2_3</para_index>
	</quote>
</quotes>
<answer>

讲道内容:
<document index="1">
    <source>/article?i=2019-05-19 喜乐</source>
    <document_content>{context_str}</document_content>
</document>


请开始对话："""


if __name__ == "__main__":
    copilot = Copilot()
    ans = copilot.chat('2019-05-19 喜乐', '2019-05-19 喜乐', [ChatMessage(role='user', content='Get Quote: 1_1-1_3')])
    print(ans)