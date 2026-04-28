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
    def replace_full_url(match):
        url = match.group(0)
        if PROXY_DOMAIN in url or any(ext in url.lower() for ext in [".png", ".jpg", ".jpeg"]): return url
        return f"https://{PROXY_DOMAIN}/ts/{encode_url(url)}"

    text = re.sub(r'https?://[^\s"<>]+', replace_full_url, text)

    if base_url:
        lines = []
        base_folder = base_url.rsplit('/', 1)[0] if '/' in base_url else base_url
        for line in text.splitlines():
            line = line.strip()
            if line and not line.startswith('#') and not line.startswith('http') and PROXY_DOMAIN not in line:
                full_url = f"{base_folder}/{line}"
                lines.append(f"https://{PROXY_DOMAIN}/ts/{encode_url(full_url)}")
            else:
                lines.append(line)
        text = "\n".join(lines)
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
    hex_match = re.search(r'([0-9a-fA-F]{10,})', full_path)
    hex_part = hex_match.group(1) if hex_match else full_path
    target_url = decode_url(hex_part)
    
    if not target_url:
        return "Invalid HEX", 400

    if request.query_string:
        sep = "&" if "?" in target_url else "?"
        target_url += f"{sep}{request.query_string.decode('utf-8')}"

    try:
        # Добавлено allow_redirects=True для обхода балансировщиков
        r = session.get(target_url, headers=HEADERS, stream=True, timeout=25, allow_redirects=True)
        
        # Если это вложенный плейлист
        content_type = r.headers.get('Content-Type', '').lower()
        if ".m3u" in target_url.lower() or "mpegurl" in content_type:
            return Response(fix_content(r.text, base_url=target_url), mimetype='application/vnd.apple.mpegurl')
        
        # Проверяем статус источника до начала стрима
        if r.status_code != 200:
            return f"Source Error: {r.status_code}", r.status_code

        def generate():
            try:
                for chunk in r.iter_content(chunk_size=131072):
                    yield chunk
            except:
                pass
        
        return Response(
            stream_with_context(generate()), 
            content_type='video/mp2t',
            headers={
                "Access-Control-Allow-Origin": "*",
                "Connection": "keep-alive"
            }
        )
    except Exception as e:
        print(f"PROXY ERROR: {e} | URL: {target_url}")
        return "Stream Error", 404

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=7860)
