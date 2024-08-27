# Python Virtual Environments (venv)

Eine detaillierte Anleitung, wie Sie eine virtuelle Python-Umgebung mit Python Virtual Environments (venv) auf Ihrem System einrichten.

## Erstellung einer virtuellen Umgebung

Um eine virtuelle Umgebung auf Ihrem System zu erstellen, führen Sie im Visual Studio Code Terminal Folgendes aus:

```shell
python3 -m venv venv
```

Dieser Schritt erstellt eine neue Verzeichnisstruktur für Ihre virtuelle Python-Umgebung. Beachten Sie, dass der zweite `venv` Parameter der Name Ihrer virtuellen Umgebung ist.

## Aktivierung der virtuellen Umgebung

Um das Virtual Environment zu aktivieren, führen Sie unter Linux oder macOS folgenden Befehl im Visual Studio Code Terminal aus:

```shell
source ./venv/bin/activate
```

### Virtuelle Umgebung unter Windows

Wenn Sie unter Windows arbeiten und die PowerShell verwenden, aktivieren Sie die Virtual Environment wie folgt im Visual Studio Code Terminal:

```shell
venv\Scripts\activate.ps1
```

Sollte es zu der Fehlermeldung `.\venv\Scripts\activate.ps1 cannot be loaded because running scripts is disabled on this system.` kommen, dann öffnen Sie ein PowerShell Terminal als **Administrator** und geben Folgendes ein:

```shell
Set-ExecutionPolicy RemoteSigned -Scope Process
```

Anschließend führen Sie den `activate`-Befehl nochmals im Visual Studio Code Terminal aus. Wenn alles korrekt installiert ist, sollte Ihre Terminal-Befehlszeile wie folgt aussehen:

```text
(venv) >
```

Dies zeigt an, dass die virtuelle Umgebung aktiviert wurde.
