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
        clean_hex = re.sub(r'[^0-9a-fA-F]', '', hex_str)
        return bytes.fromhex(clean_hex).decode()
    except:
        return None

def fix_content(text, base_url=None):
    # Если есть база, правим относительные ссылки (tracks-v1/...)
    if base_url:
        base_folder = base_url.rsplit('/', 1)[0]
        text = re.sub(r'^(?!http|#)(.+)$', rf'{base_folder}/\1', text, flags=re.MULTILINE)

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
                return Response(fix_content(f.read()), mimetype='application/vnd.apple.mpegurl')
        except Exception as e:
            return f"Error: {e}", 500
    return "File not found", 404

@app.route('/ts/<path:full_path>')
def proxy_stream(full_path):
    target_url = decode_url(full_path)
    if not target_url:
        return "Invalid HEX", 400

    try:
        r = session.get(target_url, headers=HEADERS, timeout=20, stream=True)
        # Если это плейлист, лечим его
        if ".m3u" in target_url.lower() or "EXTM3U" in r.text[:20]:
            return Response(fix_content(r.text, base_url=target_url), mimetype='application/vnd.apple.mpegurl')
        
        # Если это видео
        def generate():
            for chunk in r.iter_content(chunk_size=256*1024):
                yield chunk
        return Response(stream_with_context(generate()), content_type='video/mp2t')
    except Exception as e:
        return f"Stream Error: {e}", 404

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=7860)
