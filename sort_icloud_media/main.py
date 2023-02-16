import glob
import re
import os
import shutil

from exif import Image
from datetime import datetime


FILE_EXT = ('jpg', 'jpeg', 'gif', 'JPG', 'JPEG', 'GIF', 'png', 'PNG')

def modify_exif(filepath: str):
    folder_path = 'garbage'
    filepath_wo_ext = re.findall(r'(.+?)\.[^\/]+$', filepath)[0]
    filename = re.findall(r'.+?\/([^\/]+)\..+$', filepath)[0]
    fileext = re.findall(r'.+?\/[^\/]+\.(.+)$', filepath)[0]

    try:
        img = Image(filepath)
        date = img.get('datetime_original')
        dt = datetime.strptime(date, '%Y:%m:%d %H:%M:%S')
        folder_path = f"output/{dt.strftime('%Y')}/{dt.strftime('%m')}"
        os.makedirs(folder_path, exist_ok=True)
    except Exception as e:
        pass

    shutil.copyfile(filepath, f'{folder_path}/{filename}.{fileext}')
    try:
        shutil.copyfile(f'{filepath_wo_ext}.MOV', f'{folder_path}/{filename}.MOV')
    except:
        pass

def main():
    for ext in FILE_EXT:
        for filename in glob.iglob(f'input/**/*.{ext}', recursive=True):
            modify_exif(filename)


if __name__ == '__main__':
    main()