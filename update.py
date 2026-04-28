import requests

# Прямая ссылка на провайдера
SOURCE_URL = "http://kb-team.club/?do=/plugin&bid=iptvk&box_client=ottplay-foss&m3u&box_mac=3c2ca6f4437e"
FILENAME = "my_list.m3u"

def run():
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    print("Запрашиваю свежие токены...")
    try:
        r = requests.get(SOURCE_URL, headers=headers, timeout=30)
        if r.status_code == 200 and "#EXTM3U" in r.text:
            with open(FILENAME, "w", encoding="utf-8") as f:
                f.write(r.text.strip())
            print(f"Успех! Файл {FILENAME} обновлен.")
        else:
            print(f"Ошибка: Сервер вернул {r.status_code}")
    except Exception as e:
        print(f"Ошибка: {e}")

if __name__ == "__main__":
    run()
