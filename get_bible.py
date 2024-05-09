import requests
import json

base_folder = '/Users/junyang/church/data/bible/'  # Replace with your desired folder path
url = "https://api.getbible.net/v2/cut.json"  # Replace with your URL
filename = "bible.json"  # Replace with your desired file path

response = requests.get(url)
data = response.json()

with open( base_folder + filename, "w") as f:
    json.dump(data , f, ensure_ascii=False, indent=4)

