import glob
import os
import string


def get_files(directory, extension = None):
    os.chdir(directory)
    extension = extension or ''
    return glob.glob("**/*" + extension, recursive=True)

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


import opencc

def simplified_to_traditional(text):
    """
    Convert Simplified Chinese text to Traditional Chinese
    """
    # Initialize converter: 's2t' means Simplified to Traditional
    converter = opencc.OpenCC('s2t')
    
    # Perform the conversion
    converted_text = converter.convert(text)
    return converted_text
