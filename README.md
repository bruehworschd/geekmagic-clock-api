# GeekMagic Clock API

Inoffizielle, reverse-engineerte HTTP-API-Dokumentation für GeekMagic-Pixel-Uhren (z. B. das "Smart Clock"-Modell mit Foto-Album-Funktion). Nicht offiziell von GeekMagic, keine Verbindung zum Hersteller — gefunden durch Analyse der mitgelieferten Web-Oberfläche des Geräts.

## Warum

Das Gerät hat eine kleine eingebaute Weboberfläche (Netzwerk, Wetter, Zeit, Bilder, Einstellungen), aber keine dokumentierte API. Die Endpunkte, die die Weboberfläche selbst benutzt, lassen sich aus ihrem JavaScript extrahieren — das Gerät liefert seine `.html`/`.js`-Dateien dabei **gzip-komprimiert aus**, auch ohne passenden `Content-Encoding`-Header, was `curl`/Browser teils verwirrt. Das erklärt auch, warum die Dateien beim naiven Abruf wie Binärmüll aussehen.

## Entdeckte Endpunkte

Alle Endpunkte sind einfache `GET`-Requests (außer Upload), **ohne sichtbaren Auth-Schutz** — wer im selben Netz ist, kann sie aufrufen.

| Endpunkt | Methode | Zweck | Anmerkungen |
|---|---|---|---|
| `/doUpload?dir=<pfad>` | `POST` | Bild hochladen | `multipart/form-data`, Feld `image` (Direkt-Upload) oder `file` (zugeschnittener Blob aus dem Crop-Tool der Weboberfläche) |
| `/set?img=<pfad>` | `GET` | Bild aktiv schalten | Pfad **roh**, keine URL-Kodierung nötig (z. B. `/image/foto.jpg`); schaltet das Gerät direkt in den Bild-Modus |
| `/filelist?dir=<pfad>` | `GET` | Dateien in einem Verzeichnis auflisten | Antwort ist HTML-Tabellen-Fragment, kein JSON |
| `/space.json` | `GET` | Freien Speicherplatz abfragen | JSON, Feld `free` (vermutlich Bytes) |
| `/set?clear=image` | `GET` | Alle Bilder löschen | — |
| `/delete?file=<pfad>` | `GET` | Einzelne Datei löschen | **Pfad muss URL-kodiert sein** (`encodeURIComponent`), z. B. `%2Fimage%2Ffoto.jpg` statt `/image/foto.jpg` — mit rohem Pfad antwortet das Gerät mit `Fail` statt `OK`. Inkonsistent zu `/set?img=`, das den rohen Pfad erwartet. |
| `/set?i_i=<sekunden>&autoplay=<0\|1>` | `GET` | Automatische Diashow konfigurieren | Rotiert bei `autoplay=1` selbständig durch alle Bilder im aktiven Verzeichnis, Intervall in Sekunden |
| `/scan_ssid` | `GET` | WLAN-Scan (Netzwerk-Seite) | Noch nicht im Detail getestet |
| `/v.json` | `GET` | Geräte-/Versionsinfo (vermutet) | Noch nicht im Detail dokumentiert |
| `/brt.json`, `/timebrt.json` | vermutlich `GET` | Helligkeit (allgemein/zeitgesteuert) setzen | Aus der Firmware-Analyse (siehe unten), noch nicht live gegen ein Gerät getestet — ersetzt die frühere, falsche Vermutung `/updateLEDBrightness` |
| `/update` | `POST` | OTA-Firmware-Update | Standard-Endpunkt der ESP8266HTTPUpdateServer-Bibliothek |

### Weitere Endpunkte (aus der Firmware-Analyse, noch nicht live verifiziert)

Per `strings`-Auszug aus der offiziellen Firmware-Binärdatei gefunden (siehe Abschnitt "Firmware-Analyse" unten), aber noch nicht gegen ein echtes Gerät getestet — Methode (`GET`/`POST`, Parameter) daher unbekannt:

`/album.json` · `/app.json` · `/city.json` · `/colon.json` · `/config.json` · `/day.json` · `/delay.json` · `/dst.json` · `/fkey.json` · `/font.json` · `/gif.json` · `/hour12.json` · `/img.json` · `/key.json` · `/lon.json` · `/ntp.json` · `/rotation.json` · `/theme_list.json` (ersetzt die frühere, falsche Vermutung `/themeselect?getstate=<n>`, die 404 zurückgab) · `/timecolor.json` · `/tz.json` · `/unit.json` · `/wifi.json` · `/w_i.json`

Dazu WLAN-Erstkonfiguration (Captive-Portal-Verhalten im AP-Modus, Standardmuster bei ESP8266-Geräten): `/wifisave`, `/generate_204`, `/fwlink`, `/hotspot-detect.html`.

## Beispiel: Bild hochladen und anzeigen

```bash
DEVICE_IP="<device-ip>"   # eigene Geräte-IP eintragen

# Bild muss auf 240x240px zugeschnitten sein (vom Gerät empfohlen, nicht zwingend erzwungen)
curl -F "image=@foto.jpg" "http://$DEVICE_IP/doUpload?dir=/image/"
curl "http://$DEVICE_IP/set?img=/image/foto.jpg"
```

## Beispiel: Datei löschen (URL-Encoding beachten)

```bash
curl "http://$DEVICE_IP/delete?file=%2Fimage%2Ffoto.jpg"
```

## Beispiel: Automatische Diashow aktivieren

```bash
curl "http://$DEVICE_IP/set?i_i=30&autoplay=1"
```

## Methode: eigene Endpunkte finden

Die Weboberfläche liefert ihr JavaScript gzip-komprimiert aus. So liest man es im Klartext:

```bash
curl -s "http://$DEVICE_IP/image.html" -o page.html
gunzip -c page.html > page_decoded.html 2>/dev/null
cat page_decoded.html
```

Dasselbe funktioniert für andere Seiten (`settings.html`, `network.html`, `weather.html`, `time.html`) und deren eingebundene `.js`-Dateien.

## Firmware-Analyse (strings-Auszug, keine Dekompilierung)

Der Hersteller stellt fertige Firmware-Binärdateien selbst öffentlich bereit: [GeekMagicClock/smalltv-ultra](https://github.com/GeekMagicClock/smalltv-ultra) (inkl. `md5sum.txt` zur Integritätsprüfung). Ein reiner `strings`-Auszug aus dieser `.bin`-Datei (keine Disassemblierung/Dekompilierung, nur lesbare Textfragmente extrahieren) legt alle vom Gerät intern verwendeten Pfade offen, auch solche, die die Weboberfläche nicht direkt referenziert:

```bash
strings -n 6 FW-Smalltv-Ultra-VX.X.XX.bin | grep -E '^/[a-zA-Z_][a-zA-Z0-9_/.]*$' | sort -u
```

Firmware läuft auf **ESP8266** (laut enthaltener Fehlermeldung "Firmware ONLY supports ESP8266!!!"), Arduino-Core. Bei diesem Auszug wurden **keine Passwörter, Tokens oder sonstigen Zugangsdaten** im Klartext gefunden — passt zum Befund, dass die HTTP-API keinerlei sichtbaren Auth-Schutz hat.

## Bekannte Fallstricke

- **`/set?img=` überschreibt eine extern gesteuerte Rotation.** Falls das Gerät schon über eine andere Automatisierung läuft (z. B. eine Home-Assistant-Integration mit mehreren rotierenden Widgets/Views), schaltet ein eigener `/set?img=`-Aufruf das Gerät fest auf dieses eine Bild um — die bestehende Rotation läuft danach nicht von selbst weiter. Vor eigener Automatisierung prüfen, ob das Gerät schon anderweitig gesteuert wird.
- **Pillow-Font-Fallback-Falle beim eigenen Bild-Rendern:** `ImageFont.truetype()` mit einem hartcodierten Schriftart-Pfad (z. B. DejaVu) schlägt auf vielen Systemen fehl, weil die Datei dort schlicht nicht existiert. Ein `except OSError: return ImageFont.load_default()` als Fallback **ohne Größenangabe** ignoriert dabei jede gewünschte Schriftgröße — alle Texte landen gleich (winzig) groß, unabhängig vom übergebenen `size`-Parameter. Fix: neuere Pillow-Versionen (≥10.1) können den eingebauten Default-Font direkt skalieren — `ImageFont.load_default(size=64)` funktioniert ganz ohne externe Schriftdatei. Siehe [`examples/render_and_display.py`](examples/render_and_display.py).

## Beispielskript

[`examples/render_and_display.py`](examples/render_and_display.py) — holt Werte von einer beliebigen JSON-Quelle, rendert daraus ein 240×240-Dashboard-Bild und lädt es automatisch hoch + aktiviert es. Als Ausgangspunkt gedacht, nicht als fertige Lösung.

## Siehe auch

- [GeekMagicClock/gif](https://github.com/GeekMagicClock/gif) — Beispiel-GIFs des Herstellers, in der Geräte-Weboberfläche selbst verlinkt.

## Lizenz

[`client.py`](./client.py) steht unter MIT. Die API-Beschreibung selbst ist reine Dokumentation eines beobachteten, nicht-dokumentierten Protokolls — keine Gewähr, dass sie auf jeder Firmware-Version oder jedem GeekMagic-Modell identisch funktioniert.
