import requests
import re

SOURCE_URL = "https://iptv-online.cc/my/97479/F8A5C0EBB44866F/m3u8" 
FILENAME = "local_channels.txt"

def run():
    headers = {"User-Agent": "VLC/3.0.18"}
    try:
        r = requests.get(SOURCE_URL, headers=headers, timeout=30)
        if r.status_code == 200:
            urls = re.findall(r'(https?://[^\s]+)', r.text)
            if urls:
                with open(FILENAME, "w", encoding="utf-8") as f:
                    f.write("#EXTM3U\n") # Заголовок
                    for url in urls:
                        url = url.strip()
                        if ".m3u8" in url or "/index" in url:
                            # Вытаскиваем ID канала для названия
                            cid = url.split('/play/')[-1].split('/') if '/play/' in url else "TV"
                            f.write(f"#EXTINF:-1, Канал {cid}\n")
                            f.write(f"{url}\n") # Ссылка СТРОГО под инфой
                print(f"Обновлено. Каналов: {len(urls)}")
    except Exception as e:
        print(f"Ошибка: {e}")

if __name__ == "__main__":
    run()
