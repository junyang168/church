import json
import datetime
import boto3
import os

def update_metadata(metadata_file: str, items: list, type: str):
    aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID")
    aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")
    s3 = boto3.client('s3', aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key)
    bucket_name = 'dallas-holy-logos'
    sermon_key = 'config/sermon_dev.json'
    try:
        response = s3.get_object(Bucket=bucket_name, Key=sermon_key)
        sermons_data =  response['Body'].read().decode('utf-8')
        sermons =  json.loads(sermons_data)
    except Exception as e:
        sermons = []

    
    for item in items:
        sermon = next((sermon for sermon in sermons if sermon['item'] == item), None)
        if not sermon:                
            sermon  = { 'item': item,
                                'status': 'in development',
                            'last_updated': datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'), 
                            'author': 'dallas.holy.logos@gmail.com',
                            'type': type,}
            sermons.append(sermon)
        else:
            if not sermon.get('author'):
                sermon['author'] = 'dallas.holy.logos@gmail.com'             

        deliver_date, title = item.split(' ',1)
        sermon['deliver_date'] =  deliver_date
        sermon['title'] =  title

    sermons_data = json.dumps(sermons, ensure_ascii=False)
    s3.put_object(Body=sermons_data, Bucket=bucket_name, Key=sermon_key)
