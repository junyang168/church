import openai


file1 = open('/Users/junyang/church/data/script_processed.txt', 'r')
txt = file1.read()
file1.close()

chunk_index = 0
chunk_size = 2048

processed_text = ''

file2 = open('/Users/junyang/church/data/script_processed2.txt', 'w')
while chunk_index < len(txt):
    chunk = txt[chunk_index: chunk_index + chunk_size]
    if len(chunk) == chunk_size:
        last_para_indx = chunk.rfind('\n') + 1
        chunk = chunk[:last_para_indx]
        chunk_index += last_para_indx
    else:
        chunk_index = len(txt)

    prompt = f"""
你是圣经专家，请改正下面基督教牧师的讲道中提到的圣经经文章节名称，和圣经中人物名字。除此之外，不要做任何改动
例如：天上羅尼迦前世五章二十三節改为帖撒罗尼迦5章23节，耶華改为耶和华。
请使用中文繁体回答，格式为Markdown

{chunk}
    """

    response = openai.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.5,
        max_tokens=4000,
        top_p=1.0,
        frequency_penalty=0.0,
        presence_penalty=0.0
    )

    msg = response.choices[0].message.content
    file2.write( msg)
    file2.flush()

file2.close()