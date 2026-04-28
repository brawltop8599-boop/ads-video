from flask import Flask, Response, request, stream_with_context
import requests
import re
import os

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
    # 1. Если пришел XML/FXML, принудительно делаем из него M3U
    if "<channels>" in text or "<items>" in text or "<playlist_url>" in text:
        m3u = "#EXTM3U\n"
        # Ищем все блоки, которые могут содержать ссылки (channel, menu, item)
        items = re.findall(r'<(?:channel|menu|submenu|item)>(.*?)</(?:channel|menu|submenu|item)>', text, re.DOTALL)
        
        for item in items:
            # Ищем название
            title_match = re.search(r'<title><!\[CDATA\[(.*?)]]></title>', item)
            if not title_match: title_match = re.search(r'<title>(.*?)</title>', item)
            
            # Ищем ссылку (стрим или подраздел)
            url_match = re.search(r'<(?:playlist_url|stream_url)><!\[CDATA\[(.*?)]]></(?:playlist_url|stream_url)>', item)
            if not url_match: url_match = re.search(r'<(?:playlist_url|stream_url)>(.*?)</(?:playlist_url|stream_url)>', item)
            
            if title_match and url_match:
                title = title_match.group(1).replace("#", "") # Убираем лишние решетки
                url = url_match.group(1).strip()
                m3u += f'#EXTINF:-1,{title}\n{url}\n'
        
        if "#EXTINF" in m3u:
            text = m3u

    # 2. Проксируем все ссылки через твой домен
    def replace_full_url(match):
        url = match.group(0)
        # Не трогаем картинки и уже проксированные ссылки
        if PROXY_DOMAIN in url or any(ext in url.lower() for ext in [".png", ".jpg", ".jpeg"]): 
            return url
        return f"https://{PROXY_DOMAIN}/ts/{encode_url(url)}"

    text = re.sub(r'https?://[^\s"<>]+', replace_full_url, text)
    return text

@app.route('/')
def health():
    return "Proxy Server is Running! Use /local.m3u for proxied playlist."

@app.route('/playlist.m3u')
@app.route('/playlist.m3u8')
def proxy_playlist():
    try:
        resp = session.get(SOURCE_URL, headers=HEADERS, timeout=25)
        return Response(fix_content(resp.text), mimetype='application/vnd.apple.mpegurl')
    except Exception as e:
        return f"Error: {e}", 500

@app.route('/local.m3u')
def local_playlist():
    if os.path.exists(LOCAL_FILE):
        with open(LOCAL_FILE, 'r', encoding='utf-8') as f:
            return Response(fix_content(f.read()), mimetype='application/vnd.apple.mpegurl')
    return "Local file not found. Run GitHub Action.", 404

@app.route('/ts/<path:full_path>')
def proxy_stream(full_path):
    # Плеер шлет путь типа "HEX_CODE:8080/path/to/segment"
    # Нам нужно вытащить HEX код из самого начала пути
    hex_match = re.match(r'^([^/]+)', full_path)
    hex_part = hex_match.group(1) if hex_match else full_path
    
    # Остаток пути после HEX (если есть)
    suffix = full_path[len(hex_part):].lstrip('/')

    target_url = decode_url(hex_part)
    if not target_url:
        return f"Invalid HEX: {hex_part}", 400

    # Если есть хвост, склеиваем его с базой
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
        print(f"ERROR: {e} | Final URL: {target_url}")
        return "Stream Error", 404

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=7860)
