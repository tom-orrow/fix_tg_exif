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

async def create_task(session, item):
    url = item['attachment']['photo']['sizes'][-1]['url']
    date = datetime.fromtimestamp(item['attachment']['photo']['date'])
    try:
        image_ext = re.findall(r'.*?\/([^\/]+?)(\?|$)', url)[0][0]
    except Exception as e:
        print(image_ext)
        raise e
    folder_path = f"downloads/{date.strftime('%Y')}/{date.strftime('%m')}"
    os.makedirs(folder_path, exist_ok=True)
    tmp_image_name = f"IMG_{date.strftime('%Y%m%d_%H%M%S')}_tmp_{random.randint(0, 1000000)}_" + image_ext
    image_name = f"IMG_{date.strftime('%Y%m%d_%H%M%S')}_vk_" + image_ext
    
    tmp_file_path = f'{folder_path}/{tmp_image_name}'
    file_path = f'{folder_path}/{image_name}'
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
    
async def get_conversations(vk):
    peer_ids = []
    per_page = 200
    offset = 0
    while True:
        res = vk.messages.getConversations(count=per_page, offset=offset)
        if not res['items']:
            break

        for item in res['items']:
            peer_ids.append(item['conversation']['peer']['id'])

        offset += per_page

    return peer_ids

async def get_attachments(vk, peer_id):
    start_from = None
    while True:
        res = vk.messages.getHistoryAttachments(
            peer_id=peer_id,
            media_type='photo',
            count=200,
            start_from=start_from
        )
        if not res['items']:
            break

        
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36"
        }
        async with aiohttp.ClientSession(headers=headers, raise_for_status=True) as session:
            tasks = []
            for item in res['items']:
                task = asyncio.ensure_future(create_task(session, item=item))
                tasks.append(task)

            await asyncio.gather(*tasks)
        start_from = res['next_from']

async def main():
    load_dotenv()

    vk_token = os.getenv('TOKEN')
    vk_session = vk_api.VkApi(token=vk_token, scope='messages')
    vk = vk_session.get_api()

    peer_ids = await get_conversations(vk)

    for peer_id in peer_ids:
        print('>', peer_id)
        await get_attachments(vk, peer_id)

if __name__ == '__main__':
    asyncio.run(main())

