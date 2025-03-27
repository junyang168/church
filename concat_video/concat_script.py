import os
import json

base_folder='/Volumes/Jun SSD/data/script'

def concat_script(prefix:str):
    files = [f for f in os.listdir(base_folder) if f.startswith(prefix) and f.endswith('.json')]    

    files.sort()

    scripts = []
    for file in files:
        with open(os.path.join(base_folder, file), 'r') as f:
            scripts.append(json.load(f))

    all_entries = scripts[0]['entries']

    last_entry = scripts[0]['entries'][-1]

    for s in scripts[1:]:
        last_index = last_entry['index']
        last_start_ms = last_entry['start_ms']
        last_end_ms = last_entry['end_ms']
        last_chunk = last_entry['chunk']

        for entry in s['entries']:
            entry['index'] += last_index
            entry['start_ms'] += last_end_ms
            entry['end_ms'] += last_end_ms
            entry['chunk'] += last_chunk
            entry['start'] = '{:02}:{:02}:{:02},{:03}'.format(entry['start_ms'] // 3600000, (entry['start_ms'] % 3600000) // 60000, (entry['start_ms'] % 60000) // 1000, entry['start_ms'] % 1000)
            entry['end'] = '{:02}:{:02}:{:02},{:03}'.format(entry['end_ms'] // 3600000, (entry['end_ms'] % 3600000) // 60000, (entry['end_ms'] % 60000) // 1000, entry['end_ms'] % 1000)
            all_entries.append(entry)
        last_entry = s['entries'][-1]

    scripts[0]['metadata']['total_entries'] = len(all_entries)
    scripts[0]['metadata']['total_chunks'] = all_entries[-1]['chunk']

    with open(os.path.join(base_folder, prefix[2:-1] + '.json'), 'w') as f:
        json.dump(scripts[0], f, indent=4, ensure_ascii=False)

concat_script('S 190609-')
concat_script('S 191013-')

