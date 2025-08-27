# AI reStarter リリースガイド

## リリースプロセス

### 1. 自動リリース（推奨）

PowerShellスクリプトを使用した自動リリース：

```powershell
# リリースバージョンを指定して実行
.\scripts\release.ps1 -Version "1.0.1"
```

このスクリプトは以下を自動実行します：
- テストの実行
- バージョン番号の更新
- RELEASE_NOTESの更新
- Gitタグの作成
- リモートへのプッシュ

### 2. 手動リリース

#### ステップ1: 準備
```bash
# 仮想環境をアクティベート
venv\Scripts\activate

# テストを実行
pytest tests/ --cov=src --cov-report=term-missing
```

#### ステップ2: バージョン更新
`pyproject.toml`のバージョンを更新：
```toml
version = "1.0.1"
```

#### ステップ3: リリースノート更新
`RELEASE_NOTES.md`に新バージョンの情報を追加

#### ステップ4: Gitタグ作成
```bash
git add .
git commit -m "Release v1.0.1"
git tag v1.0.1
git push origin main
git push origin v1.0.1
```

### 3. GitHub Actionsによる自動ビルド

タグがプッシュされると自動で以下が実行されます：
- テストの実行
- Windows実行ファイルのビルド
- リリースパッケージの作成
- GitHubリリースの作成

## ローカルビルド

開発中のテスト用ビルド：

```bash
# バッチスクリプトを使用
.\scripts\build.bat

# または手動で
venv\Scripts\activate
pyinstaller pyinstaller.spec
```

## リリース成果物

各リリースには以下が含まれます：

### ZIPパッケージ内容
- `AI_reStarter.exe` - メイン実行ファイル
- `README.md` - 使用方法
- `kiro_config.json` - デフォルト設定
- `error_templates/` - エラーテンプレート
- `amazonq_templates/` - AmazonQテンプレート

### GitHubリリース
- リリースノート（日本語）
- ダウンロードリンク
- インストール手順

## バージョニング

セマンティックバージョニングを使用：
- `MAJOR.MINOR.PATCH` (例: 1.0.1)
- `MAJOR`: 破壊的変更
- `MINOR`: 新機能追加
- `PATCH`: バグ修正

## リリース前チェックリスト

- [ ] 全テストが通過
- [ ] ドキュメントが更新済み
- [ ] RELEASE_NOTESが記載済み
- [ ] 設定ファイルが適切
- [ ] テンプレートファイルが含まれている

## トラブルシューティング

### ビルドエラー
- 依存関係の確認: `pip list`
- 仮想環境の確認: `where python`
- PyInstallerの再インストール: `pip install --force-reinstall pyinstaller`

### GitHub Actions失敗
- ログを確認してエラー原因を特定
- 必要に応じてワークフローを修正
- 再度タグをプッシュ

### 実行ファイルの問題
- テンプレートファイルが含まれているか確認
- 設定ファイルが正しく配置されているか確認
- Windows Defenderの除外設定を確認
