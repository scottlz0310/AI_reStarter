Write-Host "コミット前チェックを実行中..." -ForegroundColor Green

# 仮想環境をアクティベート
if (Test-Path "venv\Scripts\Activate.ps1") {
    & ".\venv\Scripts\Activate.ps1"
    Write-Host "仮想環境をアクティベートしました" -ForegroundColor Cyan
} else {
    Write-Host "仮想環境が見つかりません" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "[1/4] ruff check実行中..." -ForegroundColor Yellow
& python -m ruff check src/ tests/
if ($LASTEXITCODE -ne 0) {
    Write-Host "ruffチェックに失敗しました" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "[2/4] ruff format実行中..." -ForegroundColor Yellow
& python -m ruff format .
if ($LASTEXITCODE -ne 0) {
    Write-Host "ruff formatに失敗しました" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "[3/4] black format実行中..." -ForegroundColor Yellow
& python -m black .
if ($LASTEXITCODE -ne 0) {
    Write-Host "blackフォーマットに失敗しました" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "[4/4] isort実行中..." -ForegroundColor Yellow
& python -m isort .
if ($LASTEXITCODE -ne 0) {
    Write-Host "isortに失敗しました" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "すべてのチェックが完了しました！" -ForegroundColor Green
Write-Host "変更をステージングしてコミットできます。" -ForegroundColor Green
