# QuickCode v2 (Flask QR Generator)

- 実際に QR を生成（PNG）
- 「QRコード」ボタンで DB に保存し、`/r/<id>` リンクへ誘導する QR を作成
- パスワードを設定すると `/r/<id>` アクセス時にパスワード入力を要求
- 「プレビュー」ボタンは保存せず URL をそのままエンコードして表示
- フォルダ/名称のメタデータも保存（一覧 `/list` で確認）

## Run
```
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
# http://localhost:5000
```
