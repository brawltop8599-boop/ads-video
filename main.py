import requests
import time

# Ссылка на ваш рабочий прокси-плейлист в Space
SOURCE = "https://videoz-arxiv.hf.space/playlist.m3u"
FILENAME = "my_list.m3u"

def run():
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    
    print(f"Пробуждаем Space по адресу: {SOURCE}...")
    
    # Пытаемся достучаться до Space (3 попытки, если он спит)
    for i in range(3):
        try:
            r = requests.get(SOURCE, headers=headers, timeout=40)
            
            # Проверяем, что получили именно плейлист
            if r.status_code == 200 and "#EXTM3U" in r.text:
                # Сохраняем результат
                with open(FILENAME, "w", encoding="utf-8") as f:
                    f.write(r.text.strip())
                print(f"Успех! Плейлист обновлен и сохранен в {FILENAME}")
                return # Выходим из функции, всё готово
            
            print(f"Попытка {i+1}: Space ответил статус {r.status_code}, ждем прогрузки...")
        except Exception as e:
            print(f"Попытка {i+1}: Ошибка соединения ({e})")
        
        time.sleep(15) # Пауза перед следующей попыткой проснуться

    print("Не удалось обновить плейлист за 3 попытки. Проверьте Space вручную.")

if __name__ == "__main__":
    run()
