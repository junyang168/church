import utils
import datetime
import urllib.parse

def create_web_index(base_folder):
    files = utils.get_files( base_folder + '/video', '.mp4')
    items = [f.split('.')[0] for f in files]
    # Extract the date from each item
    dates = [datetime.datetime.strptime(item.split(' ')[0], "%Y-%m-%d").date() for item in items]

    # Sort the items by date
    sorted_items = [item for _, item in sorted(zip(dates, items))]

    # Rest of the code...
    output_folder =  base_folder + '/../web'
    with open(f"{output_folder}/index.html", "w") as file:
        file.write("<!DOCTYPE html>\n")
        file.write("<html>\n")
        file.write("<meta http-equiv='Content-Type' content='text/html'; charset='utf-8'>\n")
        file.write("<head>\n")
        file.write("<title>Video Index</title>\n")
        file.write("</head>\n")
        file.write("<body>\n")
        file.write("<h1>王教授讲道目录</h1>\n")
        file.write("<ul>\n")
        for item in sorted_items:
            qs = urllib.parse.quote(item)
            file.write(f"<li><a href='script_editor.html?i={ qs }'>{item}</a></li>\n")
        file.write("</ul>\n")
        file.write("</body>\n")
        file.write("</html>\n")

if __name__ == '__main__':
    base_folder = '/Users/junyang/church/data'
    create_web_index( base_folder)
