from flask import Flask, render_template, request, jsonify, send_from_directory
from PIL import Image, ImageDraw, ImageFont
import os, uuid

BASE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR = os.path.join(BASE, "templates")
OUTPUT_DIR = os.path.join(BASE, "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

app = Flask(__name__)
FONT_PATHS = [
    # Android / Termux fonts first
    "/system/fonts/RobotoCondensed-Bold.ttf",
    "/system/fonts/Roboto-Bold.ttf",
    "/system/fonts/NotoSans-Bold.ttf",
    # Linux fallback
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
]

def font(size):
    for path in FONT_PATHS:
        try:
            if os.path.exists(path):
                return ImageFont.truetype(path, size)
        except:
            pass
    # Newer Pillow can scale its built-in font. This avoids the tiny text
    # caused by ImageFont.load_default() on Termux when no system font is found.
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()

def clean(s):
    return str(s or "").strip()

def centered(draw, xy, text, f, fill, stroke_width=0):
    box = draw.textbbox((0, 0), text, font=f)
    w = box[2] - box[0]
    h = box[3] - box[1]
    draw.text((xy[0] - w/2, xy[1] - h/2), text, font=f, fill=fill, stroke_width=stroke_width, stroke_fill=fill)

def fit_text(draw, text, max_width, start_size, min_size=12):
    size = start_size
    while size >= min_size:
        f = font(size)
        if draw.textbbox((0,0), text, font=f)[2] <= max_width:
            return f
        size -= 1
    return font(min_size)

def normalize_rows(rows):
    out = []
    for i, r in enumerate(rows[:12]):
        team = clean(r.get("team", ""))
        if not team:
            continue
        try:
            kill = int(float(r.get("kill", 0)))
        except:
            kill = 0
        try:
            pos = int(float(r.get("position", 0)))
        except:
            pos = 0
        try:
            booyah = int(float(r.get("booyah", 0)))
        except:
            booyah = 0

        # User-requested scoring: Total = Kill + Position.
        total = kill + pos
        out.append({
            "team": team,
            "kill": kill,
            "position": pos,
            "booyah": booyah,
            "total": total,
        })

    # Sorting priority:
    # 1) Total descending
    # 2) Booyah first (a team with Booyah ranks above a team with no Booyah)
    # 3) Kill/Elims descending
    # 4) Position descending
    #
    # This also handles ties where 2 or 3 teams have the same Total:
    # if Booyah is tied (including 0-0), higher Kill ranks first.
    out.sort(key=lambda r: (r["total"], r["booyah"], r["kill"], r["position"]), reverse=True)
    return out

def render_premium1(rows):
    path = os.path.join(TEMPLATE_DIR, "premium1.png")
    im = Image.open(path).convert("RGB")
    d = ImageDraw.Draw(im)

    # Coordinates match the supplied premium-1 template.
    row_y = [164 + i*58 for i in range(12)]
    for i in range(12):
        r = rows[i] if i < len(rows) else {}
        y = row_y[i]
        d.rectangle((874, y-21, 1495, y+21), fill=(17,159,236))
        team = clean(r.get("team",""))
        booyah = str(r.get("booyah",0))
        kill = str(r.get("kill",0))
        pos = str(r.get("position",0))
        total = str(r.get("total",0))

        centered(d, (1030, y), team, fit_text(d, team, 275, 34, 24), "white", stroke_width=1)
        centered(d, (1190, y), booyah, font(34), "white", stroke_width=1)
        centered(d, (1305, y), kill, font(34), "white", stroke_width=1)
        centered(d, (1390, y), pos, font(34), "white", stroke_width=1)
        centered(d, (1470, y), total, font(34), "white", stroke_width=1)

    out = os.path.join(OUTPUT_DIR, "MEX_TANIM_PREMIUM_1.png")
    im.save(out)
    return out

def render_premium2(rows):
    path = os.path.join(TEMPLATE_DIR, "premium2.png")
    im = Image.open(path).convert("RGB")
    d = ImageDraw.Draw(im)

    y0, dy = 300, 31.2
    for i in range(12):
        r = rows[i] if i < len(rows) else {}
        y = y0 + i*dy
        centered(d, (153, y), str(i+1), font(30), (15,20,25), stroke_width=1)
        team = clean(r.get("team",""))
        centered(d, (335, y), team, fit_text(d, team, 270, 30, 22), (15,20,25), stroke_width=1)
        centered(d, (523, y), str(r.get("kill",0)), font(30), (15,20,25), stroke_width=1)
        centered(d, (620, y), str(r.get("position",0)), font(30), (15,20,25), stroke_width=1)
        centered(d, (747, y), str(r.get("total",0)), font(30), (15,20,25), stroke_width=1)

    out = os.path.join(OUTPUT_DIR, "MEX_TANIM_PREMIUM_2.png")
    im.save(out)
    return out

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/render", methods=["POST"])
def render():
    data = request.get_json(force=True)
    rows = normalize_rows(data.get("rows", []))
    p1 = render_premium1(rows)
    p2 = render_premium2(rows)
    return jsonify({
        "rows": rows,
        "premium1": "/output/" + os.path.basename(p1),
        "premium2": "/output/" + os.path.basename(p2)
    })

@app.route("/output/<path:name>")
def output(name):
    return send_from_directory(OUTPUT_DIR, name)

if __name__ == "__main__":
    print("MEX TANIM FF POINT TABLE MAKER")
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)
