# Prüfen, ob Port 8000 belegt ist
$port = 8000
$process = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue | Select-Object -First 1

if ($process) {
    Write-Host "Port $port wird von Prozess ID $($process.OwningProcess) belegt. Beende Prozess..." -ForegroundColor Yellow
    Stop-Process -Id $process.OwningProcess -Force
    Start-Sleep -Seconds 1
}

Write-Host "Starte Meal-Plan App..." -ForegroundColor Green
uvicorn main:app --reload --port $port
