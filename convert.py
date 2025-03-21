import json
import os
import glob

def fix_corrected_script(input_folder, output_folder):
    # Create output folder if it doesn't exist
    os.makedirs(output_folder, exist_ok=True)
    
    # Get all JSONL files in the input folder
    json_files = glob.glob(os.path.join(input_folder, "*.json"))
    
    for json_file in json_files:
        # Get base filename without extension
        base_name = os.path.basename(json_file)
        output_file = os.path.join(output_folder, base_name)
        with open(json_file, 'r') as f:
            data = json.load(f)
            for entry in data:
                entry['index'] = entry.pop('start_index')
                entry['text'] = entry.pop('content')        
        # Write to JSON file as an array
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"Converted {json_file} to {output_file}")


def convert_jsonl_to_json(input_folder, output_folder):
    # Create output folder if it doesn't exist
    os.makedirs(output_folder, exist_ok=True)
    
    # Get all JSONL files in the input folder
    jsonl_files = glob.glob(os.path.join(input_folder, "*.jsonl"))
    
    for jsonl_file in jsonl_files:
        # Get base filename without extension
        base_name = os.path.basename(jsonl_file).replace('.jsonl', '')
        output_file = os.path.join(output_folder, f"{base_name}.json")
        
        # Read all JSON objects from JSONL file
        json_objects = []
        with open(jsonl_file, 'r') as f:
            for line in f:
                if line.strip():  # Skip empty lines
                    obj = json.loads(line)
                    obj['start'] = obj.pop('start_time')
                    obj['end'] = obj.pop('end_time')
                    json_objects.append(obj)
        
        new_obj = {
            "format": "json",
            "entries": json_objects
        }

        # Write to JSON file as an array
        with open(output_file, 'w') as f:
            json.dump(new_obj, f, indent=2, ensure_ascii=False)
        
        print(f"Converted {jsonl_file} to {output_file}")

# Example usage
#input_folder = "/Users/junyang/church/web/data/script"
#output_folder = "/Users/junyang/church/web/data/script"


input_folder = '/Volumes/Jun SSD/data/script_corrected'
output_folder = '/Volumes/Jun SSD/data/script_patched'

fix_corrected_script(input_folder, output_folder)

exit()


input_folder = "/opt/homebrew/var/www/church/web/data/script"
output_folder = "/opt/homebrew/var/www/church/web/data/script"

convert_jsonl_to_json(input_folder, output_folder)