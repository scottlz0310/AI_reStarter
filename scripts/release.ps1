# AI reStarter リリーススクリプト

param(
    [Parameter(Mandatory=$true)]
    [string]$Version
)

Write-Host "AI reStarter v$Version リリースを開始します..." -ForegroundColor Green

# バージョン形式チェック
if ($Version -notmatch '^v?\d+\.\d+\.\d+$') {
    Write-Error "バージョン形式が正しくありません (例: 1.0.0 または v1.0.0)"
    exit 1
}

# vプレフィックスを追加
if (-not $Version.StartsWith('v')) {
    $Version = "v$Version"
}

try {
    # 仮想環境をアクティベート
    & "venv\Scripts\Activate.ps1"

    # テストを実行
    Write-Host "テストを実行中..." -ForegroundColor Yellow
    pytest tests/ --cov=src --cov-report=term-missing
    if ($LASTEXITCODE -ne 0) {
        throw "テストが失敗しました"
    }

    # バージョンを更新
    Write-Host "バージョンを更新中..." -ForegroundColor Yellow
    $pyprojectContent = Get-Content pyproject.toml -Raw
    $pyprojectContent = $pyprojectContent -replace 'version = ".*"', "version = `"$($Version.TrimStart('v'))`""
    Set-Content pyproject.toml $pyprojectContent

    # RELEASE_NOTESを更新
    $releaseDate = Get-Date -Format "yyyy-MM-dd"
    $newEntry = @"
## バージョン $Version ($releaseDate)

### 新機能
- [ここに新機能を記載]

### 改善
- [ここに改善点を記載]

### バグ修正
- [ここにバグ修正を記載]

"@

    $releaseNotesContent = Get-Content RELEASE_NOTES.md -Raw
    $releaseNotesContent = $releaseNotesContent -replace '(# AI reStarter - リリースノート\r?\n)', "`$1`n$newEntry"
    Set-Content RELEASE_NOTES.md $releaseNotesContent

    # Gitタグを作成
    Write-Host "Gitタグを作成中..." -ForegroundColor Yellow
    git add .
    git commit -m "Release $Version"
    git tag $Version

    # リモートにプッシュ
    Write-Host "リモートにプッシュ中..." -ForegroundColor Yellow
    git push origin main
    git push origin $Version

    Write-Host "リリース $Version が正常に作成されました!" -ForegroundColor Green
    Write-Host "GitHub Actionsでビルドとリリースが自動実行されます。" -ForegroundColor Cyan

} catch {
    Write-Error "リリース処理中にエラーが発生しました: $_"
    exit 1
}
