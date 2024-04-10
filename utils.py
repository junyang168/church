import glob
import os
import string
import opencc

def get_files(directory, extension = None):
    os.chdir(directory)
    extension = extension or ''
    return glob.glob("*" + extension)

def is_whitespace_or_punctuation(char):
    return  char.isspace()  or  char in string.punctuation or char in ['，','。','、','；','：','「','」','『','』','（','）','《','》','？','！','“','”','‘','’','—','…','．','～','〈','〉','﹑','﹔','﹕','﹖','﹗','﹘','﹙','﹚','﹛','﹜','﹝','﹞','﹟','﹠','﹡','﹢','﹣','﹤','﹥','﹦','﹨','﹩','﹪','﹫','！','？','；','：','、','，','。','．','〈','〉','《','》','「','」','『','』','（','）','［','］','｛','｝','【','】','—','…','～','﹏','﹋','﹌','﹍','﹎','﹏','﹐','﹑','﹒','﹔','﹕','﹖','﹗','﹘','﹙','﹚','﹛','﹜','﹝','﹞','﹟','﹠','﹡','﹢','﹣','﹤','﹥','﹦','﹨','﹩','﹪','﹫','！','？','；','：','、','，','。','．','〈','〉','《','》','「','」','『','』','（','）','［','］','｛','｝','【','】','—','…','～','﹏','﹋','﹌','﹍','﹎','﹏','﹐','﹑','﹒','﹔','﹕','﹖','﹗','﹘','﹙','﹚','﹛','﹜','﹝','﹞','﹟','﹠','﹡','﹢','﹣','﹤',']']

def find_last_index_of_whitespace_or_punctuation(text):
    i = len(text)-1
    while i >=0 and is_whitespace_or_punctuation( text[i] ):
        i -= 1

    while i >=0 and not is_whitespace_or_punctuation( text[i] ):
        i -= 1
    return i

def clean_string(text):
    return ''.join([ch for ch in text if not is_whitespace_or_punctuation(ch)])


def convert_to_traditional_chinese(text):
    converter = opencc.OpenCC('s2t')
    return converter.convert(text)