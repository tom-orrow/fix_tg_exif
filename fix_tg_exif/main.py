import glob
import re
import os

from exif import Image
from datetime import datetime

DIR = os.path.dirname(__file__)

def modify_exif(filepath: str):
    date = re.findall(r'.+?photo_.+?@([^\.]+)\.', filepath)[0]
    filename = re.findall(r'.+?\/(photo_.+$)', filepath)[0]
    dt = datetime.strptime(date, '%d-%m-%Y_%H-%M-%S')

    folder_path = f"{DIR}/output/{dt.strftime('%Y')}/{dt.strftime('%m')}"
    os.makedirs(folder_path, exist_ok=True)

    img = Image(filepath)
    exif_dt = dt.strftime('%Y:%m:%d %H:%M:%S')
    img.DateTime = exif_dt
    img.DateTimeOriginal = exif_dt
    img.DateTimeDigitized = exif_dt

    with open(f'{folder_path}/{filename}', 'wb') as f:
        f.write(img.get_file())

def main():
    for filename in glob.iglob('{DIR}/input/**/photo_*@*.*', recursive=True):
        if re.search(r'_thumb\..+$', filename):
            continue
        
        modify_exif(filename)


if __name__ == '__main__':
    main()