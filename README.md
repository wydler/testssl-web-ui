# testssl-web-ui

Ein webbasiertes Frontend für [testssl.sh](https://github.com/testssl/testssl.sh). Die Anwendung führt TLS-/SSL-Tests über eine einfache Weboberfläche aus und zeigt die Ergebnisse direkt im Browser an.

## Funktionen

- Zertifikats- und Server-Standardtests sowie normale und vollständige Scans
- Optionaler STARTTLS-Test für FTP, SMTP, POP3, IMAP, XMPP, Telnet und LDAP
- Live-Ausgabe des Scan-Ergebnisses im Browser
- Alpine-Docker-Image

## Image lokal bauen

Die verwendete testssl.sh-Version steht in [`testsslsh.version`](./testsslsh.version). Beim Build wird diese Version aus dem offiziellen testssl.sh-Repository geladen. Der folgende Befehl verwendet den derzeit eingetragenen Versionswert:

```sh
docker build \
  --file build/alpine/Dockerfile \
  --build-arg APP_VERSION=v3.2.4 \
  --build-arg DOCKER_IMAGE_VERSION=local \
  --tag testssl-web-ui:master .
```

Beim Aktualisieren von `testsslsh.version` den Wert von `APP_VERSION` entsprechend anpassen.

## Container starten

```sh
docker run --detach \
  --name testssl-web-ui \
  --publish 5000:5000 \
  testssl-web-ui:master
```

Anschließend ist die Oberfläche unter <http://localhost:5000> erreichbar.

## Anwendung verwenden

1. Den Hostnamen des zu testenden Servers eingeben.
2. Port, Scan-Typ und bei Bedarf STARTTLS-Protokoll auswählen.
3. Bestätigen, dass eine Berechtigung zum Testen des Zielsystems vorliegt, und den Test starten.


## Konfiguration

Die folgenden Variablen können beim Start des Containers gesetzt werden:

| Variable | Standardwert | Bedeutung |
| --- | --- | --- |
| `TEST_TIMEOUT` | `300` | Maximale Laufzeit eines Tests in Sekunden. Zulässig sind positive Ganzzahlen bis einschließlich `3600`. |
| `UWSGI_PROCESSES` | `4` | Anzahl der uWSGI-Prozesse. |
| `UWSGI_THREADS` | `2` | Anzahl der Threads pro uWSGI-Prozess. |
| `TESTSSLDEBUG` | `0` | Debug-Stufe für testssl.sh; höhere Werte aktivieren zusätzliche Debug-Ausgaben. |
| `SECRET_KEY` | wird beim Start generiert | Flask-Schlüssel für die Anwendungssitzung. Für dauerhafte Installationen kann ein eigener, zufälliger Wert gesetzt werden. |

Beispiel:

```sh
docker run --detach \
  --name testssl-web-ui \
  --publish 5000:5000 \
  --env TEST_TIMEOUT=600 \
  --env UWSGI_PROCESSES=2 \
  --env UWSGI_THREADS=2 \
  --env SECRET_KEY='replace-with-a-long-random-secret' \
  testssl-web-ui:master
```

## Sicherheit und Betrieb

Die Anwendung kann Netzwerkverbindungen zu den eingegebenen Zielen herstellen. Betreibe sie daher nur in einer vertrauenswürdigen Umgebung und veröffentliche sie nicht ungeschützt im Internet. Scanne ausschließlich Systeme, für die eine ausdrückliche Berechtigung vorliegt. Die Oberfläche verlangt dafür eine Bestätigung vor jedem Test.

Der Container benötigt Netzwerkzugriff auf die zu testenden Ziele. Ohne vorgegebene IP wird außerdem DNS-Auflösung benötigt. Tests können je nach Scan-Typ und Ziel mehrere Minuten dauern.

## Automatischer Image-Build

Der GitHub-Actions-Workflow [`build.docker.images.yml`](./.github/workflows/build.docker.images.yml) baut und veröffentlicht bei Releases. Für manuelle Ausführungen müssen die im Workflow genannten Repository-Variablen und Registry-Zugangsdaten konfiguriert sein.

## Lizenz

Dieses Projekt steht unter der [GNU General Public License Version 3](./LICENSE). testssl.sh ist ein separates Projekt und unterliegt dessen eigener Lizenz.
