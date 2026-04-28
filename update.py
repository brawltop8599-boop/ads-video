import requests
import time

SOURCE_URL = "http://kb-team.club/?do=/plugin&bid=iptvk&box_client=ottplay-foss&m3u&box_mac=3c2ca6f4437e"
FILENAME = "my_list.m3u"

def run():
    nocache_url = f"{SOURCE_URL}&_t={int(time.time())}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "*/*"
    }
    
    print(f"Запрашиваю список (обход кэша)...")
    try:
        r = requests.get(nocache_url, headers=headers, timeout=30)
        # Убираем жесткую проверку на #EXTM3U, принимаем любой текст, если он длинный
        if r.status_code == 200 and len(r.text) > 100:
            with open(FILENAME, "w", encoding="utf-8") as f:
                f.write(r.text.strip())
            print(f"Успех! Файл {FILENAME} обновлен ({len(r.text)} байт).")
        else:
            print(f"Ошибка: Сервер вернул пустой ответ или статус {r.status_code}")
    except Exception as e:
        print(f"Критическая ошибка: {e}")

if __name__ == "__main__":
    run()
