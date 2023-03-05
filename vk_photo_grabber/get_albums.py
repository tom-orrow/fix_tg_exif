import vk_api
import os
import asyncio
import aiohttp
import aiofiles
import re
import random


from datetime import datetime
from dotenv import load_dotenv
from exif import Image

DIR = os.path.dirname(__file__)
    
async def get_albums(vk):
    res = vk.photos.getAlbums()
    if not res['items']:
        return

    return dict((x['id'], {'title': x['title']}) for x in res['items'])


async def get_photos(vk, albums: dict):
    offset = 0
    count_per_page = 200
    
    while True:
        print(f'Number of images: {offset}')
        res = vk.photos.getAll(
            count=count_per_page,
            offset=offset
        )
        
        if not res['items']:
            break
        
        for item in res['items']:
            album_id = item['album_id']
            if album_id == -6:
                album_title = 'Фотографии с моей страницы'
            elif album_id == -7:
                album_title = 'Фотографии на моей стене'
            else:
                album_title = item['album_id']

            albums.setdefault(album_id, {'title': album_title})
            albums[album_id].setdefault('photos', [])

            albums[album_id]['photos'].append({
                'dt': item['date'],
                'url': item['sizes'][-1]['url']
            })

        offset += count_per_page

    return albums


async def scrape_albums(albums_with_photos: dict):
    headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36"
        }
    async with aiohttp.ClientSession(headers=headers, raise_for_status=True) as session:
        for album in albums_with_photos.values():
            print(f"Getting album: {album['title']}")
            album_folder_path = f"{DIR}/downloads/{album['title']}"
            os.makedirs(album_folder_path, exist_ok=True)
            tasks = []
            for item in album['photos']:
                task = asyncio.ensure_future(create_task(session, album_folder_path=album_folder_path, item=item))
                tasks.append(task)

            await asyncio.gather(*tasks)


async def create_task(session, album_folder_path, item):
    url = item['url']
    date = datetime.fromtimestamp(item['dt'])
    try:
        image_ext = re.findall(r'.*?\/([^\/]+?)(\?|$)', url)[0][0]
    except Exception as e:
        print(image_ext)
        raise e
    folder_path = f"{album_folder_path}/{date.strftime('%Y')}/{date.strftime('%m')}"
    os.makedirs(folder_path, exist_ok=True)
    tmp_image_name = f"IMG_{date.strftime('%Y%m%d_%H%M%S')}_tmp_{random.randint(0, 1000000)}_" + image_ext
    image_name = f"IMG_{date.strftime('%Y%m%d_%H%M%S')}_vk_" + image_ext
    
    tmp_file_path = f'{folder_path}/{tmp_image_name}'
    file_path = f'{folder_path}/{image_name}'
    for i in range(3):
        try:
            async with session.get(url) as resp:
                if resp.status == 200:
                    async with aiofiles.open(tmp_file_path, mode='wb') as f:
                        await f.write(await resp.read())

                    try:
                        img = Image(tmp_file_path)
                    except Exception as e:
                        print(tmp_file_path)
                        raise e
                    img.DateTime = date.strftime('%Y:%m:%d %H:%M:%S')
                    img.DateTimeOriginal = date.strftime('%Y:%m:%d %H:%M:%S')
                    img.DateTimeDigitized = date.strftime('%Y:%m:%d %H:%M:%S')

                    async with aiofiles.open(file_path, mode='wb') as fw:
                        await fw.write(img.get_file())

                    os.remove(tmp_file_path)
                    return
        except aiohttp.client_exceptions.ClientConnectorError:
            print(f"Ошибка скачивания фото '{image_name}', пробуем снова")


async def main():
    load_dotenv()

    vk_token = os.getenv('TOKEN')
    vk_session = vk_api.VkApi(token=vk_token, scope='messages')
    vk = vk_session.get_api()

    albums = await get_albums(vk)
    albums_with_photos = await get_photos(vk, albums)
    await scrape_albums(albums_with_photos)

if __name__ == '__main__':
    asyncio.run(main())
    print('Done.')
