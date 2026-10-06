#!/usr/bin/env python3
"""Beispiel: beliebige JSON-Messwerte als 240x240-Bild rendern und auf die Uhr pushen.

Holt Daten von einer beliebigen JSON-Quelle (z.B. einem anderen Sensor im eigenen
Netz), rendert sie als simples Dashboard und laedt das Ergebnis per /doUpload
hoch, danach per /set?img= aktiv geschaltet.

Nur ein Beispiel/Ausgangspunkt -- an die eigene Datenquelle und das gewuenschte
Layout anpassen.
"""
import json
import urllib.request
from PIL import Image, ImageDraw, ImageFont

DATA_SOURCE_URL = "http://<sensor-ip>/data.json"  # eigene JSON-Quelle eintragen
CLOCK_IP = "<device-ip>"
OUT_PATH = "/tmp/dashboard.jpg"


def fetch_values():
    with urllib.request.urlopen(DATA_SOURCE_URL, timeout=10) as r:
        return json.loads(r.read())


def render_image(values: dict) -> str:
    """values: dict mit genau 4 Eintraegen {label: (wert, einheit)}, z.B.
    {"PM10": ("7.53", ""), "PM2.5": ("2.97", ""), "Temp": ("20", "C"), "Feuchte": ("51", "%")}
    """
    img = Image.new("RGB", (240, 240), color=(10, 10, 15))
    draw = ImageDraw.Draw(img)

    # Wichtig: ImageFont.truetype() mit hartcodiertem Font-Pfad schlaegt auf
    # vielen Systemen fehl (DejaVu o.ae. ist nicht ueberall installiert), und
    # der Fallback auf ImageFont.load_default() OHNE Groessenangabe ignoriert
    # jede gewuenschte Groesse -- Ergebnis: alle Texte gleich winzig, kaum
    # lesbar auf dem kleinen Display. Neuere Pillow-Versionen (>=10.1) koennen
    # den eingebauten Default-Font aber direkt skalieren:
    def font(size):
        return ImageFont.load_default(size=size)

    cyan = (0, 255, 255)
    dim = (140, 230, 230)
    f_label = font(16)
    f_value = font(38)

    def tile(cx, cy, label, value, unit=""):
        bbox_l = draw.textbbox((0, 0), label, font=f_label)
        lw = bbox_l[2] - bbox_l[0]
        draw.text((cx - lw / 2, cy - 44), label, font=f_label, fill=dim)

        text = f"{value}{unit}"
        bbox_v = draw.textbbox((0, 0), text, font=f_value)
        vw = bbox_v[2] - bbox_v[0]
        draw.text((cx - vw / 2, cy - 22), text, font=f_value, fill=cyan)

    # 2x2-Raster -- Reihenfolge: oben-links, oben-rechts, unten-links, unten-rechts
    positions = [(60, 70), (180, 70), (60, 170), (180, 170)]
    for (cx, cy), (label, (value, unit)) in zip(positions, values.items()):
        tile(cx, cy, label, value, unit)

    draw.line([(120, 20), (120, 220)], fill=(0, 80, 80), width=1)
    draw.line([(20, 120), (220, 120)], fill=(0, 80, 80), width=1)

    img.save(OUT_PATH, "JPEG", quality=90)
    return OUT_PATH


def upload_and_activate(img_path: str):
    boundary = "----dashupload"
    with open(img_path, "rb") as f:
        file_bytes = f.read()
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="image"; filename="dashboard.jpg"\r\n'
        f"Content-Type: image/jpeg\r\n\r\n"
    ).encode() + file_bytes + f"\r\n--{boundary}--\r\n".encode()

    req = urllib.request.Request(
        f"http://{CLOCK_IP}/doUpload?dir=/image/",
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=20) as r:
        print("Upload:", r.read().decode(errors="replace"))

    with urllib.request.urlopen(f"http://{CLOCK_IP}/set?img=/image/dashboard.jpg", timeout=10) as r:
        print("Activate:", r.read().decode(errors="replace"))


if __name__ == "__main__":
    data = fetch_values()
    # Beispielhafte Extraktion -- an eigenes JSON-Format anpassen
    values = {
        "Wert A": (str(data.get("a", "-")), ""),
        "Wert B": (str(data.get("b", "-")), ""),
        "Wert C": (str(data.get("c", "-")), ""),
        "Wert D": (str(data.get("d", "-")), ""),
    }
    path = render_image(values)
    print("Bild gespeichert:", path)
    upload_and_activate(path)
