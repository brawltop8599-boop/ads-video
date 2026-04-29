import os
try:  
    import requests, flask_cors
except: 
    os.system('pip install requests flask-cors flask')
    import requests, flask_cors

import re, base64, urllib.parse, time, random
from flask import Flask, request, Response, redirect
from flask_cors import CORS


# Авто-установка библиотек
try: 
    from flask_cors import CORS
except: 
    os.system('pip install requests flask-cors flask')
    from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Настройки
SECRET_KEY = "TvZaTak"
# Прямая ссылка на ваш "хитрый" плейлист
SOURCE_M3U = "http://kb-team.club/?do=/plugin&bid=iptvk&box_client=ottplay-foss&m3u&box_mac=vpkhvxmdf3pu"
USER_AGENT = "VLC/3.0.18 LibVLC/3.0.18"

session = requests.Session()

def safe_encode(data): 
    return base64.urlsafe_b64encode(data.encode()).decode().replace('=', '')

def safe_decode(data):
    try:
        data += '=' * (4 - len(data) % 4)
        return base64.urlsafe_b64decode(data.encode()).decode()
    except: return None

@app.route('/')
@app.route('/playlist.m3u')
def get_playlist():
    if request.args.get('k') != SECRET_KEY:
        return "Auth Fail", 403

    try:
        # 1. Качаем плейлист от оператора (через IP сервера)
        r = session.get(SOURCE_M3U, headers={"User-Agent": USER_AGENT}, timeout=15)
        r.encoding = 'utf-8'
        lines = r.text.splitlines()
        
        new_m3u = ["#EXTM3U"]
        base_url = request.host_url.rstrip('/')
        
        current_inf = ""
        for line in lines:
            line = line.strip()
            if line.startswith("#EXTINF"):
                current_inf = line
            elif line.startswith("http"):
                # Кодируем ссылку, чтобы сервер прогнал её через себя
                encoded_url = safe_encode(line)
                proxy_link = f"{base_url}/ts?k={SECRET_KEY}&url={encoded_url}"
                new_m3u.append(current_inf)
                new_m3u.append(proxy_link)
        
        return Response("\n".join(new_m3u), mimetype='application/vnd.apple.mpegurl')
    except Exception as e:
        return str(e), 500

@app.route('/ts')
def proxy_ts():
    if request.args.get('k') != SECRET_KEY:
        return "Forbidden", 403
    
    target_url = safe_decode(request.args.get('url'))
    if not target_url:
        return "Missing URL", 400

    # 2. Проксируем сам видеопоток
    try:
        headers = {"User-Agent": USER_AGENT}
        # Передаем Range если плеер его просит (для перемотки)
        if request.headers.get('Range'):
            headers['Range'] = request.headers.get('Range')

        # Запрашиваем видео у оператора от имени сервера
        r = session.get(target_url, headers=headers, stream=True, timeout=20)
        
        def generate():
            for chunk in r.iter_content(chunk_size=128*1024):
                yield chunk
        
        # Отдаем видео клиенту
        return Response(generate(), content_type=r.headers.get('Content-Type', 'video/mp2t'))
    except:
        return "Stream Error", 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=7860, threaded=True)
