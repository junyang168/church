import json
import pandas as pd
import re
import opencc

converter = opencc.OpenCC('s2t')

def simplified_to_traditional(text):
    """
    Convert Simplified Chinese text to Traditional Chinese
    """
    # Initialize converter: 's2t' means Simplified to Traditional
    
    # Perform the conversion
    converted_text = converter.convert(text)
    return converted_text

# List of standard Bible books for reference
BIBLE_BOOKS = [
    "創世記", "出埃及記", "利未記", "民數記", "申命記", "約書亞記", "士師記", "路得記",
    "撒母耳記上", "撒母耳記下", "列王紀上", "列王紀下", "歷代志上", "歷代志下", "以斯拉記", "尼希米記",
    "以斯帖記", "約伯記", "詩篇", "箴言", "傳道書", "雅歌", "以賽亞書", "耶利米書",
    "耶利米哀歌", "以西結書", "但以理書", "何西阿書", "約珥書", "阿摩司書", "俄巴底亞書", "約拿書",
    "彌迦書", "那鴻書", "哈巴谷書", "西番雅書", "哈該書", "撒迦利亞書", "瑪拉基書",
    "馬太福音", "馬可福音", "路加福音", "約翰福音", "使徒行傳", "羅馬書", "哥林多前書", "哥林多後書",
    "加拉太書", "以弗所書", "腓立比書", "歌羅西書", "帖撒羅尼迦前書", "帖撒羅尼迦後書",
    "提摩太前書", "提摩太後書", "提多書", "腓利門書", "希伯來書", "雅各書", "彼得前書", "彼得後書",
    "約翰一書", "約翰二書", "約翰三書", "猶大書", "啟示錄"
]
def extract_book(verse):
    verse = verse['book']
    verse = simplified_to_traditional(verse)
    if not verse or not isinstance(verse, str):
        return None
    # Normalize verse string
    verse = verse.strip()
    # Try to match the book name at the start
    for book in BIBLE_BOOKS:
        if verse.startswith(book):
            return book
        # Handle cases like "撒母耳記上" or "哥林多前書"
        if book in ["撒母耳記上", "撒母耳記下", "列王紀上", "列王紀下", "歷代志上", "歷代志下",
                    "哥林多前書", "哥林多後書", "帖撒羅尼迦前書", "帖撒羅尼迦後書",
                    "提摩太前書", "提摩太後書", "彼得前書", "彼得後書", "約翰一書", "約翰二書", "約翰三書"]:
            # Remove spaces or common suffixes for matching (e.g., "撒上" for "撒母耳記上")
            short_book = book.replace("記上", "上").replace("記下", "下").replace("前書", "前").replace("後書", "後").replace("一書", "一").replace("二書", "二").replace("三書", "三")
            if verse.startswith(short_book):
                return book
    return None

def process_sermons(json_file):
    """Process sermons and count references to each Bible book."""
    try:
        with open(json_file, 'r') as f:
            sermons = json.load(f)
    except Exception as e:
        print(f"Error reading JSON file: {e}")
        return []

    book_counts = {book: set() for book in BIBLE_BOOKS}

    # Handle different JSON structures
    if isinstance(sermons, dict):
        sermons = sermons.get('sermons', []) or list(sermons.values())
    elif not isinstance(sermons, list):
        print("Unexpected JSON structure")
        return []

    result = []
    for sermon in sermons:        
        if not isinstance(sermon, dict):
            continue
        verses = sermon.get('bible_verse')
        if not verses:
            continue
        # Handle verses as string or list
        if isinstance(verses, str):
            verses = [verses]
        elif not isinstance(verses, list):
            continue
        for verse in verses:
            book = extract_book(verse)
            if book:
                book_counts[book].add(sermon['item'])

    # Create a list of all Bible books with counts (including zeros)
    result = []
    for book in BIBLE_BOOKS:
        result.append({"Book": book, "Sermon Count": len(book_counts[book])})

    return result

def write_to_excel(data, output_file):
    """Write the book counts to an Excel file."""
    try:
        df = pd.DataFrame(data)
        df.to_excel(output_file, index=False, sheet_name="Bible Book Sermon Counts")
        print(f"Excel file '{output_file}' created successfully.")
    except Exception as e:
        print(f"Error writing to Excel: {e}")

def main():
    base_dir = '/opt/homebrew/var/www/church/web/data'  

    input_json = base_dir + "config/sermon.json"  # Replace with your JSON file path
    output_excel = base_dir + "report/bible_book_sermon_counts.xlsx"
    book_counts = process_sermons(input_json)
    if book_counts:
        write_to_excel(book_counts, output_excel)
    else:
        print("No data processed.")

if __name__ == "__main__":
    main()