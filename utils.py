import glob
import os
import string
import opencc

def get_files(directory, extension = None):
    os.chdir(directory)
    extension = extension or ''
    return glob.glob("*" + extension)

def is_whitespace_or_punctuation(char):
    if char == '*':
        return False
    else:
        return  char.isspace()  or  char in string.punctuation or char in ['，','。','、','；','：','「','」','『','』','（','）','《','》','？','！','“','”','‘','’','—','…','．','～','〈','〉','﹑','﹔','﹕','﹖','﹗','﹘','﹙','﹚','﹛','﹜','﹝','﹞','﹟','﹠','﹡','﹢','﹣','﹤','﹥','﹦','﹨','﹩','﹪','﹫','！','？','；','：','、','，','。','．','〈','〉','《','》','「','」','『','』','（','）','［','］','｛','｝','【','】','—','…','～','﹏','﹋','﹌','﹍','﹎','﹏','﹐','﹑','﹒','﹔','﹕','﹖','﹗','﹘','﹙','﹚','﹛','﹜','﹝','﹞','﹟','﹠','﹡','﹢','﹣','﹤','﹥','﹦','﹨','﹩','﹪','﹫','！','？','；','：','、','，','。','．','〈','〉','《','》','「','」','『','』','（','）','［','］','｛','｝','【','】','—','…','～','﹏','﹋','﹌','﹍','﹎','﹏','﹐','﹑','﹒','﹔','﹕','﹖','﹗','﹘','﹙','﹚','﹛','﹜','﹝','﹞','﹟','﹠','﹢','﹣','﹤',']']

def find_last_index_of_whitespace_or_punctuation(text):
    i = len(text)-1
    while i >=0 and is_whitespace_or_punctuation( text[i] ):
        i -= 1
    i_right = i

    while i >=0 and not is_whitespace_or_punctuation( text[i] ):
        i -= 1
    return (i+1, i_right)

def strip_white_space_or_punctuation(text):
        return ''.join([ch for ch in text if not is_whitespace_or_punctuation(ch)])


def find_first_index_of_whitespace_or_punctuation(text):
    i = 0
    while i < len(text) and is_whitespace_or_punctuation( text[i] ):
        i += 1
    i_left = i

    while i < len(text) and not is_whitespace_or_punctuation( text[i] ):
        i += 1
    return ( i_left, i-1)

def clean_string(text):
    return ''.join([ch for ch in text if not is_whitespace_or_punctuation(ch)])


converter = opencc.OpenCC('s2t')

def convert_to_traditional_chinese(text):
    text = text.replace('*', '')
    return converter.convert(text)


from pypinyin import lazy_pinyin, Style

def convert_to_pinyin(str):
    py = lazy_pinyin(str)    
    return ' '.join(py)
