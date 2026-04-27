import requests

# Прямая ссылка на ваше приложение на Hugging Face
SOURCE = "https://videoz-arxiv.hf.space/playlist.m3u"
FILENAME = "my_list.m3u"

def run():
    try:
        # Добавляем User-Agent, чтобы сервер не блокировал запрос от бота
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        r = requests.get(SOURCE, headers=headers, timeout=30)
        
        # Проверяем, что нам пришел именно плейлист, а не ошибка
        if r.status_code == 200 and "#EXTM3U" in r.text:
            with open(FILENAME, "w", encoding="utf-8") as f:
                f.write(r.text)
            print("Плейлист успешно обновлен!")
        else:
            print(f"Ошибка! Статус: {r.status_code}. Проверь, запущен ли Space на Hugging Face.")
    except Exception as e:
        print(f"Критическая ошибка: {e}")

if __name__ == "__main__":
    run()
