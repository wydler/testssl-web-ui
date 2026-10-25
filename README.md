# testssl-web-ui

Ein webbasiertes Frontend für [testssl.sh](https://github.com/testssl/testssl.sh). Die Anwendung führt TLS-/SSL-Tests über eine einfache Weboberfläche aus und zeigt die Ergebnisse direkt im Browser an.

## Funktionen

- Zertifikats- und Server-Standardtests sowie normale und vollständige Scans
- Optionaler STARTTLS-Test für FTP, SMTP, POP3, IMAP, XMPP, Telnet und LDAP
- Optionaler Test nur der ersten vom DNS zurückgegebenen IP-Adresse
- Live-Ausgabe des Scan-Ergebnisses im Browser
- Download des Scan-Ergebnisses als Textdatei, clientseitig ohne Speicherung auf dem Server
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

1. Den Hostnamen des zu testenden Servers eingeben. Optional kann eine IP-Adresse angegeben werden. In diesem Fall wird diese statt der DNS-Auflösung verwendet; der Hostname bleibt für TLS/SNI erhalten.
2. Port und Scan-Typ auswählen:
   - **Server defaults and certificate expiry/chain** prüft Server-Standardeinstellungen sowie Zertifikatsablauf und -kette.
   - **Normal scan** führt den normalen Scan im IDS-freundlichen Modus aus.
   - **Full scan** schließt Schwachstellenprüfungen ein, die dazu führen können, dass ein IDS die scanende IP-Adresse blockiert.
3. Bei Bedarf STARTTLS aktivieren und das passende Protokoll auswählen.
4. Bei mehreren DNS-Adressen kann **Test only one IP address** ausgewählt werden. Dann wird nur die erste vom System gelieferte IP-Adresse getestet; weitere Adressen bzw. Server hinter dem Hostnamen werden nicht geprüft. Eine manuell eingetragene IP-Adresse hat Vorrang und wird unabhängig von dieser Option allein verwendet.
5. Bestätigen, dass eine Berechtigung zum Testen des Zielsystems vorliegt, und den Test starten.
6. Nach Abschluss kann die angezeigte Ausgabe über **Download result (.txt)** als Textdatei gespeichert werden. Der Dateiname enthält Hostname sowie lokales Datum und Uhrzeit im Format `testssl_<hostname>_<JJJJ-MM-TT>_<HH-MM-SS>.txt`. Der Download wird im Browser erstellt; die Anwendung speichert dafür keine zusätzliche Datei auf dem Server.


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

## Cosign
Cosign is a command-line tool from the Sigstore project used to sign and verify software artifacts such as container images. It enables the digital signing of artifacts to guarantee their origin and integrity. Signed artifacts can be stored in the registry, and verification is possible using public-key/private-key cryptography.

### Installation with dpkg package
```bash
LATEST_VERSION=$(curl https://api.github.com/repos/sigstore/cosign/releases/latest | grep tag_name | cut -d : -f2 | tr -d "v\", ")
curl -O -L "https://github.com/sigstore/cosign/releases/latest/download/cosign_${LATEST_VERSION}_amd64.deb"
sudo dpkg -i cosign_${LATEST_VERSION}_amd64.deb
```
[Source](https://docs.sigstore.dev/cosign/system_config/installation/#with-the-cosign-binary-or-rpmdpkg-package)

### Verifying Signature
Verify with an on-disk public key provided by the signer:
```bash
DOCKER_REPOSITORY=wydler/testssl-web-ui
GITHUB_REPOSITORY=wydler/testssl-web-ui

TAG=$(curl -fsS https://api.github.com/repos/${GITHUB_REPOSITORY}/releases | grep '"tag_name"' | cut -d'"' -f4 | head -n1)
curl -O -L https://raw.githubusercontent.com/${GITHUB_REPOSITORY}/refs/tags/${TAG}/cosign.pub

DOCKER_TOKEN=$(curl -fsS "https://auth.docker.io/token?service=registry.docker.io&scope=repository:${DOCKER_REPOSITORY}:pull" | jq -r '.token')

INDEX_DIGEST_SHA=$(curl -fsSI \
  -H "Authorization: Bearer ${DOCKER_TOKEN}" \
  -H "Accept: application/vnd.oci.image.index.v1+json" \
  "https://registry-1.docker.io/v2/${DOCKER_REPOSITORY}/manifests/${TAG}" \
  | awk -F': ' 'tolower($1)=="docker-content-digest" {print $2}' \
  | tr -d '\r'
  )

RESULT=$(cosign verify --key cosign.pub docker.io/${DOCKER_REPOSITORY}:${TAG}@${INDEX_DIGEST_SHA})
echo $RESULT | jq .

rm cosign.pub
```
Hint: The third line finds the name of the latest release on GitHub. If you want to check an older version, statically assign the desired version number to the variable `TAG` (e.g., `TAG=1.0.0`).


## Lizenz

Dieses Projekt steht unter der [GNU General Public License Version 3](./LICENSE). testssl.sh ist ein separates Projekt und unterliegt dessen eigener Lizenz.
