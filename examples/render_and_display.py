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


def render_image(line1: str, line2: str) -> str:
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

    def centered_text(y, text, f, fill):
        bbox = draw.textbbox((0, 0), text, font=f)
        w = bbox[2] - bbox[0]
        draw.text(((240 - w) / 2, y), text, font=f, fill=fill)

    cyan = (0, 255, 255)
    centered_text(60, line1, font(64), cyan)
    centered_text(140, line2, font(64), cyan)

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
    path = render_image(str(data.get("line1", "-")), str(data.get("line2", "-")))
    print("Bild gespeichert:", path)
    upload_and_activate(path)
