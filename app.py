import os
import requests
import re
from flask import Flask, Response, request, stream_with_context

app = Flask(__name__)

# --- НАСТРОЙКИ ---
PROXY_DOMAIN = "videoz-arxiv.hf.space"
LOCAL_FILE = os.path.join(os.path.dirname(__file__), "my_list.m3u")
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36", "Accept": "*/*"}

session = requests.Session()

def encode_url(url):
    return url.encode().hex()

def decode_url(hex_str):
    try:
        return bytes.fromhex(hex_str).decode()
    except:
        return None

def fix_content(text):
    # Если это XML, превращаем в M3U
    if "<channel>" in text or "<playlist_url>" in text:
        m3u = "#EXTM3U\n"
        items = re.findall(r'<(?:menu|channel)>(.*?)</(?:menu|channel)>', text, re.DOTALL)
        for item in items:
            t = re.search(r'<title><!\[CDATA\[(.*?)]]></title>', item)
            u = re.search(r'<(?:playlist_url|stream_url)><!\[CDATA\[(.*?)]]></(?:playlist_url|stream_url)>', item)
            if t and u:
                m3u += f'#EXTINF:-1,{t.group(1)}\n{u.group(1)}\n'
        text = m3u if "#EXTINF" in m3u else text

    # Проксируем ссылки
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
            return f"Error reading file: {e}", 500
    return f"File not found at {LOCAL_FILE}", 404

@app.route('/ts/<path:full_path>')
def proxy_stream(full_path):
    target_url = decode_url(full_path)
    if not target_url:
        return "Invalid URL", 400
    try:
        if ".m3u" in target_url.lower():
            r = session.get(target_url, headers=HEADERS, timeout=10)
            return Response(fix_content(r.text), mimetype='application/vnd.apple.mpegurl')
        
        def generate():
            with session.get(target_url, headers=HEADERS, stream=True, timeout=30) as r:
                for chunk in r.iter_content(chunk_size=128*1024):
                    yield chunk
        return Response(stream_with_context(generate()), content_type='video/mp2t')
    except:
        return "Stream Error", 404

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=7860)
