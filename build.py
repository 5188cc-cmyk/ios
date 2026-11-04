"""把 app.html 打包成可放到网站上的独立版本，输出到 dist 文件夹。"""
import glob
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).parent
DIST = ROOT / "dist"
DIST.mkdir(exist_ok=True)

HEAD = """<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="要事簿">
<meta name="theme-color" content="#1f4a3f">
<link rel="manifest" href="manifest.webmanifest">
<link rel="apple-touch-icon" href="icon-180.png">
<style>
:root { padding-top: env(safe-area-inset-top, 0px); padding-bottom: env(safe-area-inset-bottom, 0px); }
[hidden] { display: none !important; }
img { max-width: 100%; }
</style>
"""

SW_REGISTER = """
<script>
if ('serviceWorker' in navigator && location.protocol === 'https:') {
  navigator.serviceWorker.register('sw.js').catch(function () {});
}
</script>
</html>
"""

SW = """var CACHE = 'yaoshibu-%s';
var FILES = ['./', 'index.html', 'manifest.webmanifest', 'icon-180.png', 'icon-512.png'];
self.addEventListener('install', function (e) {
  e.waitUntil(caches.open(CACHE).then(function (c) { return c.addAll(FILES); }).then(function () { return self.skipWaiting(); }));
});
self.addEventListener('activate', function (e) {
  e.waitUntil(caches.keys().then(function (keys) {
    return Promise.all(keys.filter(function (k) { return k !== CACHE; }).map(function (k) { return caches.delete(k); }));
  }).then(function () { return self.clients.claim(); }));
});
self.addEventListener('fetch', function (e) {
  if (e.request.method !== 'GET') return;
  e.respondWith(fetch(e.request).then(function (r) {
    var copy = r.clone();
    caches.open(CACHE).then(function (c) { c.put(e.request, copy); });
    return r;
  }).catch(function () { return caches.match(e.request); }));
});
"""


def find_font():
    for pattern in ("simhei.ttf", "msyhbd.ttc", "simsun.ttc"):
        hits = glob.glob("C:/Windows/Fonts/" + pattern)
        if hits:
            return hits[0]
    raise SystemExit("没有找到中文字体")


def make_icon(size):
    # 松绿底色上一枚朱红方印，和 App 内的“要”字印章一致
    scale = 4
    s = size * scale
    img = Image.new("RGB", (s, s), "#1f4a3f")
    seal = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    draw = ImageDraw.Draw(seal)
    box = s * 0.2
    draw.rounded_rectangle((box, box, s - box, s - box), radius=s * 0.075, fill="#c5301d")
    font = ImageFont.truetype(find_font(), int(s * 0.42))
    draw.text((s / 2, s / 2), "要", font=font, fill="#fff6f0", anchor="mm")
    seal = seal.rotate(7, resample=Image.BICUBIC)
    img.paste(seal, (0, 0), seal)
    return img.resize((size, size), Image.LANCZOS)


app = (ROOT / "app.html").read_text(encoding="utf-8")
(DIST / "index.html").write_text(HEAD + app + SW_REGISTER, encoding="utf-8")
(DIST / "sw.js").write_text(SW % hashlib.sha1(app.encode()).hexdigest()[:8], encoding="utf-8")
(DIST / "manifest.webmanifest").write_text(json.dumps({
    "name": "要事簿",
    "short_name": "要事簿",
    "lang": "zh-CN",
    "start_url": "./",
    "scope": "./",
    "display": "standalone",
    "background_color": "#1f4a3f",
    "theme_color": "#1f4a3f",
    "icons": [
        {"src": "icon-180.png", "sizes": "180x180", "type": "image/png"},
        {"src": "icon-512.png", "sizes": "512x512", "type": "image/png"},
    ],
}, ensure_ascii=False, indent=2), encoding="utf-8")
make_icon(180).save(DIST / "icon-180.png")
make_icon(512).save(DIST / "icon-512.png")
(ROOT / "assets").mkdir(exist_ok=True)
make_icon(1024).save(ROOT / "assets" / "icon-1024.png")
print("已生成：", ", ".join(sorted(p.name for p in DIST.iterdir())))
