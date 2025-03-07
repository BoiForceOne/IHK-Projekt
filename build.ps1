New-Item -ItemType Directory -Force -Path .\out
Set-Location .\out
Remove-Item .\dist -Recurse -Force
pyinstaller --onefile --icon ..\assets\logo.ico -w ..\main.py 
Move-Item .\dist\main.exe .\dist\Logistic.01.exe
Copy-Item -Path ..\assets -Recurse -Destination .\dist -Container
Set-Location ..