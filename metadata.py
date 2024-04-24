import json
import datetime

def update_metadata(metadata_file: str, items: list, type: str):
    with open(metadata_file, 'r') as f:
        sermons = json.load(f)
    
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
    with open(metadata_file, 'w', encoding='UTF-8') as f:
        json.dump(sermons, f, ensure_ascii=False, indent=4)