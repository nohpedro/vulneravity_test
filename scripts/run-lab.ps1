param([ValidateSet('reproduce','secure')][string]$Expectation = 'reproduce')
$ErrorActionPreference = 'Stop'
Set-Location (Split-Path -Parent $PSScriptRoot)
if (-not $env:JAVA_HOME) { throw 'Configure JAVA_HOME con un JDK 17 o posterior.' }
docker compose up -d
if ($LASTEXITCODE -ne 0) { throw 'No se pudo iniciar Docker Compose.' }
$ready = $false
for ($i=0; $i -lt 90; $i++) {
    try {
        $null = Invoke-RestMethod -Uri 'http://127.0.0.1:8090/JSON/core/view/version/' -Headers @{Host='zap'} -TimeoutSec 2
        $null = Invoke-WebRequest -Uri 'http://127.0.0.1:3000/' -TimeoutSec 2
        $ready = $true; break
    } catch { Start-Sleep -Seconds 1 }
}
if (-not $ready) { throw 'Juice Shop o ZAP no están listos.' }
New-Item -ItemType Directory -Force evidence | Out-Null
# Reset only this laboratory ZAP session to avoid mixing prior executions.
$null = Invoke-RestMethod -Uri 'http://127.0.0.1:8090/JSON/core/action/newSession/?overwrite=true' -Headers @{Host='zap'}
& ./mvnw.cmd clean test "-Dexpectation=$Expectation" 2>&1 | Tee-Object evidence/execution.log
$testExit = $LASTEXITCODE
if (Test-Path target/business-result.json) { Copy-Item target/business-result.json evidence/business-result.json }
python scripts/export_zap.py
if ($LASTEXITCODE -ne 0) { throw 'No se pudo exportar ZAP.' }
if ($testExit -ne 0) { throw "La prueba terminó con código $testExit. Consulte evidence/execution.log." }
Write-Host 'Ejecución completada. Genere Allure con: allure generate target/allure-results --clean -o output/allure-report'
