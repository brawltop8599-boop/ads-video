from flask import Flask, Response, request, stream_with_context
import requests
import re

app = Flask(__name__)

# --- НАСТРОЙКИ ---
SOURCE_URL = "http://kb-team.club/?do=/plugin&bid=iptvk&box_client=ottplay-foss&m3u&box_mac=vpkhvxmdf3pu"
PROXY_DOMAIN = "videoz-arxiv.hf.space"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36", "Accept": "*/*"}

session = requests.Session()

def encode_url(url):
    return url.encode().hex()

def decode_url(hex_str):
    try:
        # Извлекаем только чистый HEX (символы 0-9 и a-f), игнорируя порты :8080 и прочее
        match = re.search(r'([0-9a-fA-F]{10,})', hex_str)
        if match:
            return bytes.fromhex(match.group(1)).decode()
        return None
    except:
        return None

def fix_content(text, base_url=None):
    # Если пришел XML/FXML - конвертируем его в M3U
    if "<fxml" in text or "<items>" in text:
        m3u = "#EXTM3U\n"
        items = re.findall(r'<channel>(.*?)</channel>', text, re.DOTALL)
        for item in items:
            title = re.search(r'<title><!\[CDATA\[(.*?)]]></title>', item)
            url = re.search(r'<(?:playlist_url|stream_url)><!\[CDATA\[(.*?)]]></(?:playlist_url|stream_url)>', item)
            if title and url:
                m3u += f'#EXTINF:-1,{title.group(1)}\n{url.group(1)}\n'
        text = m3u if "#EXTINF" in m3u else text

    # Проксируем полные ссылки
    def replace_full_url(match):
        url = match.group(0)
        if PROXY_DOMAIN in url or any(ext in url.lower() for ext in [".png", ".jpg", ".jpeg"]): return url
        return f"https://{PROXY_DOMAIN}/ts/{encode_url(url)}"

    text = re.sub(r'https?://[^\s"<>]+', replace_full_url, text)

    # Исправляем относительные ссылки (для вложенных m3u8)
# Эта часть заменяет относительные пути внутри m3u8 на полные прокси-ссылки
    if base_url:
        new_lines = []
        base_folder = base_url.rsplit('/', 1)[0] if '/' in base_url else base_url
        for line in text.splitlines():
            line = line.strip()
            if line and not line.startswith('#') and not line.startswith('http'):
                full_link = f"{base_folder}/{line}"
                new_lines.append(f"https://{PROXY_DOMAIN}/ts/{encode_url(full_link)}")
            else:
                new_lines.append(line)
        text = "\n".join(new_lines)
    
    return text

@app.route('/')
def index():
    return "IPTV Proxy is Running! Use /playlist.m3u8 in your player."

@app.route('/playlist.m3u')
@app.route('/playlist.m3u8')
def proxy_playlist():
    try:
        resp = session.get(SOURCE_URL, headers=HEADERS, timeout=25)
        # Явно передаем URL для исправления относительных ссылок
        fixed_text = fix_content(resp.text, base_url=SOURCE_URL)
        return Response(fixed_text, mimetype='application/vnd.apple.mpegurl')
    except Exception as e:
        return f"Error: {e}", 500

@app.route('/ts/<path:full_path>')
def proxy_stream(full_path):
    # Улучшенный разбор HEX-ссылки
    hex_match = re.search(r'([0-9a-fA-F]{20,})', full_path)
    hex_part = hex_match.group(1) if hex_match else full_path
    
    target_url = decode_url(hex_part)
    if not target_url:
        return f"Invalid URL structure", 400

    # Если это m3u8 внутри потока, мы должны обработать его содержимое
    try:
        # ДОБАВЛЯЕМ REFERER - это критично для kb-team!
        stream_headers = {
            "User-Agent": HEADERS["User-Agent"],
            "Referer": "http://kb-team.club/",
            "Accept": "*/*"
        }

        if ".m3u" in target_url.lower() or ".m3u8" in target_url.lower():
            r = session.get(target_url, headers=stream_headers, timeout=20)
            return Response(fix_content(r.text, base_url=target_url), mimetype='application/vnd.apple.mpegurl')
        
        # Проксирование самого видео
        def generate():
            with session.get(target_url, headers=stream_headers, stream=True, timeout=60) as r:
                for chunk in r.iter_content(chunk_size=256*1024):
                    yield chunk
                    
        return Response(stream_with_context(generate()), content_type='video/mp2t')
    except Exception as e:
        return "Stream Error", 404

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=7860)
