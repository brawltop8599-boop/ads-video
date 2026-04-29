import os, requests, re, base64, urllib.parse, time, random
from flask import Flask, request, Response, redirect
from flask_cors import CORS

# Авто-установка
try: import flask_cors
except: os.system('pip install requests flask-cors flask')

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
        # Качаем плейлист с правильным User-Agent
        r = requests.get(SOURCE_M3U, headers={"User-Agent": UA}, timeout=20)
        lines = r.text.splitlines()
        
        new_m3u = ["#EXTM3U"]
        base = request.host_url.rstrip('/')
        
        curr_inf = ""
        for line in lines:
            if line.startswith("#EXTINF"): curr_inf = line
            elif line.startswith("http"):
                # Прячем ссылку в прокси
                enc_url = base64.urlsafe_b64encode(line.strip().encode()).decode().replace('=', '')
                new_m3u.append(curr_inf)
                new_m3u.append(f"{base}/ts?k={SECRET_KEY}&url={enc_url}")
        
        return Response("\n".join(new_m3u), mimetype='application/vnd.apple.mpegurl')
    except Exception as e: return str(e), 500

@app.route('/ts')
def proxy_ts():
    if request.args.get('k') != SECRET_KEY: return "403", 403
    try:
        url = base64.urlsafe_b64decode(request.args.get('url') + "===").decode()
        # Проксируем поток
        r = requests.get(url, headers={"User-Agent": UA}, stream=True, timeout=30)
        return Response(r.iter_content(chunk_size=128*1024), content_type=r.headers.get('Content-Type'))
    except: return "Error", 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=7860)
