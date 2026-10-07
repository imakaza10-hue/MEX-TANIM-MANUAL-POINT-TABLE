from flask import Flask, render_template, request, jsonify, send_from_directory
from PIL import Image, ImageDraw, ImageFont
import os

BASE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR = os.path.join(BASE, "templates")
OUTPUT_DIR = os.path.join(BASE, "output")

os.makedirs(OUTPUT_DIR, exist_ok=True)

app = Flask(__name__)

FONT_PATHS = [
    "/system/fonts/RobotoCondensed-Bold.ttf",
    "/system/fonts/Roboto-Bold.ttf",
    "/system/fonts/NotoSans-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
]

POSITION_POINTS = {
    1: 12,
    2: 9,
    3: 8,
    4: 7,
    5: 6,
    6: 5,
    7: 4,
    8: 3,
    9: 2,
    10: 1,
    11: 0,
    12: 0
}


def font(size):
    for path in FONT_PATHS:
        try:
            if os.path.exists(path):
                return ImageFont.truetype(path, size)
        except:
            pass

    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


def clean(value):
    return str(value or "").strip()


def centered(draw, xy, text, f, fill):
    box = draw.textbbox((0, 0), text, font=f)

    w = box[2] - box[0]
    h = box[3] - box[1]

    draw.text(
        (xy[0] - w / 2, xy[1] - h / 2),
        text,
        font=f,
        fill=fill
    )


def fit_text(draw, text, max_width, start_size, min_size=12):
    size = start_size

    while size >= min_size:
        f = font(size)

        box = draw.textbbox(
            (0, 0),
            text,
            font=f
        )

        if box[2] <= max_width:
            return f

        size -= 1

    return font(min_size)


def normalize_rows(rows):

    result = []

    for r in rows[:12]:

        team = clean(r.get("team", ""))

        if not team:
            team = "TEAM"

        try:
            kill = max(0, int(float(r.get("kill", 0))))
        except:
            kill = 0

        try:
            position = int(float(r.get("position", 0)))
        except:
            position = 0

        try:
            booyah = 1 if int(float(r.get("booyah", 0))) > 0 else 0
        except:
            booyah = 0

        position_point = POSITION_POINTS.get(position, 0)

        total = kill + position_point + booyah

        result.append({
            "team": team,
            "booyah": booyah,
            "kill": kill,
            "position": position,
            "position_point": position_point,
            "total": total
        })

    result.sort(
        key=lambda x: (
            x["total"],
            x["booyah"],
            x["kill"]
        ),
        reverse=True
    )

    return result


def render_premium1(rows):

    path = os.path.join(
        TEMPLATE_DIR,
        "premium1.png"
    )

    if not os.path.exists(path):
        raise FileNotFoundError(
            "templates/premium1.png not found"
        )

    im = Image.open(path).convert("RGB")
    draw = ImageDraw.Draw(im)

    # 12 rows
    row_y = [
        164 + i * 58
        for i in range(12)
    ]

    for i in range(12):

        r = rows[i] if i < len(rows) else {}

        y = row_y[i]

        team = clean(r.get("team", ""))
        booyah = str(r.get("booyah", 0))
        kill = str(r.get("kill", 0))
        position = str(r.get("position", 0))
        total = str(r.get("total", 0))

        centered(
            draw,
            (1030, y),
            team,
            fit_text(
                draw,
                team,
                275,
                34,
                20
            ),
            "white"
        )

        centered(
            draw,
            (1190, y),
            booyah,
            font(34),
            "white"
        )

        centered(
            draw,
            (1305, y),
            kill,
            font(34),
            "white"
        )

        centered(
            draw,
            (1390, y),
            position,
            font(34),
            "white"
        )

        centered(
            draw,
            (1470, y),
            total,
            font(34),
            "white"
        )

    output = os.path.join(
        OUTPUT_DIR,
        "MEX_TANIM_PREMIUM_1.png"
    )

    im.save(output)

    return output


def render_premium2(rows):

    path = os.path.join(
        TEMPLATE_DIR,
        "premium2.png"
    )

    if not os.path.exists(path):
        raise FileNotFoundError(
            "templates/premium2.png not found"
        )

    im = Image.open(path).convert("RGB")
    draw = ImageDraw.Draw(im)

    y0 = 300
    dy = 31.2

    for i in range(12):

        r = rows[i] if i < len(rows) else {}

        y = y0 + i * dy

        centered(
            draw,
            (153, y),
            str(i + 1),
            font(30),
            (15, 20, 25)
        )

        team = clean(r.get("team", ""))

        centered(
            draw,
            (335, y),
            team,
            fit_text(
                draw,
                team,
                270,
                30,
                18
            ),
            (15, 20, 25)
        )

        centered(
            draw,
            (523, y),
            str(r.get("kill", 0)),
            font(30),
            (15, 20, 25)
        )

        centered(
            draw,
            (620, y),
            str(r.get("position", 0)),
            font(30),
            (15, 20, 25)
        )

        centered(
            draw,
            (747, y),
            str(r.get("total", 0)),
            font(30),
            (15, 20, 25)
        )

    output = os.path.join(
        OUTPUT_DIR,
        "MEX_TANIM_PREMIUM_2.png"
    )

    im.save(output)

    return output


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/render", methods=["POST"])
def render():

    data = request.get_json(force=True)

    rows = normalize_rows(
        data.get("rows", [])
    )

    premium1 = render_premium1(rows)
    premium2 = render_premium2(rows)

    return jsonify({
        "rows": rows,
        "premium1": "/output/" + os.path.basename(premium1),
        "premium2": "/output/" + os.path.basename(premium2)
    })


@app.route("/output/<path:name>")
def output(name):
    return send_from_directory(
        OUTPUT_DIR,
        name
    )


if __name__ == "__main__":

    print(
        "MEX TANIM FF POINT TABLE MAKER"
    )

    app.run(
        host="0.0.0.0",
        port=int(
            os.environ.get(
                "PORT",
                5000
            )
        ),
        debug=False
                       )
