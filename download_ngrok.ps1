$ngrokUrl = "https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-windows-amd64.zip"
$downloadPath = Join-Path $PSScriptRoot "ngrok.zip"

Write-Host "Downloading ngrok..."
Invoke-WebRequest -Uri $ngrokUrl -OutFile $downloadPath -UseBasicParsing

Write-Host "Extracting ngrok.exe..."
Expand-Archive -LiteralPath $downloadPath -DestinationPath $PSScriptRoot -Force
Remove-Item $downloadPath
Write-Host "ngrok.exe is ready in $PSScriptRoot"
Write-Host "Then run .\run_with_ngrok.ps1"