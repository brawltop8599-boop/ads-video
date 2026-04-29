import requests
import re

SOURCE_URL = "http://kb-team.club/?do=/plugin&bid=iptvk&box_client=ottplay-foss&m3u&box_mac=3c2ca6f4437e" # Ваша ссылка
FILENAME = "local_channels.txt"

def run():
    headers = {"User-Agent": "VLC/3.0.18"}
    print("Запрашиваю оригинал для обновления базы...")
    try:
        r = requests.get(SOURCE_URL, headers=headers, timeout=30)
        if r.status_code == 200:
            # Ищем все ссылки, начинающиеся на http
            urls = re.findall(r'(https?://[^\s]+)', r.text)
            if urls:
                with open(FILENAME, "w", encoding="utf-8") as f:
                    for url in urls:
                        # Записываем только те ссылки, где есть видеопоток
                        if ".m3u8" in url or "/index" in url or ":8080" in url:
                             f.write(url.strip() + "\n")
                print(f"Успех! База {FILENAME} обновлена. Найдено каналов: {len(urls)}")
        else:
            print(f"Ошибка сервера: {r.status_code}")
    except Exception as e:
        print(f"Ошибка: {e}")

if __name__ == "__main__":
    run()
