# %%
import pandas as pd
import numpy as np
import streamlit as st
import altair as alt
from altair import limit_rows, to_values
import toolz
from altair import datum
import sqlite3


# %%
conn = sqlite3.connect("data.db")

# %%
# 地域リスト
region_list = pd.read_sql("SELECT region FROM region", conn)["region"]
region_list

# %%
# 都道府県リスト
pref_list = pd.read_sql("SELECT pref FROM prefecture", conn)["pref"]
pref_list
# %%
# 病院一覧
sql = """
SELECT
    hpcd
    ,hpname
    ,region
    ,pref
    ,med2
    ,city
    ,bed
FROM hp
LEFT JOIN prefecture ON hp.pref_id = prefecture.pref_id
LEFT JOIN region ON prefecture.region_id = region.region_id;
"""
hp = pd.read_sql(sql, conn)
hp

# %%

select_hp = hp[hp["region"] == "東北地方"]
select_hpcd = select_hp["hpcd"]

# %%
# mdc2dの取得
sql = f"""
SELECT
    hpname
    ,mdcname
    ,value
FROM mdc2d
INNER JOIN hp 
    ON mdc2d.hpcd = hp.hpcd
    AND hp.hpcd in {tuple(select_hpcd)}
LEFT JOIN mdc2_mst ON mdc2d.mdc2 = mdc2_mst.mdc2
"""

mdc2d = pd.read_sql(sql, conn)
mdc2d
# %%
# mdc6dの取得
sql = f"""
SELECT
    hpname
    ,mdcname
    ,mdc6name
    ,value
FROM mdc6d
INNER JOIN hp 
    ON mdc6d.hpcd = hp.hpcd
    AND hp.hpcd in {tuple(select_hpcd)}
LEFT JOIN mdc26_mst ON mdc6d.mdc6 = mdc26_mst.mdc6
LEFT JOIN mdc2_mst ON mdc26_mst.mdc2 = mdc2_mst.mdc2
;
"""
mdc6d = pd.read_sql(sql, conn)
mdc6d

# %%
ope_mst = pd.read_sql("SELECT * FROM ope_mst", conn)
ope_mst
# %%
mdc2_mst = pd.read_sql("SELECT * FROM mdc2_mst", conn)
mdc2_mst
# %%
mdc26_mst = pd.read_sql("SELECT * FROM mdc26_mst", conn)
mdc26_mst
# %%
oped = pd.read_sql("SELECT * FROM oped", conn)
oped
# %%
# opedの取得
sql = f"""
WITH mdc_mst as  (
    SELECT
        mdc2_mst.mdc2
        ,mdc2_mst.mdcname
        ,mdc26_mst.mdc6
        ,mdc26_mst.mdc6name
    FROM mdc2_mst
    LEFT JOIN mdc26_mst ON mdc2_mst.mdc2 = mdc26_mst.mdc2
)
SELECT
    oped.hpcd
    ,hp.hpname
    ,mdc_mst.mdcname
    ,oped.mdc6
    ,mdc_mst.mdc6name
    ,oped.ope
    ,ope_mst.opename
    ,oped.value
    ,hp.bed
FROM oped
INNER JOIN hp 
    ON oped.hpcd = hp.hpcd
    AND hp.hpcd in {tuple(select_hpcd)}
LEFT JOIN ope_mst ON oped.mdc6 = ope_mst.mdc6 and oped.ope = ope_mst.ope
LEFT JOIN mdc_mst ON oped.mdc6 = mdc_mst.mdc6;
"""
oped = pd.read_sql(sql, conn)
oped["hp"] = " "
oped
# %%
oped
# %%
