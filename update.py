import requests
import re
import os

# Ссылка на ваш источник плейлиста
SOURCE_URL = "http://kb-team.club/?do=/plugin&bid=iptvk&box_client=ottplay-foss&m3u&box_mac=vpkhvxmdf3pu" 
FILENAME = "local_channels.txt"

def run():
    # Заголовки, чтобы сайт не заблокировал запрос от скрипта
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "*/*"
    }
    
    print(f"Запуск обновления из источника: {SOURCE_URL}")
    
    try:
        # Скачиваем данные
        r = requests.get(SOURCE_URL, headers=headers, timeout=30, verify=False)
        r.raise_for_status() 
        
        content = r.text
        # Ищем все ссылки (m3u8 или прямые потоки)
        urls = re.findall(r'(https?://[^\s"\'<>]+)', content)
        
        if urls:
            with open(FILENAME, "w", encoding="utf-8") as f:
                # Записываем заголовок плейлиста
                f.write("#EXTM3U\n")
                count = 0
                
                for url in urls:
                    url = url.strip()
                    
                    # Проверяем, что это видео-ссылка
                    if ".m3u8" in url.lower() or "/play/" in url.lower() or "/index" in url.lower():
                        # Простая логика именования каналов по ID из ссылки
                        match = re.search(r'/play/(\d+)', url)
                        channel_id = match.group(1) if match else f"ID-{count + 1}"
                        
                        # Записываем данные канала (логотип и группа — общие настройки)
                        f.write(f'#EXTINF:-1 tvg-id="ch_{channel_id}" tvg-logo="https://githubusercontent.com" group-title="Общие", Канал {channel_id}\n')
                        f.write(f"{url}\n")
                        count += 1
                
            print(f"Готово! База обновлена. Найдено каналов: {count}")
        else:
            print("Ошибка: Ссылки в исходном файле не найдены.")
            
    except Exception as e:
        print(f"Произошла ошибка при обновлении: {e}")

if __name__ == "__main__":
    run()
