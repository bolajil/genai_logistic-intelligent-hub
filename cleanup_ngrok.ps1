# Clean up all ngrok files
Write-Host "Cleaning up ngrok files..." -ForegroundColor Cyan

Remove-Item -Path "ngrok.exe" -Force -ErrorAction SilentlyContinue
Remove-Item -Path "ngrok.zip" -Force -ErrorAction SilentlyContinue
Remove-Item -Path "download_ngrok.ps1" -Force -ErrorAction SilentlyContinue
Remove-Item -Path "copy_ngrok.ps1" -Force -ErrorAction SilentlyContinue
Remove-Item -Path "start_with_ngrok.ps1" -Force -ErrorAction SilentlyContinue

Write-Host "✅ All ngrok files cleaned up" -ForegroundColor Green
Write-Host ""
Write-Host "When you're ready to use ngrok:" -ForegroundColor Yellow
Write-Host "1. Download from: https://ngrok.com/download" -ForegroundColor White
Write-Host "2. Extract ngrok.exe to this folder" -ForegroundColor White
Write-Host "3. See SETUP_NGROK_AUTH.md for setup instructions" -ForegroundColor White
