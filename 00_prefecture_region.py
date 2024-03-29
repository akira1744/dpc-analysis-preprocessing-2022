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
# 地方+都道府県
sql = """CREATE TABLE `prefecture` (
  `pref_id` INTEGER NOT NULL,
  'region_id' INTEGER NOT NULL,
  `pref` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`pref_id`)
);"""

# 実施
conn.execute("DROP TABLE IF EXISTS prefecture")
conn.execute(sql)
conn.commit()


# %%
sql = """INSERT INTO `prefecture` VALUES
  (1,1,'北海道'),
  (2,2,'青森県'),
  (3,2,'岩手県'),
  (4,2,'宮城県'),
  (5,2,'秋田県'),
  (6,2,'山形県'),
  (7,2,'福島県'),
  (8,3,'茨城県'),
  (9,3,'栃木県'),
  (10,3,'群馬県'),
  (11,3,'埼玉県'),
  (12,3,'千葉県'),
  (13,3,'東京都'),
  (14,3,'神奈川県'),
  (15,4,'新潟県'),
  (16,4,'富山県'),
  (17,4,'石川県'),
  (18,4,'福井県'),
  (19,4,'山梨県'),
  (20,4,'長野県'),
  (21,4,'岐阜県'),
  (22,4,'静岡県'),
  (23,4,'愛知県'),
  (24,5,'三重県'),
  (25,5,'滋賀県'),
  (26,5,'京都府'),
  (27,5,'大阪府'),
  (28,5,'兵庫県'),
  (29,5,'奈良県'),
  (30,5,'和歌山県'),
  (31,6,'鳥取県'),
  (32,6,'島根県'),
  (33,6,'岡山県'),
  (34,6,'広島県'),
  (35,6,'山口県'),
  (36,7,'徳島県'),
  (37,7,'香川県'),
  (38,7,'愛媛県'),
  (39,7,'高知県'),
  (40,8,'福岡県'),
  (41,8,'佐賀県'),
  (42,8,'長崎県'),
  (43,8,'熊本県'),
  (44,8,'大分県'),
  (45,8,'宮崎県'),
  (46,8,'鹿児島県'),
  (47,8,'沖縄県');
"""

conn.execute(sql)
conn.commit()

# %%
# 確認
pd.read_sql("SELECT * FROM prefecture", conn)

# %%
# 地方テーブル
sql = """CREATE TABLE `region` (
  `region_id`  INTEGER NOT NULL,
  `region` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`region_id`)
);"""

conn.execute("DROP TABLE IF EXISTS region")
conn.execute(sql)
conn.commit()

# %%

sql = """INSERT INTO `region` VALUES
  (1,'北海道地方'),
  (2,'東北地方'),
  (3,'関東地方'),
  (4,'中部地方'),
  (5,'近畿地方'),
  (6,'中国地方'),
  (7,'四国地方'),
  (8,'九州地方');
"""

conn.execute(sql)
conn.commit()

# %%
# 確認
pd.read_sql("SELECT * FROM region", conn)


# %%
