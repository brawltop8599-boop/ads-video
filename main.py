import requests

SOURCE = "https://hf.space"
FILENAME = "my_list.m3u"

def run():
    try:
        r = requests.get(SOURCE, timeout=30)
        if r.status_code == 200:
            with open(FILENAME, "w", encoding="utf-8") as f:
                f.write(r.text)
            print("Обновлено!")
    except:
        pass

if __name__ == "__main__":
    run()
