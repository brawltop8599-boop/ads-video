import os
try: import requests, flask_cors
except: os.system('pip install requests flask-cors flask'); import requests, flask_cors

import re, base64, urllib.parse, time, random
from flask import Flask, request, Response, redirect
from flask_cors import CORS


app = Flask(__name__)
CORS(app)

session = requests.Session()
adapter = requests.adapters.HTTPAdapter(pool_connections=1000, pool_maxsize=1000)
session.mount('http://', adapter)
session.mount('https://', adapter)

SECRET_KEY = "TvZaTak"
LOCAL_FILE = "local_channels.txt"
MAINTENANCE_VIDEO = "https://github.com"
USER_AGENTS = ["VLC/3.0.18 LibVLC/3.0.18", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"]

CHANNELS_CACHE = []
LAST_LOAD_TIME = 0

def get_target_headers(url):
    parsed = urllib.parse.urlparse(url)
    h = {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "*/*",
        "Host": parsed.netloc,
        "Referer": f"{parsed.scheme}://{parsed.netloc}/",
        "Connection": "keep-alive"
    }
    if request.headers.get('Range'):
        h['Range'] = request.headers.get('Range')
    return h

def load_data():
    global CHANNELS_CACHE, LAST_LOAD_TIME
    if time.time() - LAST_LOAD_TIME < 20 and CHANNELS_CACHE: return
    if os.path.exists(LOCAL_FILE):
        try:
            with open(LOCAL_FILE, "r", encoding="utf-8") as f:
                content = f.read()
                items = re.findall(r'#EXTINF:(.*?),(.*?)\n(http[^\s#]+)', content)
                CHANNELS_CACHE = []
                for attr_str, name, url in items:
                    t_id = re.search(r'tvg-id="(.*?)"', attr_str)
                    t_logo = re.search(r'tvg-logo="(.*?)"', attr_str)
                    t_rec = re.search(r'tvg-rec="(.*?)"', attr_str)
                    group = re.search(r'group-title="(.*?)"', attr_str)
                    CHANNELS_CACHE.append({
                        "name": name.strip(), "url": url.strip(),
                        "tvg_id": t_id.group(1) if t_id else "",
                        "tvg_logo": t_logo.group(1) if t_logo else "",
                        "tvg_rec": t_rec.group(1) if t_rec else "0",
                        "group": group.group(1) if group else "Общие"
                    })
                LAST_LOAD_TIME = time.time()
        except: pass

def safe_encode(data): return base64.urlsafe_b64encode(data.encode()).decode().replace('=', '')
def safe_decode(data):
    try:
        data += '=' * (4 - len(data) % 4)
        return base64.urlsafe_b64decode(data.encode()).decode()
    except: return None

@app.route('/')
@app.route('/playlist.m3u')
def playlist():
    if request.args.get('k') != SECRET_KEY: return redirect(MAINTENANCE_VIDEO)
    load_data()
    base = request.host_url.rstrip('/')
    m3u = ["#EXTM3U url-tvg=\"http://epg.one\""]
    for i, ch in enumerate(CHANNELS_CACHE):
        eid = safe_encode(str(i))
        inf = f'#EXTINF:-1 tvg-id="{ch["tvg_id"]}" tvg-logo="{ch["tvg_logo"]}" group-title="{ch["group"]}"'
        if ch["tvg_rec"] != "0":
            inf += f' tvg-rec="{ch["tvg_rec"]}" catchup="append" catchup-days="7"'
        m3u.append(f'{inf},{ch["name"]}\n{base}/s?k={SECRET_KEY}&i={eid}')
    return Response("\n".join(m3u), mimetype='application/vnd.apple.mpegurl')

@app.route('/s')
def s():
    if request.args.get('k') != SECRET_KEY: return "Auth Fail", 403
    
    eid, enc = request.args.get('i'), request.args.get('e')
    archive_params = request.args.to_dict()
    for k in ['k', 'i', 'e']: archive_params.pop(k, None)
    
    if 'lutc' in archive_params: archive_params['utc'] = archive_params['lutc']

    target_url = None
    if enc:
        target_url = safe_decode(enc)
    elif eid:
        load_data()
        try:
            idx = int(safe_decode(eid))
            if 0 <= idx < len(CHANNELS_CACHE): target_url = CHANNELS_CACHE[idx]["url"]
        except: pass

    if not target_url: return "Not Found", 404

    if archive_params:
        for key, val in archive_params.items():
            if f"{key}=" not in target_url:
                sep = '&' if '?' in target_url else '?'
                target_url += f"{sep}{key}={val}"

    try:
        r = session.get(target_url, headers=get_target_headers(target_url), stream=True, timeout=(15, 60), verify=False, allow_redirects=True)
        excluded = ['content-encoding', 'content-length', 'transfer-encoding', 'connection', 'server', 'set-cookie']
        h = {k: v for k, v in r.headers.items() if k.lower() not in excluded}
        h['Access-Control-Allow-Origin'] = '*'
        h['Accept-Ranges'] = 'bytes'

        ct = r.headers.get('Content-Type', '').lower()
        is_m3u8 = "mpegurl" in ct or ".m3u8" in target_url.lower().split('?')[0]

        if is_m3u8:
            content = r.content.decode('utf-8', errors='ignore')
            lines = content.splitlines()
            new_lines = []
            base_proxy = request.host_url.rstrip('/')
            for line in lines:
                line = line.strip()
                if line and not line.startswith('#'):
                    full_link = urllib.parse.urljoin(r.url, line)
                    proxy_link = f"{base_proxy}/s?k={SECRET_KEY}&e={safe_encode(full_link)}"
                    if archive_params: proxy_link += "&" + urllib.parse.urlencode(archive_params)
                    new_lines.append(proxy_link)
                else:
                    new_lines.append(line)
            return Response("\n".join(new_lines), mimetype='application/vnd.apple.mpegurl')

        if 'video' not in h.get('Content-Type', '').lower():
            h['Content-Type'] = 'video/mp2t'

        def generate():
            try:
                for chunk in r.iter_content(chunk_size=256*1024):
                    yield chunk
            finally:
                r.close()

        return Response(generate(), headers=h, status=r.status_code)

    except Exception as e:
        return redirect(MAINTENANCE_VIDEO)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=7860, threaded=True)
