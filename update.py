import requests
import re
import os

# Ссылка на ваш источник плейлиста
SOURCE_URL = "https://iptv-online.cc/my/97479/5BE4FFE625DE3AD/m3u8" 
FILENAME = "local_channels.txt"

def run():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "*/*"
    }
    
    print(f"Начинаю обновление из источника: {SOURCE_URL}")
    
    try:
        # Запрос к источнику
        r = requests.get(SOURCE_URL, headers=headers, timeout=30, verify=False)
        r.raise_for_status() # Проверка на ошибки 404, 500 и т.д.
        
        # Ищем все ссылки (m3u8 или прямые потоки)
        content = r.text
        # Регулярка ищет строки, похожие на URL
        urls = re.findall(r'(https?://[^\s"\'<>]+)', content)
        
        if urls:
            with open(FILENAME, "w", encoding="utf-8") as f:
                f.write("#EXTM3U\n")
                count = 0
                for url in urls:
                    url = url.strip()
                    
                    # Фильтруем только нужные типы ссылок
                    if ".m3u8" in url.lower() or "/play/" in url.lower() or "/index" in url.lower():
                        # Пытаемся вытащить ID канала для названия
                        match = re.search(r'/play/(\d+)', url)
                        channel_id = match.group(1) if match else f"{count + 1}"
                        
                        # Записываем в формате M3U
                        f.write(f"#EXTINF:-1 tvg-id=\"id_{channel_id}\", Канал {channel_id}\n")
                        f.write(f"{url}\n")
                        count += 1
                
            print(f"Успешно! Обновлено каналов: {count}")
        else:
            print("Ошибка: Ссылки в источнике не найдены. Проверьте структуру файла.")
            
    except Exception as e:
        print(f"Критическая ошибка при обновлении: {e}")

if __name__ == "__main__":
    run()
