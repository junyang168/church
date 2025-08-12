
import json
from llm import call_llm


def get_sermon_content(sermon_meta: dict)-> str:
    item = sermon_meta['item'] 
    url = "http://127.0.0.1:8000/sc_api/final_sermon/junyang168@gmail.com/" 
    response = requests.get(url + item)
    sermon_detail = response.json()

    paragraphs = sermon_detail['script']

    theme = sermon_meta['theme'] if sermon_meta['theme'] else sermon_meta['title']

    article = theme + '\n\n' + '\n\n'.join( [ p['text'] for p in paragraphs ] )
    return article

def get_series_content(all_sermons_meta: dict, series_items: list[str]) -> str:
    articles = []
    for index, item in enumerate(series_items):
        sermon_meta = next((s for s in all_sermons_meta if s['item'] == item), None)
        article = get_sermon_content(sermon_meta)
        articles.append(f"#第{index + 1}講：{article}")
    return "\n\n".join(articles)


from typing import List
from google import genai
from google.genai import types
import os


def get_summary( article: str):
    json_format = """
    ```json
    {
        "title":"空坟墓",
        "topics": "耶稣复活",
        "summary": "通过分析历史文献和圣经记载，强调耶稣的空坟墓是复活的关键证据。指出犹太传说与福音书记载的一致性，以及罗马兵丁的证词矛盾，反驳了门徒偷尸体的说法，论证了复活的历史真实性。",
        "keypoints": "1. 觀點 1，\n 2. 觀點 2，\n 3. 觀點 3"
    }
    ```
    """

    ai_prompt = f"""请給下面基督教福音派教授的講道加標題,然後写一个简洁的摘要，最後指出主题詞和主要观点。注意：
    1. 不要為系列中的每一篇講道加標題，只需要為整個系列加標題。
    2. 標題要简洁
    3. 摘要先点出主题，再加核心内容。简介不要超过 1000 字。
    4. 主题词簡介。如果有多個主题词，请用逗号分隔。
    5. 使用繁體中文
    回答符合以下JSON格式:
    {json_format}
    牧师讲道内容：{article}
    """              
    provider = os.getenv("PROVIDER")

    summary =  call_llm(provider, ai_prompt)
    return summary

def create_series(all_sermons_meta: dict, series_items: list[str], series_name: str) -> str:
    base_dir = '/Users/junyang'
    with open( base_dir + '/church/web/data/config/sermon_series.json', 'r', encoding='utf-8') as f:
        series_meta_data = json.load(f)
    series = next((s for s in series_meta_data if s['id'] == series_name), None)
    if series is None:
        series = {'id': series_name,  'sermons': series_items}
        series_meta_data.append(series)
    else:
        return series
#        series['sermons'] = series_items
    
    series_content = "#" + series_name + ' 系列\n\n'
    series_content += get_series_content(all_sermons_meta, series_items)
    with open(base_dir + f'/church/web/data/sermon_series/{series_name}.txt', 'w', encoding='utf-8') as f:
        f.write(series_content)
    sp = get_summary(series_content)
    series['summary'] = sp['summary']
    series['topics'] = sp['topics']
    series['title'] = sp['title']
    series['keypoints'] = sp['keypoints']

    with open(base_dir + '/church/web/data/config/sermon_series.json', 'w', encoding='utf-8') as f:
        json.dump(series_meta_data, f, ensure_ascii=False, indent=4)
        
    return series    

if __name__ == '__main__':
    import requests
    import time    
    base_folder = '/opt/homebrew/var/www/church/web/data'  
    meta_file_name = base_folder + '/config/' + 'sermon.json'

    with open(meta_file_name, 'r') as fsc:
        all_sermons_meta = json.load(fsc)

    series_items = [
        "S 200913 林前1 教會的身份",
        "S 200920 林前1 10-31教會的合一",
        "S 200927 林前2 1-16 福音與智慧",
        "S 201004 林前2 聖靈傳遞神的智慧",
        "S 201011 林前2 屬靈人看透",
        "S 201018 林前3 正確認識神的僕人",
        "S 201025",
        "S 201101",
        "S 201108",
        "S 201115",
        "S 201122",
        "S 201129",
        "S 201206",
        "S 201227",
        "S 210103",
        "S 210110",
        "S 210117",
        "S 210124",
        "S 210131",
        "S 210207",
        "S 210214",
        "S 210221",
        "S 210228",
        "S 210307",
        "S 210314",
        "S 210321",
        "S 210328",
        "S 210411",
        "S 210418",
        "S 210425",
        "S 210502"
    ]
    series_name = "哥林多前書 釋經​"
    create_series(all_sermons_meta, series_items, series_name)

    exit()


    series_items = [
        "S 200426",
        "S 200503",
        "S 200510",
        "S 200517",
        "S 200524"
    ]
    series_name = "馬太福音24 章 釋經"
    create_series(all_sermons_meta, series_items, series_name)

    series_items = [
        "2021 NYSC 專題：馬太福音釋經（八）王守仁 教授 4之1",
        "2021 NYSC 專題：馬太福音釋經（八）王守仁 教授 4之2",
        "2021 NYSC 專題：馬太福音釋經（八）王守仁 教授 4之3",
        "2021 NYSC 專題：馬太福音釋經（八）王守仁 教授 4之4"
    ]
    series_name = "2021 NYSC 專題：馬太福音釋經（八)"
    create_series(all_sermons_meta, series_items, series_name)

    series_items = [
        "011WSR01",
        "011WSR02",
        "011WSR03",
        "2022年 NYSC 專題 馬太福音釋經（九）王守仁 教授  第二堂"
    ]
    series_name = "2021年 NYSC 專題：馬太福音釋經（九）"
    create_series(all_sermons_meta, series_items, series_name)
