# Logistic.01

## Beschreibung
Ein Projekt, um das Nachbestellen von elektronischen Bauteilen in der Area.01 zu vereinfachen.

## To-do:
- Refactoring
    - [ ] settings.py vereinfachen
    - [x] ScannerView nicht in der main.py
- Features
    - [x] Excert TreeView From Settings for better overview
    - [ ] Ceos Anzahl übergeben (in der URL)
    - [ ] Dateiüberwachung der config.json
    - [ ] Daten in SQLite speichern

## Planned
- v0.2.0 SQLite
    - Daten in SQLite speichern
- v0.3.0 verschiedene Views über Browser artige Sidebar (Scanner, Suche?, Übersicht, Settings)

## Funktionen
- Benutzeroberfläche zum Verwalten von Einträgen
- Liste mit derzeitig relevanten Einträgen.
    - Hinzufügen durch Scannen von DMC- oder Barcodes oder
    - Textsuche nach Einträgen
- Anzeige von Informationen über das Bauteil
    - ID, Namen und Hersteller des Bauteiles
    - Links zur wichtigen Webseite des Bauteils
    - Vorhandede Stückzahl
- Exportieren der Liste, z.B. als Einkaufsliste
- Konfigurierbare Spalten (TODO)
- Mehrere Lagerorte pro Eintrag aus selbstdefinierter Liste (TODO)
- Einträge können erstellt, bearbeitet und gelöscht werden
- Handbuch mit Anleitung zur Nutzung
- Mehrere Personen können an einer Datenbank/Excel arbeiten. Schreibt nur reihenweise, Synchronisierung über z.B. OneDrive

## Herunterladen
Gehe zur release-Seite und lade die aktuelle Version herunter.
Es ist nur ein Windows x86 Portable Version verfügbar.
Das Programm ist aber plattformunabhängig, einfach die Anweisungen zum Einrichten folgen.


Da dieses Programm zum gemeinsamen Verwalten von einem Lager ist gibt es gibt zwei wichtige Dateien außerhalb des Programmes:
- config.json: Diese Datei enthält die Konfiguration für die Anwendung, wie z.B. die Lagerorte. Wenn nicht vorhanden wird eine neue leere Datei angelegt.
- db.xlsx: Die 'Datenbank' in der alle Einträge sind. Es gibt noch keinen Weg eine neue vom Programm generieren zu lassen. Siehe unten zum Manuellen anlegen.

Diese beiden Dateien sollten vom Team geteilt werden. Nach der Excel Datei wird bei Programmstart gefragt, die Konfigurationsdatei muss neben das Programm in den Ordner gelegt werden (Während das Programm NICHT läuft).
Die config.json wird in der Zukunft in die Datenbank aufgenommen, wenn zu einer besseren Datenbank als Excel gewechselt wird.

Auf die Inhalte der beiden Dateien muss nicht zugegriffen werden, es ist alles über das Programm einstellbar und veränderbar.


## Projekt einrichten
### Voraussetzungen
Lade den Zip-Ordner herunter und entpacke ihn.
Alternativ kannst du mit folgendem Befehl das Repository in den jetzigen Ordner klonen:
```sh
$ git clone https://github.com/UltimateResistor/Logistic.01.git
```

Installiere die benötigten Python-Pakete mit folgendem Befehl:
```sh
$ pip install -r ./requirements.txt
```

### Ausführen des Programmes
Der Einstiegspunkt des Programms ist die Datei _main.py_.
Die _main.py_ Datei kann mit folgendem Befehl ausgeführt werden:
```sh
$ python main.py
```
Sie enthält die grafische Oberfläche. Das Textfeld ist bereits fokussiert. Einfach mit dem Scanner einen Code einscannen und das Ergebnis wird angezeigt.

## Code-Struktur
Der Logik für das Hauptansicht des Programms ist in dem main Modul geschrieben.
Die alle Typ-Definitionen für den Zustand des Programmes sind im state Modul definiert.
Die anderen Dateien enthalten einzelne Features, die in der _main.py_ Datei verwendet werden.

### Startablauf
Das Programm startet in der main() Funktion im main Modul (main.py).
Zuerst wird eine QApplication erstellt, dass ist der Kontext für die UI-Libary. Diese wird nicht nur für das Hauptfenster gebraucht, sondern auch für Popups und Dialoge.
Als nächstes werden die Einstellungen von den Datei config.json und settings.json geladen und im Settings Struct gespeichert.
Dann werden die daten aus der Excel-Datei geladen in das Data Struct geladen.
Das GUI wird erstellt und mit den Daten gefüllt.
Alle anderen Funktionen werden über UI-Events aufgerufen.

### main
Enthält die Logik für den Start und die Hauptansicht des Programms.
Das UI ist dreigeteilt: Ein Menu, eine Tabelle und ein Input-Leiste.
Jeder dieser Teile hat eine eigene Update-Funktion, die alle Änderungen an dem UI durchführt.
Änderungen außerhalb dieser Funktionen sind nicht erwünscht, da sie schwierig zum Nachvollziehen sind.


### state
Enthalten alle Structs, die den Zustand des Programmes enthalten.
Diese werden in der main Funktion initialisiert und an alle weiteren Funktionen übergeben.
Das State Structs enthält Referenzen zu allen anderen Structs, sodass auf sie über das State Struct zugegriffen werden kann.
Dadurch nehmen die meisten Funktionen nur den State Struct als Parameter und nicht die anderen Structs.
Wenn nur ein bestimmter Teil des Zustands gebraucht wird (z.B. nur das Data Struct), dann kann auch nur dieser als Parameter übergeben werden.

### db
Das db Modul enthält Funktionen und Abstrahierung zur Kommunikation mit der Datenbank, bzw. der Excel-Datei.

### consts
Konstanten, die für das Programm benötigt werden.
Können von überall verwendet werden, dürfen aber nicht verändert werden.

### entries
Erstellen und Bearbeiten von Einträgen in der Datenbank.

### fileActions
Überprüfen von Pfaden und Auswählen von Dateien.

### qrGenerator
Erzeugen von QR-Codes.

### search
Fuzzy-Suche für Einträge in der Datenbank.

### settings
Laden, Speichern und Bearbeiten von Einstellungen.
