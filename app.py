
import os  # Исправлено: добавлен импорт для работы с файлами
from flask import Flask, Response, request, stream_with_context
import requests
import re

app = Flask(__name__)
@app.route('/')
def index():
    return "<h1>Server is Running!</h1><p>Ваш плейлист тут: <a href='/local.m3u'>/local.m3u</a></p>"

# --- НАСТРОЙКИ ---
SOURCE_URL = http://kb-team.club/?do=/plugin&bid=iptvk&box_client=ottplay-foss&m3u&box_mac=vpkhvxmdf3pu"
PROXY_DOMAIN = "videoz-arxiv.hf.space"
LOCAL_FILE = "my_list.m3u"  # Исправлено: добавлена переменная пути к файлу
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36", "Accept": "*/*"}

session = requests.Session()

def encode_url(url):
    return url.encode().hex()

def decode_url(hex_str):
    try:
        # Извлекаем HEX, игнорируя порты и лишние символы
        match = re.search(r'([0-9a-fA-F]{10,})', hex_str)
        if match:
            return bytes.fromhex(match.group(1)).decode()
        return None
    except:
        return None

def fix_content(text, base_url=None):
    # Конвертация XML/FXML в M3U
    if "<fxml" in text or "<items>" in text:
        m3u = "#EXTM3U\n"
        items = re.findall(r'<channel>(.*?)</channel>', text, re.DOTALL)
        for item in items:
            title = re.search(r'<title><!\[CDATA\[(.*?)]]></title>', item)
            url = re.search(r'<(?:playlist_url|stream_url)><!\[CDATA\[(.*?)]]></(?:playlist_url|stream_url)>', item)
            if title and url:
                m3u += f'#EXTINF:-1,{title.group(1)}\n{url.group(1)}\n'
        text = m3u if "#EXTINF" in m3u else text

    # Проксируем ссылки на потоки
    def replace_full_url(match):
        url = match.group(0)
        # Не проксируем картинки и уже проксированные ссылки
        if PROXY_DOMAIN in url or any(ext in url.lower() for ext in [".png", ".jpg", ".jpeg"]): 
            return url
        return f"https://{PROXY_DOMAIN}/ts/{encode_url(url)}"

    text = re.sub(r'https?://[^\s"<>]+', replace_full_url, text)

    # Исправляем относительные ссылки (для вложенных m3u8)
    if base_url:
        lines = []
        base_folder = base_url.rsplit('/', 1)[0] if '/' in base_url else base_url
        for line in text.splitlines():
            line = line.strip()
            if line and not line.startswith('#') and not line.startswith('http') and not PROXY_DOMAIN in line:
                full_url = f"{base_folder}/{line}"
                lines.append(f"https://{PROXY_DOMAIN}/ts/{encode_url(full_url)}")
            else:
                lines.append(line)
        text = "\n".join(lines)
    
    return text

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
    # Исправлено: теперь файл проверяется и читается корректно
    if os.path.exists(LOCAL_FILE):
        try:
            with open(LOCAL_FILE, 'r', encoding='utf-8') as f:
                content = f.read()
                # Прогоняем локальный список через fix_content, чтобы проксировать ссылки внутри него
                return Response(fix_content(content), mimetype='application/vnd.apple.mpegurl')
        except Exception as e:
            return f"Error reading local file: {e}", 500
    return f"Local file '{LOCAL_FILE}' not found. Check GitHub Action.", 404
	
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
        print(f"ERROR: {e} | Final URL: {target_url}")
        return "Stream Error", 404

if __name__ == "__main__":
    # Для Hugging Face обязательно порт 7860
    app.run(host='0.0.0.0', port=7860)
