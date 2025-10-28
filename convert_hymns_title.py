from bs4 import BeautifulSoup
import json
import re

def convert_hymns_html_to_json(html_file_path, json_file_path):
    """
    Reads an HTML file containing a list of hymns, extracts the index,
    title, and link for each hymn, and saves the data to a JSON file.

    Args:
        html_file_path (str): The path to the input HTML file.
        json_file_path (str): The path where the output JSON file will be saved.
    """
    hymns_list = []

    try:
        # Open and read the HTML file with UTF-8 encoding
        with open(html_file_path, 'r', encoding='utf-8') as f:
            html_content = f.read()

        # Create a BeautifulSoup object to parse the HTML
        soup = BeautifulSoup(html_content, 'lxml')

        # Find all the list items (<li>) in the document
        list_items = soup.find_all('li')

        for item in list_items:
            # Find the anchor tag <a> within the list item
            anchor_tag = item.find('a')
            
            if anchor_tag:
                # Extract the title from the text of the anchor tag
                title = anchor_tag.get_text(strip=True)
                
                # Extract the link from the 'href' attribute
                link = anchor_tag.get('href')
                
                # Use regex to find the number in the list item's text
                # Example text: "第1首" (Hymn #1)
                index_match = re.search(r'\d+', item.text)
                if index_match:
                    index = int(index_match.group(0))
                else:
                    index = None # Handle cases where index might be missing
                    
                # Create a dictionary for the hymn and add it to our list
                hymn_data = {
                    'index': index,
                    'title': title,
                    'link': link
                }
                hymns_list.append(hymn_data)

        # Write the list of hymns to a JSON file
        with open(json_file_path, 'w', encoding='utf-8') as f:
            # json.dumps converts the Python list to a JSON formatted string
            # ensure_ascii=False ensures Chinese characters are not escaped
            # indent=2 makes the JSON output readable (pretty-printing)
            json.dump(hymns_list, f, ensure_ascii=False, indent=2)
            
        print(f"Successfully converted {len(hymns_list)} hymns.")
        print(f"JSON data saved to '{json_file_path}'")

    except FileNotFoundError:
        print(f"Error: The file '{html_file_path}' was not found.")
    except Exception as e:
        print(f"An error occurred: {e}")

# --- --- --- --- ---
#      MAIN
# --- --- --- --- ---
if __name__ == "__main__":
    # Define the input and output file names
    input_html_file = '/Users/junyang/church/data/hymns.html'
    output_json_file = '/Users/junyang/church/data/hymns.json'
    
    # Run the conversion function
    convert_hymns_html_to_json(input_html_file, output_json_file)