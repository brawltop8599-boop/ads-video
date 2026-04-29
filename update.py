import requests
import re

SOURCE_URL = "https://iptv-online.cc/my/97479/FF46BB6E2C1A136/m3u8" 
FILENAME = "local_channels.txt"

def run():
    headers = {"User-Agent": "VLC/3.0.18"}
    print("Запрашиваю оригинал для обновления базы...")
    try:
        r = requests.get(SOURCE_URL, headers=headers, timeout=30)
        if r.status_code == 200:
            # Ищем все ссылки
            urls = re.findall(r'(https?://[^\s]+)', r.text)
            
            if urls:
                with open(FILENAME, "w", encoding="utf-8") as f:
                    # 1. ОБЯЗАТЕЛЬНО записываем заголовок в начало файла
                    f.write("#EXTM3U\n")
                    
                    count = 0
                    for url in urls:
                        url = url.strip()
                        # Фильтруем только нужные ссылки
                        if ".m3u8" in url or "/index" in url or ":8080" in url:
                            # 2. Извлекаем ID канала из ссылки для названия (например, 9987)
                            # Если структура ссылки изменится, будет просто порядковый номер
                            parts = url.split('/play/')
                            channel_id = parts[1].split('/')[0] if len(parts) > 1 else str(count + 1)
                            
                            # 3. Записываем инфо-строку и саму ссылку
                            f.write(f"#EXTINF:-1, Канал {channel_id}\n")
                            f.write(f"{url}\n")
                            count += 1
                            
                print(f"Успех! База {FILENAME} обновлена. Найдено каналов: {count}")
        else:
            print(f"Ошибка сервера: {r.status_code}")
    except Exception as e:
        print(f"Ошибка: {e}")

if __name__ == "__main__":
    run()
