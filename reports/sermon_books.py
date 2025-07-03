import json
import csv
from collections import defaultdict
import uuid

base_dir = '/Volumes/Jun SSD/data'  
# Sample JSON data (replace with actual file reading in production)
with open(base_dir +'/config/sermon.json', 'r', encoding='utf-8') as file:
    sermons = json.load(file)

# Function to extract unique books from bible_verse field
def get_bible_books(bible_verses):
    if not bible_verses:
        return ""
    books = sorted(set(verse['book'] for verse in bible_verses))
    return ";".join(books)

# Prepare data for CSV
csv_data = []
for sermon in sermons:
    item = sermon.get('item', '')
    title = sermon.get('title', '')
    status = sermon.get('status', '')
    deliver_date = sermon.get('deliver_date', '')
    theme = sermon.get('theme', '')
    bible_books = get_bible_books(sermon.get('bible_verse', []))
    
    csv_data.append({
        'item': item,
        'title': title,
        'status': status,
        'deliver_date': deliver_date,
        'theme': theme,
        'bible_books': bible_books
    })

# Write to CSV
with open(base_dir + '/report/sermon_summary.csv', 'w', encoding='utf-8', newline='') as csvfile:
    fieldnames = ['item', 'title', 'status', 'deliver_date', 'theme', 'bible_books']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    
    writer.writeheader()
    for row in csv_data:
        writer.writerow(row)

print("CSV file 'sermon_summary.csv' has been generated.")