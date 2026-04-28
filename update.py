import requests
import time

# ПРЯМАЯ ССЫЛКА НА ИСТОЧНИК
SOURCE_URL = "http://kb-team.club/?do=/plugin&bid=iptvk&box_client=ottplay-foss&m3u&box_mac=3c2ca6f4437e"
FILENAME = "my_list.m3u"

def run():
    # Добавляем случайный параметр к ссылке, чтобы провайдер не выдавал старый файл из кэша
    nocache_url = f"{SOURCE_URL}&_t={int(time.time())}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "*/*"
    }
    
    print(f"Запрашиваю свежий список напрямую (с очисткой кэша)...")
    
    try:
        # Используем сессию, чтобы куки (если они есть) подхватились
        session = requests.Session()
        r = session.get(nocache_url, headers=headers, timeout=30)
        
        if r.status_code == 200 and ("#EXTM3U" in r.text or "<channel>" in r.text):
            with open(FILENAME, "w", encoding="utf-8") as f:
                f.write(r.text.strip())
            print(f"Успех! Файл {FILENAME} обновлен и содержит свежие токены.")
        else:
            print(f"Ошибка: Сервер вернул статус {r.status_code}. Возможно, временная блокировка IP.")
            
    except Exception as e:
        print(f"Критическая ошибка: {e}")

if __name__ == "__main__":
    run()
