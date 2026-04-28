import os
import requests
import re
from flask import Flask, Response, request, stream_with_context

app = Flask(__name__)

# --- НАСТРОЙКИ ---
SOURCE_URL = "http://kb-team.club/?do=/plugin&bid=iptvk&box_client=ottplay-foss&m3u&box_mac=3c2ca6f4437e"
PROXY_DOMAIN = "videoz-arxiv.hf.space"
LOCAL_FILE = "my_list.m3u"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36", "Accept": "*/*"}

session = requests.Session()

def encode_url(url):
    return url.encode().hex()

def decode_url(hex_str):
    try:
        match = re.search(r'([0-9a-fA-F]{10,})', hex_str)
        if match:
            return bytes.fromhex(match.group(1)).decode()
        return None
    except:
        return None

def fix_content(text, base_url=None):
    # 1. КОНВЕРТАЦИЯ XML В M3U (Добавлена поддержка <menu> и <playlist_url>)
    if "<menu>" in text or "<channel>" in text:
        m3u = "#EXTM3U\n"
        # Ищем все блоки меню и каналов
        items = re.findall(r'<(?:menu|channel)>(.*?)</(?:menu|channel)>', text, re.DOTALL)
        for item in items:
            title_match = re.search(r'<title><!\[CDATA\[(.*?)]]></title>', item)
            url_match = re.search(r'<(?:playlist_url|stream_url)><!\[CDATA\[(.*?)]]></(?:playlist_url|stream_url)>', item)
            if title_match and url_match:
                title = title_match.group(1)
                url = url_match.group(1)
                if url and url != "none":
                    m3u += f'#EXTINF:-1,{title}\n{url}\n'
        if "#EXTINF" in m3u:
            text = m3u

    # 2. ПРОКСИРОВАНИЕ ССЫЛОК
    def replace_url(match):
        u = match.group(0)
        if PROXY_DOMAIN in u or any(ext in u.lower() for ext in [".png", ".jpg", ".jpeg"]):
            return u
        return f"https://{PROXY_DOMAIN}/ts/{encode_url(u)}"

    text = re.sub(r'https?://[^\s"<>#\n]+', replace_url, text)
    return text

@app.route('/')
def index():
    return "<h1>Server is Running!</h1><p>Ваш плейлист тут: <a href='/local.m3u'>/local.m3u</a></p>"

@app.route('/playlist.m3u')
def proxy_playlist():
    try:
        resp = session.get(SOURCE_URL, headers=HEADERS, timeout=25)
        return Response(fix_content(resp.text), mimetype='application/vnd.apple.mpegurl')
    except Exception as e:
        return f"Error: {e}", 500

@app.route('/local.m3u')
def local_playlist():
    if os.path.exists(LOCAL_FILE):
        try:
            with open(LOCAL_FILE, 'r', encoding='utf-8') as f:
                return Response(fix_content(f.read()), mimetype='application/vnd.apple.mpegurl')
        except Exception as e:
            return f"Error reading file: {e}", 500
    return "Local file not found. Run GitHub Action.", 404

@app.route('/ts/<path:full_path>')
def proxy_stream(full_path):
    hex_match = re.match(r'^([^/]+)', full_path)
    hex_part = hex_match.group(1) if hex_match else full_path
    suffix = full_path[len(hex_part):].lstrip('/')
    target_url = decode_url(hex_part)
    
    if not target_url:
        return f"Invalid HEX: {hex_part}", 400

    if suffix:
        clean_suffix = suffix.replace(":8080/", "").replace(":80/", "")
        base_folder = target_url.rsplit('/', 1)[0] if '/' in target_url else target_url
        target_url = f"{base_folder}/{clean_suffix}"

    if request.query_string:
        sep = "&" if "?" in target_url else "?"
        target_url += f"{sep}{request.query_string.decode('utf-8')}"

    try:
        if ".m3u" in target_url.lower():
            r = session.get(target_url, headers=HEADERS, timeout=20)
            return Response(fix_content(r.text, base_url=target_url), mimetype='application/vnd.apple.mpegurl')
        
        def generate():
            with session.get(target_url, headers=HEADERS, stream=True, timeout=45) as r:
                r.raise_for_status()
                for chunk in r.iter_content(chunk_size=131072):
                    yield chunk
        return Response(stream_with_context(generate()), content_type='video/mp2t')
    except Exception as e:
        return "Stream Error", 404

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=7860)
