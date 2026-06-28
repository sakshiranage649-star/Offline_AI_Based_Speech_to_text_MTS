import os
import urllib.request
import re

ASSETS_DIR = os.path.join("frontend", "assets")
JS_DIR = os.path.join(ASSETS_DIR, "js")
CSS_DIR = os.path.join(ASSETS_DIR, "css")
FONTS_DIR = os.path.join(ASSETS_DIR, "fonts")
IMG_DIR = os.path.join(ASSETS_DIR, "img")

os.makedirs(JS_DIR, exist_ok=True)
os.makedirs(CSS_DIR, exist_ok=True)
os.makedirs(FONTS_DIR, exist_ok=True)
os.makedirs(IMG_DIR, exist_ok=True)

# 1. Download JS files
js_files = {
    "tailwindcss.js": "https://cdn.tailwindcss.com",
    "chart.js": "https://cdn.jsdelivr.net/npm/chart.js",
    "lucide.js": "https://unpkg.com/lucide@latest"
}

print("Downloading JS files...")
for filename, url in js_files.items():
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"})
    with urllib.request.urlopen(req) as response:
        with open(os.path.join(JS_DIR, filename), "wb") as f:
            f.write(response.read())

# 2. Download FontAwesome CSS and Webfonts
print("Downloading FontAwesome...")
fa_css_url = "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css"
fa_css_path = os.path.join(CSS_DIR, "fontawesome.min.css")
req = urllib.request.Request(fa_css_url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"})
with urllib.request.urlopen(req) as response:
    with open(fa_css_path, "wb") as f:
        f.write(response.read())

with open(fa_css_path, "r", encoding="utf-8") as f:
    fa_css = f.read()

# FontAwesome fonts usually in ../webfonts/
webfonts_urls = set(re.findall(r'url\(([^)]+)\)', fa_css))
print(webfonts_urls)
for w_url in webfonts_urls:
    # Handle paths like '../webfonts/fa-solid-900.woff2'
    w_url = w_url.strip("'\"")
    if '?' in w_url:
        w_url = w_url.split('?')[0]
    if '#' in w_url:
        w_url = w_url.split('#')[0]
    
    if "webfonts/" in w_url:
        font_name = os.path.basename(w_url)
        # FontAwesome base url
        full_url = f"https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/webfonts/{font_name}"
        font_path = os.path.join(FONTS_DIR, font_name)
        if not os.path.exists(font_path):
            print(f"  Fetching {full_url} -> {font_name}")
            try:
                req = urllib.request.Request(full_url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"})
                with urllib.request.urlopen(req) as response:
                    with open(font_path, "wb") as f:
                        f.write(response.read())
            except Exception as e:
                print(f"  Failed to fetch {full_url}: {e}")

# Fix CSS paths
fa_css = fa_css.replace("../webfonts/", "../fonts/")
with open(fa_css_path, "w", encoding="utf-8") as f:
    f.write(fa_css)

# 3. Download Google Fonts
print("Downloading Google Fonts...")
# Request Google Fonts API with a modern user agent to get WOFF2
req = urllib.request.Request(
    "https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Manrope:wght@700;800&display=swap",
    headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36"}
)
with urllib.request.urlopen(req) as response:
    gfonts_css = response.read().decode("utf-8")

gfont_urls = set(re.findall(r'url\((https://fonts.gstatic.com/[^)]+)\)', gfonts_css))
for g_url in gfont_urls:
    font_filename = g_url.split("/")[-1]
    # To avoid naming collisions, we hash the url or use parts of it, but woff2 filename is mostly unique
    font_path = os.path.join(FONTS_DIR, font_filename)
    if not os.path.exists(font_path):
        print(f"  Fetching {g_url} -> {font_filename}")
        try:
            req = urllib.request.Request(g_url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"})
            with urllib.request.urlopen(req) as response:
                with open(font_path, "wb") as f:
                    f.write(response.read())
        except Exception as e:
            print(f"  Failed to fetch {g_url}: {e}")
    
    # Replace url in CSS
    gfonts_css = gfonts_css.replace(g_url, f"../fonts/{font_filename}")

with open(os.path.join(CSS_DIR, "google_fonts.css"), "w", encoding="utf-8") as f:
    f.write(gfonts_css)

# 4. Default Avatar SVG
avatar_svg = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
  <rect width="100" height="100" fill="#171f33"/>
  <text x="50%" y="50%" font-family="Arial" font-size="40" font-weight="bold" fill="#bac3ff" text-anchor="middle" dy=".3em">U</text>
</svg>"""

with open(os.path.join(IMG_DIR, "default_avatar.svg"), "w", encoding="utf-8") as f:
    f.write(avatar_svg)

print("All assets downloaded successfully.")
