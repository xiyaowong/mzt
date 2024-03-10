import json
import os
import re
import time
from queue import Empty, Queue
from threading import Thread

import requests

from utils import check_dir, download

base_dir = os.path.abspath(os.path.dirname(__file__))
pics_save_dir = os.path.join(base_dir, 'pics')

check_dir(pics_save_dir)

parse_task = Queue(maxsize=10000)  # [id]
dl_task = Queue(maxsize=10000)  # [url, filename, filetype]

base_hd = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
    'Origin': 'https://t.me',
    'Host': 't.me',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.138 Safari/537.36'
}


def newest_id() -> int:
    try:
        rep = requests.get('https://t.me/s/botmzt',
                           headers=base_hd.update({"Referer": "https://t.me/botmzt"}), timeout=20)
        ids = re.findall(r'https://t\.me/botmzt/(\d+)', rep.text)
        newest_id = max(int(i) for i in ids)
        print(f'最新图片ID：{newest_id}')
        return newest_id
    except Exception as e:
        print(e)
    return 0


def get_parse_id_list() -> list:
    with open(os.path.join(base_dir, 'task.json')) as f:
        task = json.load(f)
    start = task['start']
    end = task['end']
    with open(os.path.join(base_dir, 'task.json'), 'w') as f:
        json.dump({"start": 0, "end": 0}, f)
    if start == 0 and end == 0:
        saved_pic_list = [i[:i.rindex('.')] for i in os.listdir(pics_save_dir)]
        max_id = max(int(i) for i in saved_pic_list)
        start = max_id
        end = newest_id()
        if start == end or start > end:
            return []
    return list(range(start, end))


def parse():
    while not parse_task.empty():
        saved_pic_list = [i[:i.rindex('.')] for i in os.listdir(pics_save_dir)]
        try:
            parse_id = parse_task.get(timeout=10)
            print(f'[PARSING]: {parse_id}')

            if str(parse_id) in saved_pic_list:
                print(f'{parse_id}已存在！')
                continue

            url = f"https://t.me/botmzt/{parse_id}?embed=1&single=1"
            rep = requests.get(url, headers=base_hd.update({'Referer': url}), timeout=22)
            imgs = re.findall(r"background-image:url\('(http.*?)'\)", rep.text)
            if imgs:
                img_url = imgs[0]
                img_name = str(parse_id)
                img_type = img_url[img_url.rindex('.') + 1:]
                done = [img_url, img_name, img_type]
                print(f"[PARSE DONE]: {done}")
                dl_task.put(done)
        except Exception as e:
            if isinstance(e, Empty):
                break
            print("[Func: parse {parse_id}]", e)


def dl():
    while not dl_task.empty():
        try:
            pic = dl_task.get(timeout=15)
            pic_url = pic[0]
            pic_name = pic[1]
            pic_type = pic[2]
            print(f'[Downloading]: {pic_name}.{pic_type}')
            download(file_url=pic_url,
                     file_name=pic_name,
                     file_type=pic_type,
                     headers=base_hd.update({"Host": "cdn1.telesco.pe"}),
                     save_path=pics_save_dir)
        except Exception as e:
            if isinstance(e, Empty):
                break
            print(f"[Func: dl {pic}]", e)


def main():
    parse_id_list = get_parse_id_list()
    print(f'=======parse_id_list: {parse_id_list}=======')
    for parse_id in parse_id_list:
        parse_task.put(parse_id)

    parse_threads = [Thread(target=parse) for _ in range(8)]

    for t in parse_threads:
        t.start()

    for t in parse_threads:
        t.join()

    time.sleep(120)

    dl_threads = [Thread(target=dl) for _ in range(8)]
    for t in dl_threads:
        t.start()
    for t in dl_threads:
        t.join()

    refresh_data()


def refresh_data():
    saved_pic_list = os.listdir(pics_save_dir)
    data = {
        'time': int(time.time()),
        'count': len(saved_pic_list),
        'pics': saved_pic_list
    }
    with open(os.path.join(base_dir, 'data.json'), 'w') as f:
        json.dump(data, f)
        print('[data.json]更新成功！')


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(e)
        refresh_data()
