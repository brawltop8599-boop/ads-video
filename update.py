import requests
import re

SOURCE_URL = "https://iptv-online.cc/my/97479/A41463A4526E745/m3u8" 
FILENAME = "local_channels.txt"

def run():
    headers = {"User-Agent": "VLC/3.0.18"}
    try:
        r = requests.get(SOURCE_URL, headers=headers, timeout=30)
        if r.status_code == 200:
            urls = re.findall(r'(https?://[^\s]+)', r.text)
            if urls:
                with open(FILENAME, "w", encoding="utf-8") as f:
                    f.write("#EXTM3U\n")
                    count = 0
                    for url in urls:
                        url = url.strip()
                        # Собираем только прямые ссылки на видео
                        if ".m3u8" in url or "/index" in url:
                            # Извлекаем ID (цифры после /play/)
                            match = re.search(r'/play/(\d+)', url)
                            channel_id = match.group(1) if match else f"Stream-{count}"
                            
                            # Пишем в правильном порядке: инфо, затем ссылка
                            f.write(f"#EXTINF:-1, Канал {channel_id}\n")
                            f.write(f"{url}\n")
                            count += 1
                print(f"Обновлено. Каналов в базе: {count}")
            else:
                print("Ссылки в источнике не найдены.")
        else:
            print(f"Ошибка источника: {r.status_code}")
    except Exception as e:
        print(f"Ошибка скрипта: {e}")

if __name__ == "__main__":
    run()
