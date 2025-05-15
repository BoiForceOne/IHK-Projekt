# Logistics.01 - Handbuch

## Einführung
Willkommen bei Logistic.01! Diese Anwendung hilft Ihnen, Barcodes und QR-Codes zu scannen, Einträge zu verwalten und Daten in einer übersichtlichen Tabelle anzuzeigen, das alles mit dem Ziel Nachbestellungen zu erleichtern. Dieses Handbuch führt Sie durch die grundlegenden Funktionen und die Bedienung der Anwendung.

## Hauptfunktionen
- Benutzeroberfläche zum Verwalten von Einträgen
- Liste mit derzeitig relevanten Einträgen.
    - Hinzufügen durch Scannen von DMC- oder Barcodes oder
    - Textsuche nach Einträgen
- Anzeige von Informationen über das Bauteil
    - ID, Namen und Hersteller des Bauteiles
    - Links zur wichtigen Webseite des Bauteils
    - Vorhandede Stückzahl
- Exportieren der Liste, z.B. als Einkaufsliste im Excel Format
- Einträge können erstellt, bearbeitet und gelöscht werden
- Handbuch mit Anleitung zur Nutzung
## Bedienungsanleitung
### 1. Starten der Anwendung
Öffnen Sie die Anwendung durch Doppelklick auf die Datei Logistic.01.
Das Hauptfenster der Anwendung wird angezeigt.
- Fehlersuche:
  	+ Excel-Datei: Falls Fehler auftreten, kann dies an einer fehlenden, verschobenen oder veralteten Excel-Datei liegen. Nutzen Sie die Suchfunktion für die Excel-Datei, die sich bei einem Start ohne gültige Excel-Datei automatisch öffnet. Stellen Sie sicher, dass die Datei die erforderlichen Spalten (ID, Code, Typ) enthält und keine Spalten wie Delete, Edit oder Count.
  + Konfigurationsdateien: Bei Problemen mit den Konfigurationsdateien löschen Sie die Datei manuell und laden sie neu herunter oder installieren Sie das Programm neu.
### 2. Scannen von Codes
Geben Sie den zu scannenden Code in das Textfeld ein und drücken Sie die Eingabetaste oder scannen Sie den Code direkt.
Der gescannte Code wird der Liste der gescannten IDs hinzugefügt. Nutzen Sie den Multiplikator rechts unten nach dem "x", um größere Mengen durch einen Scan zu erfassen. Der Multiplikator kann im Programm eingestellt oder durch Scannen von Multiplikator Data Matrix Codes geändert werden. Sie können die Anzahl der gescannten Objekte auch nachträglich in der Tabelle ändern.
+ Fehlersuche:
Stellen Sie sicher, dass der Fokus auf der Eingabeleiste gesetzt ist (blinkender Cursor) und der Scanner verbunden ist.
### 3. Verwalten von Einträgen
- Bearbeiten eines Eintrags:
Klicken Sie auf das Stiftsymbol (✏️) neben dem Eintrag, den Sie bearbeiten möchten.
Nehmen Sie die gewünschten Änderungen vor und speichern Sie diese. Sie können einen Eintrag auch vollständig aus der Datenbank löschen. Diese Aktion kann nicht rückgängig gemacht werden.

- Entfernen eines Eintrags:
Klicken Sie auf das Papierkorbsymbol (🗑️) neben dem Eintrag, den Sie aus der Liste entfernen möchten. Der Eintrag wird aus der Ansicht entfernt und nicht in die Einkaufs-Excel-Datei gespeichert.
### 4. Speichern und Laden
- Speichern in Excel-Datei:
Klicken Sie auf das Diskettensymbol (💾) in der Menüleiste.
Wählen Sie den Speicherort und den Dateinamen aus und speichern Sie die Datei. Sie haben nun eine fertige Einkaufsliste mit allen nötigen Informationen für ein eventuelles Nachbestellen.
- Laden von verschiedenen Beständen:
Klicken Sie auf das Zahnradsymbol (⚙️) in der Menüleiste für die Einstellungen.
Wählen Sie den Pfad der neuen Excel-Datei aus und speichern Sie die Einstellungen. Die Einträge aus dieser Datei werden in der Anwendung geladen.
- Fehlersuche:
Falls der angegebene Pfad ungültig ist, können die Einstellungen nicht gespeichert werden. Eine Nachricht weist Sie darauf hin, und eine rote Markierung erscheint um die Eingabeleiste für den Excel-Pfad. Beachten Sie die gleichen Hinweise wie bei der Fehlersuche beim Start der Anwendung.
### 5. Menüleiste
- Einstellungen: Klicken Sie auf das Zahnradsymbol (⚙️) in der Menüleiste, um die Einstellungen nach Ihren Wünschen anzupassen.
- Hilfe: Klicken Sie auf das Fragezeichensymbol (❔) in der Menüleiste, um Hilfe zu erhalten. Bei weiteren Fragen wenden Sie sich bitte an *area.01*.
- Alle Artikel entfernen: Klicken Sie auf das rote X (❌), um alle Artikel aus der gescannten Liste zu entfernen.
- Speichern in Excel-Datei: Klicken Sie auf das Diskettensymbol (💾), um die Liste zu speichern (siehe Speichern).
- Einträge hinzufügen: Klicken Sie auf das blaue Plus (➕), um Einträge in die Datenbank hinzuzufügen.
- Objektsuche: Klicken Sie auf die Lupe (🔍), um nach bestimmten Teilen zu suchen. Durch Klicken auf "Add" wird das Teil der gescannten Liste hinzugefügt.

### 6. Einstellungen
  #### Einführung
  Der folgende Teil erklärt, wie Sie die Einstellungen der Anwendung "Logistic.01" anpassen können. Die Einstellungen ermöglichen es Ihnen, die Anwendung nach Ihren Bedürfnissen zu konfigurieren, einschließlich der Verwaltung von Lagerorten und der Festlegung des Dateipfads.

  #### Hauptfunktionen
  Dateipfad festlegen: Wählen Sie die Excel-Datei, in der die Daten gespeichert werden.
  Lagerorte verwalten: Fügen Sie neue Lagerorte hinzu, benennen Sie sie um oder löschen Sie sie.

  #### Dateipfad festlegen
  Klicken Sie auf die Schaltfläche "Datei auswählen" neben dem Textfeld "Datei-Pfad".
  Wählen Sie die gewünschte Excel-Datei aus dem Dateidialog aus.
  Der Pfad zur ausgewählten Datei wird für ihre Überprüfung im Textfeld angezeigt.

  #### Lagerorte verwalten
  - Lagerort hinzufügen:
  Lagerorte sind die höchste Ebene der Hierarchie, zum Beispiel Kellerlager 1 oder Abstelllager 1.
  Klicken Sie auf die Schaltfläche "Hinzufügen". Geben Sie den Namen des neuen Lagerorts ein und bestätigen Sie. Falls bereits ein Lagerort mit diesem Namen existiert, wird eine Warnung angezeigt. 

  - Unterteilung hinzufügen:
  Wählen Sie einen bestehenden Lagerort aus der Baumansicht aus.
  Klicken Sie auf die Schaltfläche "Unterteilung hinzufügen".
  Geben Sie den Namen der neuen Unterteilung ein und bestätigen Sie.

  - Lagerort umbenennen:
  Wählen Sie den Lagerort aus der Baumansicht aus, den Sie umbenennen möchten.
  Klicken Sie auf die Schaltfläche "Unbenennen".
  Geben Sie den neuen Namen ein und bestätigen Sie.

  - Lagerort löschen:
  Wählen Sie den Lagerort aus der Baumansicht aus, den Sie löschen möchten.
  Klicken Sie auf die Schaltfläche "Löschen".
  Bestätigen Sie die Löschung.

  - Drag and drop:
  Sie können außerdem eine Unterteilung in einen anderen Lagerort verschieben, indem Sie die Unterteilung mit der Maus in den     Zielort ziehen.

  - Multi-Selection:
  Durch shift + klick oder durch das auswählen der Multi-Selection können Sie mehrere Einträge, zum Beispiel zum löschen,  auswählen.

  #### Änderungen speichern oder abbrechen
  - Speichern:
  Klicken Sie auf die Schaltfläche "Speichern", um alle Änderungen zu speichern.
  Eine Bestätigungsmeldung wird angezeigt, wenn die Einstellungen erfolgreich gespeichert wurden.

  - Abbrechen:
  Klicken Sie auf die Schaltfläche "Abbrechen" oder auf den Zurück-Knopf mit dem Haus-Symbol (🏠), um die Einstellungen zu verlassen, ohne Änderungen zu speichern. Wenn Änderungen vorgenommen wurden, werden Sie gefragt, ob Sie ohne Speichern verlassen möchten.