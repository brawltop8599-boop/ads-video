import os, requests, re, base64, urllib.parse, time, random
from flask import Flask, request, Response, redirect

# Авто-установка (теперь сначала ставим, потом импортируем)
try: 
    from flask_cors import CORS
except: 
    os.system('pip install requests flask-cors flask')
    from flask_cors import CORS

app = Flask(__name__)
CORS(app)

SECRET_KEY = "TvZaTak"
# Ссылка на вашего оператора
SOURCE_M3U = "http://kb-team.club/?do=/plugin&bid=iptvk&box_client=ottplay-foss&m3u&box_mac=vpkhvxmdf3pu"
# Маскируемся под плеер VLC
UA = "VLC/3.0.18 LibVLC/3.0.18"

@app.route('/playlist.m3u')
def get_playlist():
    if request.args.get('k') != SECRET_KEY: return "Fail", 403
    try:
        # Максимальная маскировка под плеер
        headers = {
            "User-Agent": UA,
            "Accept": "*/*",
            "Referer": "http://kb-team.club/",
            "Connection": "keep-alive"
        }
        
        # Делаем запрос
        r = requests.get(SOURCE_M3U, headers=headers, timeout=20)
        r.encoding = 'utf-8' 
        
        lines = r.text.splitlines()
        new_m3u = ["#EXTM3U"]
        base = request.host_url.rstrip('/')
        
        count = 0
        curr_inf = ""
        for line in lines:
            line = line.strip()
            if not line: continue
            if line.startswith("#EXTINF"): 
                curr_inf = line
            elif line.startswith("http"):
                # Кодируем ссылку для прокси
                enc_url = base64.urlsafe_b64encode(line.encode()).decode().replace('=', '')
                new_m3u.append(curr_inf)
                new_m3u.append(f"{base}/ts?k={SECRET_KEY}&url={enc_url}")
                count += 1
        
        # Если список пуст, выводим отладочную инфу прямо в плейлист
        if count == 0:
            return f"#EXTM3U\n#EXTINF:-1, Ошибка: Оператор вернул пустоту. Статус: {r.status_code}", 200
            
        return Response("\n".join(new_m3u), mimetype='application/vnd.apple.mpegurl')
    except Exception as e: 
        return f"Ошибка сервера: {str(e)}", 500

@app.route('/ts')
def proxy_ts():
    if request.args.get('k') != SECRET_KEY: return "403", 403
    try:
        # Декодируем оригинальную ссылку
        url = base64.urlsafe_b64decode(request.args.get('url') + "===").decode()
        
        # Заголовки для потока видео
        headers = {
            "User-Agent": UA,
            "Referer": "http://kb-team.club/",
            "Connection": "keep-alive"
        }
        
        # Передаем Range, если плеер его просит
        if request.headers.get('Range'):
            headers['Range'] = request.headers.get('Range')

        r = requests.get(url, headers=headers, stream=True, timeout=30, verify=False)
        
        # Фильтруем заголовки ответа
        excluded = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
        h = {k: v for k, v in r.headers.items() if k.lower() not in excluded}
        
        return Response(r.iter_content(chunk_size=256*1024), headers=h, status=r.status_code)
    except: return "Stream Error", 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=7860)
