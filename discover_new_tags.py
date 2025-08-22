# discover_new_tags.py
import os
import json
from pathlib import Path
from dotenv import load_dotenv
import time
from tqdm import tqdm
from collections import Counter
from llm import call_llm
from tags.sermon_content import SermonContent

# --- 1. 配置 ---
load_dotenv()

BASE_DIR = os.getenv('DATA_DIR')
SERMONS_FOLDER = f"{BASE_DIR}/sermon_content"
TAGS_FILE = f"{BASE_DIR}/config/sermon_tags.json" # 输出结果的文件名
OUTPUT_FILE = f"{BASE_DIR}/config/discovered_tags.json" # 输出结果的文件名

# --- 2. 构建开放式 Prompt ---
SYSTEM_PROMPT = """
你是一位精通圣经神学的基督教福音派神学分析家，拥有极强的概念抽象和提炼能力。你的任务是阅读一段讲道文稿，并从中提炼出其核心的神学概念或主题。

# 任务指令:
1.  请仔细阅读下面提供的“讲道文稿片段”。
2.  每个主题请使用一个简洁、精炼、具有普遍性的神学术语来描述（例如：“因信成义”，而不是“关于如何得救的讨论”,"释经学",而不是”聖經詮釋學“）。
3.  你的回答必须是一个 Python 列表格式的 JSON 字符串。例如：["三位一体", "道成肉身", "神的护理"]
4.  请自由发挥你的神学知识，提炼出你认为最合适的术语，无需遵循任何预设列表。
5.  如果文稿片段内容过于简短或没有明确的神学主题，请返回一个空列表：[]
6.  不要添加任何额外的解释或评论，只返回 JSON 列表。
7.  所有主題盡量使用繁體中文

---
# 讲道文稿片段:
"""

# --- 3. 调用 Gemini API 的函数 ---
def discover_tags_for_chunk(chunk_text: str):
    """
    为单个文本块调用 Gemini API 并返回建议的标签列表。
    """
    if not chunk_text or len(chunk_text.split()) < 30: # 稍微提高门槛
        return []
        
    try:
        provider = os.getenv('PROVIDER')
        full_prompt = SYSTEM_PROMPT + chunk_text
        tags = call_llm(provider, full_prompt)

        # 对返回的标签进行清洗，例如去除多余空格
        return [tag.strip() for tag in tags if isinstance(tag, str) and tag.strip()] if isinstance(tags, list) else []

    except Exception as e:
        print(f"\n调用 API 时发生错误: {e}")
        return None

# --- 4. 主处理流程 ---
def main():
    print("🚀 开始探索性地生成新的神学标签...")
    
    sermon_files = list(Path(SERMONS_FOLDER).glob("*.json"))
    if not sermon_files:
        print(f"⚠️ 在 '{SERMONS_FOLDER}' 中未找到 JSON 文件。")
        return

    all_discovered_tags = []

#    sermon_files = ['/Users/junyang/church/web/data/sermon_content/2021 NYSC 專題：馬太福音釋經（八）王守仁 教授 4之1.json']

    sermon_tags = {}

    for file_path in tqdm(sermon_files, desc="分析讲道文件"):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                sermon = json.load(f)
        except json.JSONDecodeError:
            print(f"\n警告: 文件 {file_path.name} 格式错误，已跳过。")
            continue

        if 'script' in sermon and isinstance(sermon['script'], list):
            chunk_text = "\n\n".join([p.get('text', '') for p in sermon['script']])
            retries = 3
            while retries > 0:
                tags = discover_tags_for_chunk(sermon['metadata']['title'] + '\n\n' + chunk_text)
                if tags is not None:
                    all_discovered_tags.extend(tags)
                    sermon_id = sermon['metadata']['item']
                    sermon_tags[sermon_id] = tags
                    with open(TAGS_FILE, 'w', encoding='utf-8') as f:
                        json.dump(sermon_tags, f, ensure_ascii=False, indent=2)
                    time.sleep(1)
                    break
                else:
                    retries -= 1
                    print(f"\n文件 {file_path.name} 的某个片段生成失败，正在重试...")
                    time.sleep(5)
    
    # --- 5. 统计和保存结果 ---
    if not all_discovered_tags:
        print("\n未能发现任何标签。")
        return

    print(f"\n🔍 AI 总共提出了 {len(set(all_discovered_tags))} 个独特的标签建议。")


    # 使用 Counter 统计每个标签的出现频率
    tag_counts = Counter(all_discovered_tags)
    
    # 将结果转换为一个按频率降序排序的列表
    sorted_tags = sorted(tag_counts.items(), key=lambda item: item[1], reverse=True)
    
    # 格式化为更易读的 JSON 对象
    output_data = {
        "total_unique_tags": len(sorted_tags),
        "tag_frequencies": dict(sorted_tags)
    }

    try:
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=4)
        print(f"\n✅ 结果已成功保存到 '{OUTPUT_FILE}' 文件中。")
        print("下一步：请与同工团队一起审核此文件，以建立或扩充您的官方标签体系。")
    except Exception as e:
        print(f"\n写入结果文件时发生错误: {e}")




if __name__ == "__main__":
    main()