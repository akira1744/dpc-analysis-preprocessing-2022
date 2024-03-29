# %%
import pandas as pd
import numpy as np
import streamlit as st
import altair as alt
from altair import limit_rows, to_values
import toolz
from altair import datum
import sqlite3
import os

# %%
year = "2022"

# %%
output_dir = "output/" + year
os.makedirs(output_dir, exist_ok=True)

# %%
# sqlite3でdata.dbを作成
conn = sqlite3.connect("data.db")

# %%
prefecture = pd.read_sql("SELECT * FROM prefecture", conn)
prefecture

# %%
region = pd.read_sql("SELECT * FROM region", conn)
region

# %%
hp = pd.read_csv(
    os.path.join(output_dir, "hp_mst.csv"),
    dtype={
        "hpcd": int,
        "hpname": "category",
        "pref": "category",
        "med2": "category",
        "city": object,
        "bed": int,
        "month": int,
    },
)

hp

# %%
# hpにprefectureをleft_join
hp = hp.merge(prefecture, left_on="pref", right_on="pref", how="left")

# hpに欠損があるかどうかを確認
hp.isnull().sum()

# hpのpref_idとprefの集計表
hp.groupby(["pref_id", "pref"]).size().reset_index(name="count")

# %%
# 列の並び替え
hp = hp.loc[
    :, ["hpcd", "hpname", "region_id", "pref_id", "med2", "city", "bed", "month"]
]
hp

# %%
# hpテーブルを作成
hp.to_sql("hp", conn, if_exists="replace", index=False)

# %%
# hpテーブルの読み込みテスト
test = pd.read_sql("SELECT * FROM hp", conn)
test

# %%
mdc2_mst = pd.read_csv(
    os.path.join(output_dir, "mdc2_mst.csv"),
    encoding="cp932",
    dtype={"mdc2": int, "mdcname": "category"},
)
mdc2_mst

# %%
# mdc2_mstテーブルを作成
mdc2_mst.to_sql("mdc2_mst", conn, if_exists="replace", index=False)

# %%
# sqlでmdc2テーブルのmdc2列にインデックスを作成
conn.execute("CREATE INDEX idx_mdc2 ON mdc2_mst (mdc2)")

# %%
mdc26_mst = pd.read_csv(
    os.path.join(output_dir, "mdc26_mst.csv"),
    encoding="cp932",
    dtype={"mdc2": int, "mdc6": "category", "mdc6name": "category"},
)
mdc26_mst

# %%
# mdc2_mstテーブルを作成
mdc26_mst.to_sql("mdc26_mst", conn, if_exists="replace", index=False)

# %%
# sqlでmdc26テーブルのmdc2,mdc6の列にインデックスを作成
conn.execute("CREATE INDEX idx_mdc26_mst ON mdc26_mst (mdc2,mdc6)")

# %%
ope_mst = pd.read_csv(
    os.path.join(output_dir, "mdc6ope_mst.csv"),
    encoding="cp932",
    dtype={"mdc6": "category", "ope": int, "opename": "category"},
)
ope_mst

# %%
# ope_mstのopeが0のデータを抽出
ope_mst[ope_mst["ope"] == 0]

# %%
# ope_mstテーブルを作成
ope_mst.to_sql("ope_mst", conn, if_exists="replace", index=False)

# %%
# sqlでope_mstテーブルのmdc6の列にインデックスを作成
conn.execute("CREATE INDEX idx_ope_mst ON ope_mst (mdc6)")

# %%
mdc2d = pd.read_csv(
    os.path.join(output_dir, "mdc2_data.csv"),
    encoding="cp932",
    dtype={"hpcd": int, "md2": int, "value": int},
)
mdc2d

# %%
# hpのmonth列を結合
mdc2d = mdc2d.merge(hp[["hpcd", "month"]], left_on="hpcd", right_on="hpcd", how="left")
# 各行でvalueをmonthでわる
mdc2d["value"] = mdc2d["value"] / mdc2d["month"]
# valueを四捨五入して小数点第1位までにする
mdc2d["value"] = mdc2d["value"].round(1)
# month列をdrop
mdc2d = mdc2d.drop(columns="month")
mdc2d

# %%
# mdc2dテーブルを作成
mdc2d.to_sql("mdc2d", conn, if_exists="replace", index=False)

# %%
# hpcdとmdc2にインデックスを作成
conn.execute("CREATE INDEX idx_mdc2d ON mdc2d (hpcd,mdc2)")

# %%
mdc6d = pd.read_csv(
    os.path.join(output_dir, "mdc6_data.csv"),
    encoding="cp932",
    dtype={"hpcd": int, "mdc6": "category", "value": int},
)
mdc6d

# %%
# hpのmonth列を結合
mdc6d = mdc6d.merge(hp[["hpcd", "month"]], left_on="hpcd", right_on="hpcd", how="left")
# 各行でvalueをmonthでわる
mdc6d["value"] = mdc6d["value"] / mdc6d["month"]
# valueを四捨五入して小数点第1位までにする
mdc6d["value"] = mdc6d["value"].round(1)
# month列をdrop
mdc6d = mdc6d.drop(columns="month")
mdc6d

# %%
# mdc6dテーブルを作成
mdc6d.to_sql("mdc6d", conn, if_exists="replace", index=False)

# %%
# hpcdとmdc6にインデックスを作成
conn.execute("CREATE INDEX idx_mdc6d ON mdc6d (hpcd,mdc6)")

# %%
oped = pd.read_csv(
    os.path.join(output_dir, "ope_data.csv"),
    encoding="cp932",
    dtype={"hpcd": int, "mdc6": "category", "ope": int, "value": int},
)
oped

# %%
# hpのmonth列を結合
oped = oped.merge(hp[["hpcd", "month"]], left_on="hpcd", right_on="hpcd", how="left")
# 各行でvalueをmonthでわる
oped["value"] = oped["value"] / oped["month"]
# valueを四捨五入して小数点第1位までにする
oped["value"] = oped["value"].round(1)
# month列をdrop
oped = oped.drop(columns="month")
oped


# %%
# opedテーブルを作成
oped.to_sql("oped", conn, if_exists="replace", index=False)

# %%
# hpcdとmdc6にインデックスを作成
conn.execute("CREATE INDEX idx_oped ON oped (hpcd,mdc6,ope)")

conn.commit()
conn.close()

# %%
