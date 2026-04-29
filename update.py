import requests
import time

# МЫ СМЕНИЛИ КЛИЕНТА НА VLC, ЧТОБЫ ПОЛУЧИТЬ СПИСОК, А НЕ МЕНЮ
SOURCE_URL = "https://iptv-online.cc/my/97479/E740CF16EFAA743/m3u8"
FILENAME = "my_list.m3u" 

def run():
    headers = {"User-Agent": "VLC/3.0.18"} # Маскируемся под плеер
    print("Запрашиваю чистый плейлист M3U...")
    try:
        r = requests.get(SOURCE_URL, headers=headers, timeout=30)
        if r.status_code == 200:
            with open(FILENAME, "w", encoding="utf-8") as f:
                f.write(r.text.strip())
            print(f"Успех! Получено {len(r.text)} байт данных.")
        else:
            print(f"Ошибка сервера: {r.status_code}")
    except Exception as e:
        print(f"Ошибка: {e}")

if __name__ == "__main__":
    run()
