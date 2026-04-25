$ErrorActionPreference = "Stop"
Set-Location "$PSScriptRoot"

if (!(Test-Path ".venv")) {
  py -m venv .venv
}

.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe init_db.py

$env:FLASK_SECRET_KEY = "local-test-key"
$env:PORT = "5000"
$env:FLASK_USE_RELOADER = "0"

$proc = Start-Process -FilePath ".\.venv\Scripts\python.exe" -ArgumentList "app.py" -PassThru
Start-Sleep -Seconds 3

try {
  Write-Host "[1/4] Health check"
  curl.exe -sS "http://127.0.0.1:5000/health"
  Write-Host "`n[2/4] Login page status"
  curl.exe -sS -o NUL -w "%{http_code}`n" "http://127.0.0.1:5000/login"
  Write-Host "[3/4] PDF endpoint sem login (esperado 302)"
  curl.exe -sS -o NUL -w "%{http_code}`n" "http://127.0.0.1:5000/receitas/exportar-pdf"
  Write-Host "[4/4] Pronto: abra http://127.0.0.1:5000"
}
finally {
  Stop-Process -Id $proc.Id -Force
}