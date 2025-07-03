import openai
import os
# Replace with your actual API key
openai.api_key = os.getenv("OPENAI_API_KEY")

# Sample Christian prayer (you can replace this with your own)
prayer_text = """
亲爱的天父，

我们满心感谢祢的恩典与慈爱，感谢祢带领我们度过这一周的生活，也感谢祢赐下平安与盼望。主啊，我们特别为今天的团契向祢献上感恩，感谢祢让我们这个周五晚上的聚会得以重新开始。感谢祢保守我们弟兄姊妹的心，让我们能同心合意地聚在一起，彼此扶持，彼此鼓励，在真理中一同追求祢的旨意。

主啊，我们也特别为团契的同工们祷告，感谢祢赐给他们智慧和热心，在这个时代懂得善用科技，借着AI平台,整理王教授的讲道信息。在这个过程中，我们更深地体会到你的信实。每次校对讲稿时重新思想经文，讨论怎么准确传达信息，这些细节都让我们对你的话有了新的领受，心思意念都被祢更新。愿祢的圣灵引导我们，不是单靠知识，而是在实践中经历属灵生命的成长。

主啊，我们深知，若不是祢亲自建造，这一切的努力都是枉然。求祢继续带领我们每一位弟兄姊妹，不论是参与服事的，还是安静聆听的，都能在团契中遇见祢、经历祢、爱慕祢。

我们将接下来的时光恭敬地交托在祢手中，愿祢在我们当中居首位，愿祢的名在我们中间得荣耀。

我们如此祷告，是奉靠主耶稣基督得胜的名，阿们。
"""


# Generate speech
response = openai.audio.speech.create(
    model="tts-1-hd",           # or "tts-1-hd" for higher quality
    voice="nova",            # "nova" or "shimmer" are calm and soothing voices
    input=prayer_text
)

# Save to file
base_dir = '/Volumes/Jun SSD/data'
with open(base_dir + "/prayer/prayer.mp3", "wb") as f:
    f.write(response.content)

print("Prayer audio saved as prayer.mp3")
