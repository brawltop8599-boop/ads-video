def fix_content(text, base_url=None):
    # Если внутри плейлиста есть относительные пути (как tracks-v1/...), 
    # превращаем их в полные ссылки, используя base_url
    if base_url:
        base_folder = base_url.rsplit('/', 1)[0]
        # Заменяем пути, которые не начинаются с http
        text = re.sub(r'^(?!http|#)(.+)$', rf'{base_folder}/\1', text, flags=re.MULTILINE)

    def replace_url(match):
        u = match.group(0)
        if PROXY_DOMAIN in u or any(ext in u.lower() for ext in [".png", ".jpg", ".jpeg"]):
            return u
        return f"https://{PROXY_DOMAIN}/ts/{encode_url(u)}"
    
    return re.sub(r'https?://[^\s"<>#\n]+', replace_url, text)

@app.route('/ts/<path:full_path>')
def proxy_stream(full_path):
    # Декодируем основную ссылку
    target_url = decode_url(full_path)
    if not target_url:
        return "Invalid HEX", 400

    try:
        # Если это плейлист (.m3u8), читаем его и лечим пути внутри
        r = session.get(target_url, headers=HEADERS, timeout=15)
        if ".m3u" in target_url.lower() or "#EXTM3U" in r.text:
            # ПЕРЕДАЕМ target_url как базу для относительных ссылок
            return Response(fix_content(r.text, base_url=target_url), mimetype='application/vnd.apple.mpegurl')
        
        # Если это видео (.ts)
        return Response(stream_with_context(iter(r.iter_content(chunk_size=256*1024))), content_type='video/mp2t')
    except Exception as e:
        return f"Error: {e}", 404
