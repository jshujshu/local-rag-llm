# activate venv
Write-Host "Activating Python environment..." -ForegroundColor Cyan
. .\.venv\Scripts\Activate.ps1

# Security: prevent HuggingFace from pulling updated model weights at runtime
$env:HF_HUB_OFFLINE = "1"

# Security: bind to loopback by default.
# Set $env:BIND_HOST = "0.0.0.0" before running to expose on LAN.
if (-not $env:BIND_HOST) { $env:BIND_HOST = "127.0.0.1" }

# start qdrant
Write-Host "Starting Qdrant..." -ForegroundColor Cyan
docker start qdrant-server 2>$null

if ($LASTEXITCODE -ne 0) {
    Write-Host "Qdrant not running. Creating new container..." -ForegroundColor Yellow

    docker run -d --name qdrant-server `
        -p 6333:6333 -p 6334:6334 `
        -v ${PWD}\qdrant_storage:/qdrant/storage `
        qdrant/qdrant
}

# run health check
Write-Host "Checking Qdrant..." -ForegroundColor Cyan
try {
    Invoke-RestMethod http://localhost:6333/collections | Out-Null
    Write-Host "Qdrant is ready." -ForegroundColor Green
} catch {
    Write-Host "Qdrant not ready yet (it may still be starting)." -ForegroundColor Yellow
}

# start fastapi
Write-Host "Starting FastAPI RAG server (host=$($env:BIND_HOST))..." -ForegroundColor Cyan

if ($env:DEV_MODE -eq "1") {
    uvicorn api:app --host $env:BIND_HOST --port 8000 --reload
} else {
    uvicorn api:app --host $env:BIND_HOST --port 8000
}

