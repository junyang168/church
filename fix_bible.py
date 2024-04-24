import openai
import json
import difflib
import utils

def normalize(text:str):
    return text
    segments = []
    i = 0
    while i < len(text):
        while i < len(text) and utils.is_whitespace_or_punctuation(text[i]):
            i += 1
        seg_start = i
        while i < len(text) and not utils.is_whitespace_or_punctuation(text[i]):
            i += 1        
        segments.append(text[seg_start:i])
    return ''.join(segments)

with open('/Users/junyang/church/data/script_patched/2019-2-15 心mp4.json', 'r') as file1:
    json_patched = json.load(file1)
    paragraphs_patched = [ normalize(p.get('text')) for p in json_patched ]




with open('/Users/junyang/church/data/script_review/心.txt', 'r') as file2:
    txt = file2.read()
    paragraphs_review = txt.split('\n\n')
    paragraphs_review = [ normalize(p) for p in paragraphs_review ]

#for diff in difflib.unified_diff(paragraphs_patched, paragraphs_review):
#    print(diff)


p_indx = [f'[{i}]' for i in range(1, len(paragraphs_patched)+1)]
txt_patched = '\n\n'.join( [ p[0] + p[1]  for p in  zip(paragraphs_patched, p_indx) ])

p_indx = [f'[{i}]' for i in range(1, len(paragraphs_review)+1)]
txt_review = '\n\n'.join( [ p[0] + p[1]  for p in  zip(paragraphs_review, p_indx) ])


diff = difflib.Differ().compare(txt_patched, txt_review)
for ele in diff:
    if ele.startswith('-'):
        print(f"\033[91m{ele[2:]}\033[0m", end='')  # Print removed lines in red
    elif ele.startswith('+'):
        print(f"\033[92m{ele[2:]}\033[0m", end='')  # Print added lines in green
    else:
        print(ele[2:], end='')  # Print unchanged lines as is
print('\n')


iPatched = 0
iReview = 0
len_patched = len(paragraphs_patched)
len_review = len(paragraphs_review)
json_review = []
while iPatched < len_patched and iReview < len_review:    
    while iPatched < len_patched and iReview < len_review and  difflib.SequenceMatcher(None, paragraphs_patched[iPatched], paragraphs_review[iReview]).ratio() > 0.8:
        json_para = { 'text': paragraphs_review[iReview], 'index': json_patched[iPatched].get('index') }
        json_review.append(json_para)
        diff = difflib.Differ().compare(paragraphs_patched[iPatched], paragraphs_review[iReview])
        for ele in diff:
            if ele.startswith('-'):
                print(f"\033[91m{ele}\033[0m", end='')  # Print removed lines in red
            elif ele.startswith('+'):
                print(f"\033[92m{ele}\033[0m", end='')  # Print added lines in green
            else:
                print(ele.strip(), end='')  # Print unchanged lines as is
        print('\n')
        iPatched += 1
        iReview += 1

    j = iReview + 1        
    while iPatched < len_patched and j < len_review and difflib.SequenceMatcher(None, paragraphs_patched[iPatched], paragraphs_review[j]).ratio() < 0.8:
        j += 1
    
    if j >= len_review:
        if iPatched < len_patched:
            print(f"\033[91m{paragraphs_patched[iPatched]}\033[0m\n")
        iPatched += 1
    else:
        for k in range(iReview, j):
            json_para = { 'text': paragraphs_review[k], 'index': json_patched[iPatched-1].get('index') }
            json_review.append(json_para)
            print(f"\033[92m{paragraphs_review[k]}\033[0m\n")
        iReview = j

for k in range(iPatched, len_patched):
    print(f"\033[91m{paragraphs_patched[k]}\033[0m\n")

for k in range(iReview, len_review):
    json_para = { 'text': paragraphs_review[k], 'index': json_patched[len_patched-1].get('index') }
    json_review.append(json_para)
    print(f"\033[92m{paragraphs_review[k]}\033[0m\n")

with open('/Users/junyang/church/data/review/' + '2019-2-15 心mp4' + '.json', 'w', encoding='UTF-8') as f:
    json.dump(json_review, f, ensure_ascii=False, indent=4)



