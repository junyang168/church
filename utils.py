import glob
import os

def get_files(directory, extension = None):
    os.chdir(directory)
    extension = extension or ''
    return glob.glob("*" + extension)
