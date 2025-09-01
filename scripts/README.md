# Scripts Directory

このディレクトリには、ビルドとリリースプロセスで使用されるスクリプトが含まれています。

## ファイル一覧

### Python スクリプト

- **`build_release.py`** - 完全なリリースビルドプロセスを自動化
- **`create_release_package.py`** - リリースパッケージとZIPファイルの作成
- **`test_executable.py`** - 実行ファイルとリリースパッケージのテスト

### バッチファイル

- **`build.bat`** - Windows用ビルドスクリプト
- **`test.bat`** - Windows用テストスクリプト

### PowerShell スクリプト

- **`pre-commit-check.ps1`** - コミット前のコード品質チェック
- **`release.ps1`** - リリースプロセス用スクリプト

## 使用方法

### ローカルビルド
```bash
python scripts/build_release.py
```

### リリースパッケージ作成
```bash
python scripts/create_release_package.py
```

### 実行ファイルテスト
```bash
python scripts/test_executable.py
```

## GitHub Actions での使用

これらのスクリプトは `.github/workflows/release.yml` で自動的に実行されます。
