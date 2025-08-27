# 開発環境ルール

## 仮想環境の必須適用

### セッション開始時の必須作業
**すべてのコマンド実行前に必ず仮想環境をアクティベートする**

```bash
# Windows環境での仮想環境アクティベート
venv\Scripts\activate
```

### コマンド実行時のルール
- 単発コマンド実行時は前に `venv\Scripts\activate &&` を付ける
- 複数コマンドを実行する場合は最初に仮想環境をアクティベート

### 例
```bash
# 単発コマンド
venv\Scripts\activate && pytest

# 複数コマンド
venv\Scripts\activate
python --version
pip list
pytest tests/
```

### 確認方法
仮想環境が正しく適用されているかの確認：
```bash
where python
# 出力: C:\Github\AI_reStarter\venv\Scripts\python.exe が含まれること
```

## 開発ツール実行環境

### テスト実行
```bash
venv\Scripts\activate && pytest tests/ -v
```

### コード品質チェック
```bash
venv\Scripts\activate && black src/ tests/
venv\Scripts\activate && flake8 src/ tests/
venv\Scripts\activate && mypy src/
```

### パッケージ管理
```bash
venv\Scripts\activate && pip install -e ".[dev]"
venv\Scripts\activate && pip list
```

## 注意事項
- VS Code設定ファイルが完全に反映されるまで手動アクティベートが必要
- AmazonQターミナルでは特に仮想環境の手動適用を忘れずに実行
- 仮想環境未適用でのコマンド実行は禁止
