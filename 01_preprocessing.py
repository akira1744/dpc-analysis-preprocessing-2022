# %%
import os
from glob import glob
import pandas as pd
import numpy as np
import streamlit as st
from package import myfunc
import altair as alt


# %%
# global setting
# TODO 年度が変わったら書き換え
year = "2022"

# %%
# フォルダ指定(なければ作成)
input_dir = "input/" + year
os.makedirs(input_dir, exist_ok=True)
output_dir = "output/" + year
os.makedirs(output_dir, exist_ok=True)


# %%
def to_unique(df, maincol, subcol):
    before = df[maincol].nunique()
    rename = df[maincol] + "_" + df[subcol]
    after = rename.nunique()
    print(f"列数:{len(df[maincol])}")
    print(f"{maincol}ユニーク数:{before}")
    print(f"{maincol,subcol}ユニーク数:{after}")
    if before == after:
        print("{maincol}を変換しませんでした")
    else:
        df["tmp_for_count"] = 1
        df2 = df.groupby(maincol, as_index=False).count()[[maincol, "tmp_for_count"]]
        df2 = df2.rename(columns={"tmp_for_count": maincol + "_count"})
        df3 = df.groupby([maincol, subcol], as_index=False).count()[
            [maincol, subcol, "tmp_for_count"]
        ]
        df3 = df3.rename(columns={"tmp_for_count": maincol + subcol + "_count"})
        df4 = df3.merge(df2, on=maincol, how="left")
        df4["mask_flag"] = df4.iloc[:, 2] != df4.iloc[:, 3]
        df4["new_" + maincol] = df4[maincol] + "_" + df4[subcol]
        df = df.merge(
            df4[[maincol, subcol, "new_" + maincol, "mask_flag"]],
            on=[maincol, subcol],
            how="left",
        )
        df[maincol] = df[maincol].mask(df["mask_flag"], df["new_" + maincol])
        df = df.drop(columns=["new_" + maincol, "mask_flag", "tmp_for_count"])
        print(f"{maincol}の重複を{subcol}で固有化しました")
        return df


# %%
# 1. 都道府県,2次医療圏,市町村のマスタを作成
def make_location_mst():
    # 都道府県ー二次医療圏ー市町村ー病院のマスタデータを作成する
    location_mst = pd.read_csv(
        os.path.join(input_dir, "総務省県二次医療圏市町村.csv"),
        encoding="cp932",
        usecols=[0],
        skiprows=[0, 1, 2, 3, 4, 5, 6, 7, 8],
        header=None,
        dtype=object,
    )
    # 先頭数字の桁数でカラムを分ける
    location_mst["pref"] = location_mst.apply(
        lambda x: np.nan if x[0][2].isdecimal() else x[0], axis=1
    )
    location_mst["med2"] = location_mst.apply(
        lambda x: (
            x[0] if ((x[0][2].isdecimal()) and not (x[0][4].isdecimal())) else np.nan
        ),
        axis=1,
    )
    location_mst["city"] = location_mst.apply(
        lambda x: x[0] if x[0][4].isdecimal() else np.nan, axis=1
    )
    # 上の値でnaを埋める
    location_mst[["pref", "med2"]] = location_mst[["pref", "med2"]].fillna(
        method="ffill"
    )
    # 空白削除
    cols = ["pref", "med2", "city"]
    for col in cols:
        location_mst["{}".format(col)] = location_mst["{}".format(col)].str.replace(
            "　", ""
        )
        location_mst["{}".format(col)] = location_mst["{}".format(col)].str.replace(
            " ", ""
        )
    # cityがnaの行を削除
    location_mst = location_mst.loc[~location_mst["city"].isna()]
    # コードと名称を分離
    location_mst["prefcd"] = location_mst["pref"].str[:2]
    location_mst["pref"] = location_mst["pref"].str[2:]
    location_mst["med2cd"] = location_mst["med2"].str[:4]
    location_mst["med2"] = location_mst["med2"].str[4:]
    location_mst["citycd"] = location_mst["city"].str[:5]
    location_mst["city"] = location_mst["city"].str[5:]
    # 必要列抽出
    location_mst = location_mst[["prefcd", "pref", "med2cd", "med2", "citycd", "city"]]
    # 二次医療圏名、市町村名の重複を補完
    location_mst = to_unique(location_mst, "city", "pref")
    location_mst = to_unique(location_mst, "city", "med2")
    location_mst = to_unique(location_mst, "med2", "pref")
    return location_mst


# %%
location_mst = make_location_mst()


# %%
# 2.医療機関マスタの作成
def make_hp_mst():
    # 施設概要表をインポート　告示番号から市町村番号を結合　市町村番号から　２次医療圏名、件名を結合
    df = pd.read_excel(os.path.join(input_dir, "施設概要表.xlsx"), dtype=object)
    # カラム名の修正
    df.columns = [
        "告示番号",
        "通番",
        "市町村番号",
        "都道府県",
        "施設名",
        "病院類型",
        "DPC算定病床数",
        "DPC算定病床の入院基本料",
        "DPC算定病床割合",
        "回復期リハビリテーション病棟入院料病床数",
        "地域包括ケア病棟入院料病床数",
        "精神病床数",
        "療養病床数",
        "結核病床数",
        "病床総数",
        "提出月数",
    ]
    # 告示番号がnaの行を削除
    df = df[~df["告示番号"].isna()]
    # 告示番号が数字でない行を削除
    df = df.loc[df["告示番号"].str.isdecimal()]
    # 必要列のみ抽出
    df = df[
        [
            "市町村番号",
            "告示番号",
            "施設名",
            "DPC算定病床数",
            "病床総数",
            "DPC算定病床の入院基本料",
            "提出月数",
        ]
    ]
    return df


# %%
# 医療機関マスタの作成。この段階では施設名はuniqueになっていなくてもOK
hp_mst = make_hp_mst()
hp_mst.describe()


# %%
# 3.市町村番号をkeyにして、hp_mstに県,二次医療圏を結合
def merge_hp_mst_location_mst(hp_mst, location_mst):
    hp = hp_mst.merge(location_mst, left_on="市町村番号", right_on="citycd", how="left")
    hp = hp[
        [
            "prefcd",
            "pref",
            "med2cd",
            "med2",
            "citycd",
            "city",
            "告示番号",
            "施設名",
            "病床総数",
            "提出月数",
        ]
    ]
    print(f"hp_mst列数{len(hp_mst)}")
    print(f"hp列数{len(hp)}")
    hp = hp.rename(
        columns={
            "告示番号": "hpcd",
            "施設名": "hpname",
            "病床総数": "bed",
            "提出月数": "month",
        }
    )
    hp = to_unique(hp, "hpname", "pref")  # 病院名を固有化
    hp = hp.sort_values(
        [
            "prefcd",
            "med2cd",
            "citycd",
            "hpcd",
        ]
    ).reset_index(drop=True)
    return hp


# %%
# 病院名を固有化
hp = merge_hp_mst_location_mst(hp_mst, location_mst)
hp.describe()

# %%
# 追加 hpcdが重複しているデータを調べる
hp[hp.duplicated(subset="hpcd", keep=False)]

# %%
# hpnameが兵庫県立はりま姫路総合医療センターのhpcdを31037002に変更
hp["hpcd"] = hp["hpcd"].mask(
    hp["hpname"] == "兵庫県立はりま姫路総合医療センター", "31037002"
)
# 医療法人錦秀会阪和記念病院を30912002に変更
hp["hpcd"] = hp["hpcd"].mask(hp["hpname"] == "医療法人錦秀会阪和記念病院", "30912002")
# 川西市立総合医療センターを31028002に変更
hp["hpcd"] = hp["hpcd"].mask(hp["hpname"] == "川西市立総合医療センター", "31028002")


# %%
# 4.dpcのマスタを作成
def make_mdc2_mst():
    # DPC点数早見表からmdc2マスタの作成
    mdc2 = pd.read_excel(
        os.path.join(input_dir, "診断群分類（DPC) 電子点数表.xlsx"),
        sheet_name="１）ＭＤＣ名称",
        skiprows=[1],
        dtype=object,
        usecols=[0, 1],
    )
    mdc2["MDCname"] = mdc2["MDCｺｰﾄﾞ"] + " " + mdc2["MDC名称"]
    mdc2 = mdc2[["MDCｺｰﾄﾞ", "MDCname"]]
    mdc2.columns = ["mdc2", "mdcname"]
    return mdc2


# %%
def make_mdc6_mst():
    # DPC点数早見表からmdc6マスタの作成
    mdc6 = pd.read_excel(
        os.path.join(input_dir, "診断群分類（DPC) 電子点数表.xlsx"),
        sheet_name="２）分類名称",
        skiprows=[1],
        dtype=object,
        usecols=[0, 1, 2],
    )
    mdc6["mdc6"] = mdc6["MDCｺｰﾄﾞ"] + mdc6["分類ｺｰﾄﾞ"]
    mdc6["mdc6name"] = mdc6["mdc6"] + " " + mdc6["名称"]
    mdc6["mdc2"] = mdc6["mdc6"].str[:2]
    mdc6 = mdc6[["mdc2", "mdc6", "mdc6name"]]
    return mdc6


# %%
def make_dpc_opekubun_mst():
    # DPC点数早見表からDPCの手術マスタを作成
    dpc_opkubun_mst = pd.read_excel(
        os.path.join(input_dir, "診断群分類（DPC) 電子点数表.xlsx"),
        sheet_name="11）診断群分類点数表",
        skiprows=[0, 1, 3],
        dtype=object,
    )
    dpc_opkubun_mst["mdc6"] = dpc_opkubun_mst["診断群分類番号"].str[0:6]
    dpc_opkubun_mst["ope"] = dpc_opkubun_mst["診断群分類番号"].str[8:10]
    dpc_opkubun_mst = dpc_opkubun_mst[["mdc6", "ope", "手術名"]]
    dpc_opkubun_mst.columns = ["mdc6", "ope", "opename"]
    # 14桁のマスタから10桁までのマスタを作成しているので重複削除が必要
    dpc_opkubun_mst.drop_duplicates(inplace=True)
    return dpc_opkubun_mst


# %%
def make_dpc_kcode_mst():
    # DPC点数早見表から mdc6 ope毎の手術名一覧のデータ
    dpc_kcode = pd.read_excel(
        os.path.join(input_dir, "診断群分類（DPC) 電子点数表.xlsx"),
        sheet_name="６）手術 ",
        dtype=object,
        header=None,
    )
    # ヘッダー処理（2行結合されている)
    tmp = dpc_kcode.iloc[:2]  # 上から2行だけを抽出
    tmp = tmp.T  # 転置
    tmp = tmp.fillna(method="ffill")  # 上のデータで値を置き換え
    tmp["columns"] = tmp[0] + "_" + tmp[1]
    tmp["columns"].iloc[:6] = tmp[0].iloc[:6]
    columns = tmp["columns"]
    dpc_kcode.columns = columns
    dpc_kcode = dpc_kcode.iloc[2:]
    # 必要列抽出
    dpc_kcode["mdc6"] = dpc_kcode["MDCｺｰﾄﾞ"] + dpc_kcode["分類ｺｰﾄﾞ"]
    dpc_kcode = dpc_kcode[["mdc6", "対応ｺｰﾄﾞ", "手術１_Ｋコード", "手術１_点数表名称"]]
    dpc_kcode.columns = ["mdc6", "ope", "k", "kname"]
    dpc_kcode = dpc_kcode.sort_values(
        ["mdc6", "ope", "k"], ascending=[True, False, True]
    ).reset_index(drop=True)
    # コードと名称を結合
    dpc_kcode["k_kname"] = dpc_kcode["k"] + " " + dpc_kcode["kname"]
    return dpc_kcode


# %%
def merge_dpc_mst(dpc_kcode_mst, dpc_opkubun_mst):
    print(len(dpc_kcode_mst))
    dpc_mst = dpc_kcode_mst.merge(dpc_opkubun_mst, on=["mdc6", "ope"], how="left")
    dpc_mst["opename"] = dpc_mst.apply(
        lambda x: "手術なし" if x["ope"] == "99" else x["opename"], axis=1
    )
    dpc_mst["opename"] = dpc_mst.apply(
        lambda x: "その他手術" if x["ope"] == "97" else x["opename"], axis=1
    )
    dpc_mst["opename"] = dpc_mst["ope"] + " " + dpc_mst["opename"]
    print(len(dpc_mst))
    dpc_mst = dpc_mst.merge(mdc6_mst, on="mdc6", how="left")
    print(len(dpc_mst))
    dpc_mst = dpc_mst.merge(mdc2_mst, on="mdc2", how="left")
    print(len(dpc_mst))
    dpc_mst = dpc_mst[
        ["mdc2", "mdcname", "mdc6", "mdc6name", "ope", "opename", "k_kname"]
    ]
    dpc_mst.columns = ["mdc2", "mdcname", "mdc6", "mdc6name", "ope", "opename", "kcode"]
    return dpc_mst


# %%
mdc2_mst = make_mdc2_mst()
mdc2_mst.describe()
# %%
mdc6_mst = make_mdc6_mst()
mdc6_mst.describe()
# %%
dpc_opkubun_mst = make_dpc_opekubun_mst()
dpc_opkubun_mst.describe()
# %%
dpc_kcode_mst = make_dpc_kcode_mst()
dpc_kcode_mst.describe(include=object)
# %%
dpc_kcode_mst.head(1)
# %%
dpc_mst = merge_dpc_mst(dpc_kcode_mst, dpc_opkubun_mst)
dpc_mst.describe(include="all")


# %%
# 5.mdc6別実績の集計
def mdc6_oep_hp_load(mode="件数"):
    # ②[mdc6別手術別医療機関別]の集計
    # MDC2別で1つずつのエクセルになっている為、前処理してから結合
    # 前処理　横持→縦持
    cols = ["告示番号", "通番", "施設名", "mdc6", "mdc6name", "ope", "value"]
    data = pd.DataFrame(index=[], columns=cols)  # 空のdfを作成
    files = glob(
        os.path.join(input_dir, "疾患別手術別集計/*.xlsx")
    )  # ファイルリストの取得
    for file in files:
        print(file)
        # ヘッダー行がセル結合され3層構造になってるので、縦持ちデータに変える為に前処理
        # カラム名を作成し設定(抽出、縦に置換、穴埋め、３列の名前を結合、ABC列も別途処理し)
        df = pd.read_excel(file, header=None)
        ddf = df.iloc[:4]  # 上から３行だけを抽出
        ddf = ddf.T  # 転置
        ddf = ddf.fillna(method="ffill")  # 上のデータで値を置き換え
        ddf["columns"] = ddf[0] + "_" + ddf[1] + "_" + ddf[2] + "_" + ddf[3]
        ddf["columns"].iloc[:3] = ddf[3].iloc[:3]
        # ABC列（告示番号、通し番号、施設名)も同じ列にまとめる。
        columns = ddf["columns"]
        df.columns = columns

        # 合併病院の個別処理
        df["告示番号"] = df["告示番号"].mask(
            df["施設名"] == "兵庫県立はりま姫路総合医療センター", "31037002"
        )
        df["告示番号"] = df["告示番号"].mask(
            df["施設名"] == "医療法人錦秀会阪和記念病院", "30912002"
        )
        df["告示番号"] = df["告示番号"].mask(
            df["施設名"] == "川西市立総合医療センター", "31028002"
        )

        # 在院日数,97(輸血以外の再掲)を削除
        df = df.iloc[4:]
        df = df.T
        df.reset_index(inplace=True)
        df = df[~df["columns"].str.contains("97（輸血以外の再掲）")]
        if mode == "在院日数":
            df = df[~df["columns"].str.contains("件数")]
        if mode == "件数":
            df = df[~df["columns"].str.contains("在院日数")]
        df = df.T
        df.columns = df.iloc[0]
        df = df.iloc[1:]
        # 縦持ちに変換して並び替え
        df = df.melt(id_vars=["告示番号", "通番", "施設名"])
        df = df.sort_values(["告示番号", "columns"])
        # 10件未満で[-]の列を削除
        df.loc[df.value == "-", "value"] = 0
        # 　上で結合したカラム名を再度分離
        df["mdc6"] = df["columns"].str.split(pat="_", expand=True)[0]
        df["mdc6name"] = df["columns"].str.split(pat="_", expand=True)[1]
        df["ope"] = df["columns"].str.split(pat="_", expand=True)[3]
        # 　並び替え等してから結合
        df = df.sort_values(["告示番号", "mdc6", "ope"], ascending=[True, True, False])
        df = df.reset_index(drop=True)
        df = df[cols]
        data = data.append(df)
    # loop終了後,インデックスを振り直し
    data = data.reset_index(drop=True)
    if mode == "在院日数":
        data = data.rename(columns={"value": "stay"})
    return data


# %%
def merge_mdc6(mdc6_value, mdc6_stay):
    print(mdc6_value.shape)
    print(mdc6_stay.shape)
    print(len(mdc6_value.loc[mdc6_value["value"] == 0]))
    print(len(mdc6_stay.loc[mdc6_stay["stay"] == 0]))
    mdc6 = mdc6_value.merge(
        mdc6_stay,
        how="left",
        on=["告示番号", "通番", "施設名", "mdc6", "mdc6name", "ope"],
    )
    mdc6 = mdc6.rename(columns={"告示番号": "hpcd", "施設名": "hpname"})
    return mdc6


##########################################################################################
# %%
mdc6_value = mdc6_oep_hp_load(mode="件数")

# %%
mdc6_value.to_pickle(os.path.join(output_dir, "mdc6_value.pkl"))

# %%
mdc6_stay = mdc6_oep_hp_load(mode="在院日数")

# %%
mdc6_stay.to_pickle(os.path.join(output_dir, "mdc6_stay.pkl"))

##########################################################################################

# %%
# pickelの読み込み
mdc6_value = pd.read_pickle(os.path.join(output_dir, "mdc6_value.pkl"))
mdc6_stay = pd.read_pickle(os.path.join(output_dir, "mdc6_stay.pkl"))

# %%
mdc6 = merge_mdc6(mdc6_value, mdc6_stay)
mdc6.head(1)

# %%
mdc6.describe(include="all")

# %%
# outputdirにpickelで保存
mdc6.to_pickle(os.path.join(output_dir, "mdc6.pkl"))

#########################################################################################

# %%
# pickelの読み込み
mdc6 = pd.read_pickle(os.path.join(output_dir, "mdc6.pkl"))


# %%
# 6.mdc2の集計
def make_mdc2():
    data_file = "（２）MDC別医療機関別件数（割合）.xlsx"
    mdc2 = pd.read_excel(
        os.path.join(input_dir, data_file), dtype="object", skiprows=[0, 2]
    )
    # セル結合されていたため、空白になっている列を穴埋め
    mdc2[["告示番号", "通番", "施設名"]] = mdc2[["告示番号", "通番", "施設名"]].fillna(
        method="ffill"
    )
    # 10件未満で[-]になっているデータを穴埋め
    mdc2 = mdc2.replace("-", 0)
    mdc2 = mdc2.drop(["通番"], axis="columns")

    # 合併病院の個別処理
    mdc2["告示番号"] = mdc2["告示番号"].mask(
        mdc2["施設名"] == "兵庫県立はりま姫路総合医療センター", "31037002"
    )
    mdc2["告示番号"] = mdc2["告示番号"].mask(
        mdc2["施設名"] == "医療法人錦秀会阪和記念病院", "30912002"
    )
    mdc2["告示番号"] = mdc2["告示番号"].mask(
        mdc2["施設名"] == "川西市立総合医療センター", "31028002"
    )

    # 縦持ちに変換
    mdc2 = mdc2.melt(id_vars=["告示番号", "施設名", "手術"], ignore_index=False)
    mdc2 = mdc2.rename(
        columns={"variable": "mdc", "施設名": "hpname", "告示番号": "hpcd"}
    )
    mdc2 = mdc2.sort_values(["hpcd", "mdc"])
    # 手術ありなしに分かれているので集計
    mdc2 = mdc2.groupby(by=["hpcd", "mdc"], as_index=False).sum()
    mdc2.columns = ["hpcd", "mdc2", "value"]
    return mdc2


# %%
mdc2 = make_mdc2()
mdc2.describe(include="all")

# %%
# 7.データの確認
# 7.0 目検
hp.head(1)

# %%
hp.describe()

# %%
dpc_mst.head(1)

# %%
dpc_mst.describe(include="all")

# %%
mdc6.head(1)

# %%
mdc6.describe(include="all")

# %%
mdc2.head(1)

# %%
mdc2.describe(include="all")


# %%
# 7.1 hpcdの確認
def data_cheack(leftdf, rightdf, colname):
    l = pd.Series(leftdf[colname].unique())
    r = pd.Series(rightdf[colname].unique())
    l_len = len(l)
    r_len = len(r)
    print(f"left length is {l_len}")
    print(f"right length is {r_len}")
    print(f"left in right is {l_len == sum(l.isin(r))}")
    print(f"right in left is {r_len == sum(r.isin(l))}")


# %%
data_cheack(mdc2, hp, "hpcd")

# %%
data_cheack(mdc6, hp, "hpcd")

# %%
data_cheack(mdc2, mdc6, "hpcd")

# %%
# 7.2 dpcコードの確認
data_cheack(dpc_mst, mdc2, "mdc2")

# %%
data_cheack(mdc6, dpc_mst, "mdc6")

# %%
# A1. Altair_streamlit用にデータを加工

# A1_1 hp_mstの作成

# 1 hp_mstの作成
# [hpcd,hpname, pref, med2,city,bed]
# pref med2 cityは名称でOK 中でカテゴリ変数として使用する
# valueの追加　→おそらく不要　ソートや0件削除したあとに削除する
# valueで降順ソート
# 0件の病院は削除
# 病床数0は要確認
# 病院名を35文字以内にしなければいけない→vegaがエラーを吐く
# 表示されるのは14文字だけ
# 全角スペースは半角スペースに置き換える
# # 石心会は法人名を消しておく
# 内部処理
# 　1 hp_listを作成　件数多い順で表示するので、このデータのhpname列をそのまま使う
# （pref_listはコードで直打ちする）

# %%
hp["bed"] = hp["bed"].astype(int)
hp.describe().T

# %%
hp[hp["bed"] == 0]

# %%
# mdc2テーブルを病院別に集計してをhp_mstに付与する
hp_value_df = mdc2.groupby("hpcd", as_index=False).sum()[["hpcd", "value"]]

# %%
hp = hp.merge(hp_value_df, on="hpcd")

# %%
hp.isnull().sum()

# %%
# 削除する病院は療養や回復期の病院であることを確認
hp[(hp["value"] == 0) & (hp["pref"] == "埼玉県")]

# %%
# 実績が0の病院を削除することでbed0の病院が消えることを確認
hp[hp["bed"] == 0]

# %%
hp = hp.loc[hp["value"] > 0]
hp.describe().T


# %%
# 病院名が長すぎる問題について
hp.loc[hp["hpname"].str.len() > 35, "hpname"]

# %%
hp["hpname"] = hp["hpname"].mask(
    hp["hpname"]
    == "長野県厚生農業協同組合連合会鹿教湯三才山リハビリテーションセンター鹿教湯病院",
    "鹿教湯三才山リハビリテーションセンター鹿教湯病院",
)


# %%
hp["hpname"] = hp["hpname"].mask(
    hp["hpname"] == "社会医療法人財団石心会　川崎幸病院", "川崎幸病院"
)
hp["hpname"] = hp["hpname"].mask(
    hp["hpname"] == "社会医療法人財団石心会　埼玉石心会病院", "埼玉石心会病院"
)
hp["hpname"] = hp["hpname"].mask(
    hp["hpname"] == "医療法人社団新東京石心会さいわい鶴見病院", "さいわい鶴井病院"
)

# %%
# 全角スペースを半角スペースに変更
hp["hpname"] = hp["hpname"].str.replace("　", " ")

# %%
hp = hp.sort_values(["value", "hpcd"], ascending=[False, True]).reset_index(drop=True)
hp.columns

# %%
hp_mst = hp[["hpcd", "hpname", "pref", "med2", "city", "bed",'month']]
hp_mst.describe(include="all")

# %%
hp["hpcd"] = hp["hpcd"].astype(int)

# %%
# hp_mst.to_csv("data/hp_mst.csv", index=False)
hp_mst.to_csv(os.path.join(output_dir, "hp_mst.csv"), index=False)

# %%
# A1_2_mdc26_mstの作成
# 2 mdc26_mst
# [mdc2name, mdc6,mdc6name]
# ope_aggに結合するのに使用する
dpc_mst.head(1)

# %%
mdc26_mst = dpc_mst[["mdc2", "mdc6", "mdc6name"]].drop_duplicates()

# %%
mdc26_mst.describe()

# %%
mdc26_mst["mdc2"] = mdc26_mst["mdc2"].astype(int)

# %%
# mdc26_mst.to_csv("data/mdc26_mst.csv", encoding="cp932", index=False)
mdc26_mst.to_csv(
    os.path.join(output_dir, "mdc26_mst.csv"), encoding="cp932", index=False
)

# %%
# A1_3 mdc2_mst
mdc2_mst.head(1)

# %%
mdc2_mst["mdc2"] = mdc2_mst["mdc2"].astype(int)

# %%
# mdc2_mst.to_csv("data/mdc2_mst.csv", encoding="cp932", index=False)
mdc2_mst.to_csv(os.path.join(output_dir, "mdc2_mst.csv"), encoding="cp932", index=False)

# %%
# A1_3 ope_mstの作成

# 3 mdc6ope__mst
# [mdc6,ope,opename]
# dpc_mstからkコードの列を削除
# ope_aggに名称を付与するためのテーブル
# 99手術ありと97その他手術ありに、mdc6nameを付与したopenameを作成
dpc_mst.head(1)

# %%
dpc_mst["mdc6name"].str[7:]

# %%
f = dpc_mst["opename"].isin(["99 手術なし", "97 その他手術"])
dpc_mst["opename"] = dpc_mst["opename"].mask(
    f, dpc_mst["opename"] + "_" + dpc_mst["mdc6name"].str[7:]
)

dpc_mst.head(5)

# %%
mdc6ope_mst = dpc_mst[["mdc6", "ope", "opename"]]
mdc6ope_mst = mdc6ope_mst.drop_duplicates()
# %%
mdc6ope_mst.describe()
# %%
mdc6ope_mst["ope"] = mdc6ope_mst["ope"].astype(int)
# %%
mdc6ope_mst.head(1)
# %%
# mdc6ope_mst.to_csv("data/mdc6ope_mst.csv", encoding="cp932", index=False)
mdc6ope_mst.to_csv(
    os.path.join(output_dir, "mdc6ope_mst.csv"), encoding="cp932", index=False
)
# %%
# A1_4 mdc_dataの作成

# 4 mdc_data
# MDC2別のグラフ用
# [hpname,mdcname,value]
mdc2.head(1)
# %%
mdc2_mst.head(1)
# %%
hp.head(1)
# %%
mdc2["mdc2"] = mdc2["mdc2"].astype(int)
mdc2["hpcd"] = mdc2["hpcd"].astype(int)
# %%
mdc2 = mdc2.merge(mdc2_mst, on="mdc2")
# %%
mdc2.head(1)
# %%
mdc2 = mdc2.merge(hp[["hpcd", "hpname"]], on="hpcd")
mdc2.head(1)
# %%
mdc2_data = mdc2[["hpcd", "mdc2", "value"]]
# %%
mdc2_data
# %%
mdc2_data = mdc2_data.loc[mdc2["value"] > 0]
# %%
mdc2_data = mdc2_data.sort_values(
    ["value", "hpcd", "mdc2"], ascending=[False, True, True]
).reset_index(drop=True)
# %%
mdc2_data.head(1)
# %%
mdc2_data.describe(include="all")
# %%
# mdc2_data.to_csv("data/mdc2_data.csv", encoding="cp932", index=False)
mdc2_data.to_csv(
    os.path.join(output_dir, "mdc2_data.csv"), encoding="cp932", index=False
)

# %%
# A1_5 mdc6_dataの作成
mdc6_data = mdc6.loc[:, ["hpcd", "mdc6", "ope", "value"]]
# %%
mdc6_data
# %%
mdc6_data = mdc6_data.groupby(["hpcd", "mdc6"]).sum()["value"].reset_index(drop=False)
print(len(mdc6_data))
mdc6_data.head(5)
# %%
mdc6_data = mdc6_data.loc[mdc6_data["value"] > 0]
# %%
mdc6_data = mdc6_data.sort_values(
    ["value", "hpcd", "mdc6"], ascending=[False, True, True]
)
# %%
mdc6_data["hpcd"] = mdc6_data["hpcd"].astype(int)
# %%
# mdc6_data.to_csv("data/mdc6_data.csv", encoding="cp932", index=False)
mdc6_data.to_csv(
    os.path.join(output_dir, "mdc6_data.csv"), encoding="cp932", index=False
)

# %%
# A1_6 ope_dataの作成
mdc6.head(1)

# %%
ope_data = mdc6.loc[:, ["hpcd", "mdc6", "ope", "value"]]
# %%
ope_data = ope_data.loc[ope_data["value"] > 0]
# %%
ope_data = ope_data.sort_values(
    ["value", "hpcd", "mdc6", "ope"], ascending=[False, True, True, True]
)
# %%
ope_data["hpcd"] = ope_data["hpcd"].astype(int)
ope_data["ope"] = ope_data["ope"].astype(int)
# %%
ope_data
# %%
# ope_data.to_csv("data/ope_data.csv", encoding="cp932", index=False)
# ope_data.to_csv(os.path.join(output_dir, "ope_data.csv"), encoding="cp932", index=False)

# %%
# A1_7 mdc2とmdc6を比較して,10件未満で削除された文を補完する
mdc2_data
# %%
mdc2_data[mdc2_data["hpcd"] == 20025]
# %%
ope_data.head(1)
# %%
ope_data.dtypes
# %%
ope_data["mdc2"] = ope_data["mdc6"].str[:2]
# %%
ope_data["mdc2"] = ope_data["mdc2"].astype(int)
# %%
ope_data["value"] = ope_data["value"].astype(int)
# %%
ope_data_agg = ope_data.groupby(["hpcd", "mdc2"]).sum()["value"].reset_index()
ope_data_agg
# %%
ope_data_agg = mdc2_data.merge(ope_data_agg, how="left", on=["hpcd", "mdc2"])
# %%
f = ope_data_agg["value_y"].isnull()
ope_data_agg[f]
# %%
ope_data_agg["value_y"] = ope_data_agg["value_y"].mask(f, 0)
ope_data_agg[f]
# %%
ope_data_agg["value"] = ope_data_agg["value_x"] - ope_data_agg["value_y"]
# %%
ope_data_agg["value"] = ope_data_agg["value"].astype(int)
# %%
ope_data_agg
# %%
ope_data_agg[ope_data_agg["hpcd"] == 20025]
# %%
ope_data_agg = ope_data_agg[["hpcd", "mdc2", "value"]].copy(deep=True)
# %%
ope_data_agg["mdc2"] = ope_data_agg["mdc2"].astype(str).str.zfill(2)
# %%
ope_data_agg["mdc6"] = ope_data_agg["mdc2"] + "0000"
# %%
ope_data_agg = ope_data_agg[ope_data_agg["value"] != 0].copy(deep=True)
# %%
ope_data_agg["ope"] = 0
# %%
ope_data_agg = ope_data_agg[["hpcd", "mdc6", "ope", "value"]].copy(deep=True)
# %%
ope_data_agg
# %%
ope_data2 = pd.concat([ope_data, ope_data_agg])
ope_data2 = ope_data2[["hpcd", "mdc6", "ope", "value"]].copy(deep=True)
ope_data2
# %%
# ope_data2.to_csv("data/ope_data.csv", encoding="cp932", index=False)
ope_data2.to_csv(
    os.path.join(output_dir, "ope_data.csv"), encoding="cp932", index=False
)

# %%
