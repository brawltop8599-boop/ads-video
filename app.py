import os
import requests
import re
from flask import Flask, Response, request, stream_with_context

app = Flask(__name__)

# --- НАСТРОЙКИ ---
PROXY_DOMAIN = "videoz-arxiv.hf.space"
LOCAL_FILE = os.path.join(os.path.dirname(__file__), "my_list.m3u")
HEADERS = {
    "User-Agent": "VLC/3.0.18",
    "Referer": "https://iptv-online.cc",
    "Accept": "*/*"
}


session = requests.Session()

def encode_url(url):
    return url.encode().hex()

def decode_url(hex_str):
    try:
        return bytes.fromhex(hex_str).decode()
    except:
        return None

def fix_content(text):
    def replace_url(match):
        u = match.group(0)
        if PROXY_DOMAIN in u or any(ext in u.lower() for ext in [".png", ".jpg", ".jpeg"]):
            return u
        return f"https://{PROXY_DOMAIN}/ts/{encode_url(u)}"
    return re.sub(r'https?://[^\s"<>#\n]+', replace_url, text)

@app.route('/')
def index():
    return "<h1>Server is Running!</h1><p>Плейлист: <a href='/local.m3u'>/local.m3u</a></p>"

@app.route('/local.m3u')
def local_playlist():
    if os.path.exists(LOCAL_FILE):
        try:
            with open(LOCAL_FILE, 'r', encoding='utf-8') as f:
                content = f.read()
                response = Response(fix_content(content), mimetype='application/vnd.apple.mpegurl')
                # ГЛАВНОЕ: ЗАПРЕТ КЭША, чтобы плеер сразу видел новый токен
                response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
                response.headers["Pragma"] = "no-cache"
                response.headers["Expires"] = "0"
                return response
        except Exception as e:
            return f"Error: {e}", 500
    return "File not found", 404

@app.route('/ts/<path:full_path>')
def proxy_stream(full_path):
    # 1. Просто декодируем HEX целиком
    target_url = decode_url(full_path)
    
    if not target_url:
        return "Invalid HEX", 400

    # 2. Добавляем параметры из запроса, если они есть
    if request.query_string:
        sep = "&" if "?" in target_url else "?"
        target_url += f"{sep}{request.query_string.decode('utf-8')}"

    try:
        # Если это плейлист (.m3u8), лечим его
        if ".m3u" in target_url.lower():
            r = session.get(target_url, headers=HEADERS, timeout=20)
            return Response(fix_content(r.text), mimetype='application/vnd.apple.mpegurl')
        
        # Если это видео-сегмент (.ts), передаем поток
        def generate():
            # Здесь используются ваши HEADERS с Referer и VLC
            with session.get(target_url, headers=HEADERS, stream=True, timeout=45) as r:
                r.raise_for_status()
                for chunk in r.iter_content(chunk_size=128*1024):
                    yield chunk
        return Response(stream_with_context(generate()), content_type='video/mp2t')
    except Exception as e:
        print(f"Ошибка потока: {e} | URL: {target_url}")
        return "Stream Error", 404

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=7860)
