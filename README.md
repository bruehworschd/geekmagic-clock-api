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
| `/updateLEDBrightness` | vermutlich `GET`/`POST` | LED-Helligkeit setzen | Parameter noch nicht im Detail dokumentiert |

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

## Siehe auch

- [GeekMagicClock/gif](https://github.com/GeekMagicClock/gif) — Beispiel-GIFs des Herstellers, in der Geräte-Weboberfläche selbst verlinkt.

## Lizenz

[`client.py`](./client.py) steht unter MIT. Die API-Beschreibung selbst ist reine Dokumentation eines beobachteten, nicht-dokumentierten Protokolls — keine Gewähr, dass sie auf jeder Firmware-Version oder jedem GeekMagic-Modell identisch funktioniert.
