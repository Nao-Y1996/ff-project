FROM python:3.10

# コンテナ内の作業ディレクトリを設定
WORKDIR /app

# 必要なライブラリをインストール
COPY requirements.txt .
# todo 環境構築時に自動でmigrate
RUN pip install --no-cache-dir -r requirements.txt
