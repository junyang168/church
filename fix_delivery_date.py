import os
import glob
from datetime import datetime
import boto3


import json
from datetime import datetime


with open("mp4_files.txt", "r", encoding="utf-8") as f:
    lines = f.readlines()


# Parse into JSON structure
data = []
for line in lines:
    if line.startswith("File:"):
        parts = line.split(" | Last Modified: ")
        path = parts[0].replace("File: ", "").strip()
        date_str = parts[1].strip()
        # Convert date to ISO 8601
        date_obj = datetime.strptime(date_str, "%b %d %H:%M:%S %Y")
        iso_date = date_obj.strftime("%Y-%m-%dT%H:%M:%S")
        data.append({"path": path, 
                     "item" : path[len('/Volumes/JC Data HD 8-26-2022/'):-len('.mp4')],
                     "last_modified": date_obj}
                     )

# Write to JSON file
#with open("mp4_files.json", "w", encoding="utf-8") as f:
#    json.dump(data, f, ensure_ascii=False, indent=2)

def find_item(item):
    if item.find('2019') >= 0:
        return None

    for line in data:
        item_name = line['item']
        if item_name.startswith('HLC/'):
            item_name = item_name[4:]
        item_name = item_name.replace('/', '-')
        if item_name == item:
            return line
    return None

with open("web/data/config/sermon.json", "r", encoding="utf-8") as f:
    sermons = json.load(f)

for sermon in sermons:
    item = find_item(sermon['item'])    
    if item:
        sermon['deliver_date'] = item[ "last_modified"].strftime('%Y-%m-%d')

with open("web/data/config/sermon.json", "w", encoding="utf-8") as f:
    json.dump(sermons, f, ensure_ascii=False, indent=2)

aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID")
aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")
s3 = boto3.client('s3', aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key)
bucket_name = os.getenv('AWS_S3_BUCKET_NAME') 
sermon_key = 'config/sermon_dev.json'
sermons_data = json.dumps(sermons, ensure_ascii=False, indent=2)
s3.put_object(Body=sermons_data, Bucket=bucket_name, Key=sermon_key)


