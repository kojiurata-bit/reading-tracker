#!/bin/bash
# macOS: ダブルクリックでインストール
cd "$(dirname "$0")"
python3 install.py || { echo "python3 が見つかりません。https://www.python.org/downloads/ から Python 3 をインストールしてください"; }
echo
read -r -p "Enter キーで閉じます"
