import requests
import os

# ПРЯ
DIRECT_SOURCE = "http://kb-team.club/?do=/plugin&bid=iptvk&box_client=ottplay-foss&m3u&box_mac=3c2ca6f4437e"
FILENAME = "my_list.m3u"

def run():
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    
    print(f"Запрашиваем свежий список напрямую...")
    try:
        r = requests.get(DIRECT_SOURCE, headers=headers, timeout=30)
        if r.status_code == 200 and "#EXTM3U" in r.text:
            # Сохраняем "чистый" список. Space сам его проксирует при чтении.
            with open(FILENAME, "w", encoding="utf-8") as f:
                f.write(r.text.strip())
            print(f"Успех! Файл {FILENAME} обновлен.")
        else:
            print(f"Ошибка: Сервер вернул статус {r.status_code} или текст не M3U")
    except Exception as e:
        print(f"Критическая ошибка: {e}")

if __name__ == "__main__":
    run()

        time.sleep(15) # Пауза перед следующей попыткой проснуться

    print("Не удалось обновить плейлист за 3 попытки. Проверьте Space вручную.")

if __name__ == "__main__":
    run()
