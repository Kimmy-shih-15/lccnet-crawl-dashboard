# -*- coding: utf-8 -*-
"""
Created on Sun Sep 20 09:23:07 2026

@author: USER
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
from bs4 import BeautifulSoup
import jieba
from collections import Counter

# ---------------------------------------------------------
# 1. 頁面配置
# ---------------------------------------------------------
st.set_page_config(page_title="文字雲實戰演練儀表板", layout="wide")
st.title("聯成電腦文章詞頻分析")
st.caption("透過網頁爬蟲與 Jieba 中文斷詞，分析聯成電腦文章的熱門關鍵字")

# ---------------------------------------------------------
# 2. 準備模擬資料集 (含 OHLCV 與 Lesson 9 NLP 斷詞/情緒成果)
# ---------------------------------------------------------
# 建立 10 個交易日的價量與情緒資料
# trade_dates = pd.date_range("2026-09-01", periods=14, freq="D")
# trade_dates = trade_dates[trade_dates.dayofweek < 5][:10] # 僅保留工作日

# stock_df = pd.DataFrame({
#     "date": trade_dates,
#     "open":  [1010.0, 1015.0, 1025.0, 1020.0, 1030.0, 1035.0, 1025.0, 1040.0, 1050.0, 1045.0],
#     "high":  [1020.0, 1030.0, 1035.0, 1025.0, 1040.0, 1045.0, 1030.0, 1055.0, 1060.0, 1055.0],
#     "low":   [1005.0, 1010.0, 1015.0, 1010.0, 1025.0, 1020.0, 1015.0, 1035.0, 1040.0, 1035.0],
#     "close": [1015.0, 1025.0, 1020.0, 1030.0, 1035.0, 1025.0, 1040.0, 1050.0, 1045.0, 1050.0],
#     "volume": [32000, 41000, 28000, 35000, 48000, 39000, 52000, 61000, 45000, 43000],
#     "sentiment": [+0.45, +0.78, -0.12, +0.35, +0.82, -0.41, +0.65, +0.91, +0.22, +0.54],
#     "top_keyword": ["法說看好", "營收新高", "外資調節", "散戶進場", "護國神山", "短線獲利", "多頭重啟", "狂飆暴賺", "量縮整理", "主力回補"]
# })



url = "https://www.lccnet.com.tw/lccnet/article/details/2675"

headers = {
    "User-Agent": "Mozilla/5.0"
}

# 抓取網頁
response = requests.get(url, headers=headers)
response.encoding = "utf-8"

# 解析 HTML
soup = BeautifulSoup(response.text, "html.parser")

# 取得文字
text = soup.get_text(separator=" ", strip=True)

# jieba 斷詞
words = jieba.lcut(text)

# 停用詞
stop_words = [
    "的", "了", "是", "在", "與", "和",
    "也", "有", "讓", "更", "就", "都",
    "聯成", "電腦"
]

# 清理文字
clean_words = []

for word in words:
    word = word.strip()

    if len(word) >= 2 and word not in stop_words:
        clean_words.append(word)

# 統計詞頻
word_count = Counter(clean_words)

# 印出前 30 名
print("===== 詞頻 TOP 30 =====")

for word, count in word_count.most_common(30):
    print(word, count)

# 取聯成電腦文章詞頻前 50 名
top_words = word_count.most_common(50)

# 轉成 DataFrame
wordcloud_df = pd.DataFrame(
    top_words,
    columns=["word", "count"]
)

print(wordcloud_df)

# ==========================================
# 聯成電腦文章互動文字雲
# ==========================================

st.subheader("☁️ 聯成電腦文章熱門關鍵字")

# Counter → DataFrame
wordcloud_df = pd.DataFrame(
    word_count.most_common(50),
    columns=["word", "count"]
)


# ------------------------------
# 計算文字位置
# ------------------------------

def calculate_spiral_layout(n_words: int):

    theta = np.linspace(0, 4.5 * np.pi, n_words)
    radius = np.linspace(0, 1.1, n_words)

    np.random.seed(42)

    jitter_theta = theta + np.random.uniform(
        -0.15, 0.15, n_words
    )

    return (
        radius * np.cos(jitter_theta),
        radius * np.sin(jitter_theta)
    )


x_pos, y_pos = calculate_spiral_layout(len(wordcloud_df))

wordcloud_df["x"] = x_pos
wordcloud_df["y"] = y_pos


# ------------------------------
# 詞頻越高 → 字越大
# ------------------------------

c_min = wordcloud_df["count"].min()
c_max = wordcloud_df["count"].max()

if c_max == c_min:
    wordcloud_df["font_size"] = 30
else:
    wordcloud_df["font_size"] = (
        16
        + (wordcloud_df["count"] - c_min)
        / (c_max - c_min)
        * 30
    )


# ------------------------------
# 根據詞頻設定顏色
# ------------------------------

def get_color(count):

    if count >= wordcloud_df["count"].quantile(0.75):
        return "#ef4444"

    elif count >= wordcloud_df["count"].quantile(0.5):
        return "#f59e0b"

    else:
        return "#10b981"


wordcloud_df["color"] = (
    wordcloud_df["count"].apply(get_color)
)


# ------------------------------
# 建立互動文字雲
# ------------------------------

fig_wc = go.Figure()

fig_wc.add_trace(
    go.Scatter(

        x=wordcloud_df["x"],
        y=wordcloud_df["y"],

        mode="text",

        text=wordcloud_df["word"],

        textfont=dict(
            size=wordcloud_df["font_size"],
            color=wordcloud_df["color"],
            family="system-ui, -apple-system, sans-serif"
        ),

        customdata=wordcloud_df["count"],

        hovertemplate=
            "<b>關鍵字：</b> %{text}<br>" +
            "<b>出現次數：</b> %{customdata} 次" +
            "<extra></extra>"
    )
)


# ------------------------------
# 隱藏座標軸
# ------------------------------

fig_wc.update_layout(

    xaxis=dict(
        showgrid=False,
        showticklabels=False,
        zeroline=False,
        range=[-1.4, 1.4]
    ),

    yaxis=dict(
        showgrid=False,
        showticklabels=False,
        zeroline=False,
        range=[-1.4, 1.4]
    ),

    plot_bgcolor="rgba(241, 245, 249, 0.6)",
    paper_bgcolor="rgba(0, 0, 0, 0)",

    height=520,

    margin=dict(
        l=20,
        r=20,
        t=20,
        b=20
    )
)


st.plotly_chart(
    fig_wc,
    use_container_width=True
)


# =========================
# Streamlit 儀表板
# =========================

st.title("📊 聯成電腦文章詞頻分析")

st.caption("分析聯成電腦網站文章內容，呈現常見關鍵字與詞頻分布")


# -------------------------
# 統計資訊
# -------------------------

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        label="關鍵字數量",
        value=len(wordcloud_df)
    )

with col2:
    st.metric(
        label="最高出現次數",
        value=wordcloud_df["count"].max()
    )

with col3:
    st.metric(
        label="總詞頻",
        value=wordcloud_df["count"].sum()
    )


st.divider()



# -------------------------
# TOP 10 關鍵字
# -------------------------

st.subheader("🏆 TOP 10 熱門關鍵字")

top10 = wordcloud_df.sort_values(
    "count",
    ascending=False
).head(10)

st.bar_chart(
    top10,
    x="word",
    y="count"
)


# -------------------------
# 詞頻資料
# -------------------------

st.subheader("📋 關鍵字詞頻資料")

st.dataframe(
    wordcloud_df,
    use_container_width=True
)