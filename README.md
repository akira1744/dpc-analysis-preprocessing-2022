# DPC導入の影響評価に係る調査「退院患者調査」の可視化WEBアプリの前処理

## DPC導入の影響評価に係る調査「退院患者調査」の可視化WEBアプリ

https://dpc-analysis-2022.streamlit.app/

https://github.com/akira1744/dpc-analysis-2022

## DataSource

[令和4年度DPC導入の影響評価に係る調査「退院患者調査」の結果報告について](https://www.mhlw.go.jp/stf/shingi2/newpage_39119.html)

[診断群分類（DPC) 電子点数表（令和3年11月24日更新）](https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/0000198757_00003.html)

## 前処理の環境

- env.sh
- poetry.toml
- poetry.lock
- pyproject.toml

## 前処理スクリプト

- 00_prefecture_region.py
- 01_preprocessing.py
- 02_import_data_to_db.py
- 03_read_test.py

## 本番環境テスト用のファイル

- main.py
- package/myfunc.py
- data.db
- requirements.txt
