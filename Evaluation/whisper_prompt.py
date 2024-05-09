from openai import OpenAI
client = OpenAI()
import json

#audio_file = open("/Users/junyang/church/data/2019-2-18-sample_2.mp3", "rb")
#audio_file = open("/Users/junyang/church/web/data/audio/2019-4-14 罗4 1-25 因信成义_1.mp3",'rb')

#file_name = "/Users/junyang/church/web/data/2019-2-18-sample.mp3"
file_name = '/Users/junyang/church/data/2019-2-18-sample__3_min.mp3'
audio_file = open(file_name,'rb')

text = "我們今天從聖經裡面看到良心的問題。平常在很多教會裡面，大家已經聽很多次，常常講到的不是說，你要做一件事，你一件事去禱告，你禱告完了之後，你良心平安就去做，良心不平安就不要做。這是在教會裡面傳統的教導。可是這種說法跟聖經講的衝突，聖經並沒有說，你要做什麼事，你去禱告，你禱告完了以後，良心平安你就做，良心不平安就不要做，其實沒有這些事。我們從聖經來看，保羅在**哥林多前書**第八章到第十章，更多教會的人問保羅，君主是不是可以吃祭過偶像的東西。保羅來處理這個問題的時候，保羅就談到良心的問題。所以我們要談到良心，這些問題的時候，就要看聖經裡面所教導的是什麼。所以我們先來看，保羅對基督徒，外邦的基督徒，吃祭偶像的東西，他的教導到底是什麼。保羅來教導這件事的時候，他有機會談到良心的問題，所以我們先來看，更多前書第十章十字節到二十二節。 "
print(text[133:])

def parse_srt(self, file_name, file_content):
    # Split the content by double newlines
    segmentgs = file_content.strip().split('\n\n')

    data = []
    for segment in segmentgs:
        # Split the section into lines
        lines = segment.split('\n')

        # The first line is the index
        index = int(lines[0])

        # The second line is the time range
        time_range = lines[1]
        start_time, end_time = time_range.split(' --> ')

        # The remaining lines are the text
        text = ' '.join(lines[2:])

        # Add the data to the list
        data.append({
            'index': self.get_index_id(file_name, index),
            'start_time': start_time,
            'end_time': end_time,
            'text': text,
        })

    return data

bible_terms = '哥林多前書 基督徒 詩篇 以弗所書 腓立比書 教會 祭偶像 羅馬書 新約 舊約 使徒行傳 傳福音 摩西律法 受割禮 聖靈 誡命 使徒 安息日 獻祭 传福音 侍奉 耶穌復活 雅各 猶太人 提摩太後書 提摩太前書 因信稱義 以賽亞 義人 亞伯拉罕 '

transcription = client.audio.transcriptions.create(
    model="whisper-1", 
    file=audio_file,
    response_format='text',
    prompt="生于忧患，死于欢乐。不亦快哉！\n 基督徒不能拜偶像。\n" 
)

print(transcription)
exit()
data = parse_srt(transcription)

with open('/Users/junyang/church/data/transcription.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=4)


pass
