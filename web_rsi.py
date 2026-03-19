import streamlit as st
import ccxt
import pandas as pd
import plotly.graph_objects as go
from ta.momentum import RSIIndicator
import time  # Thêm công cụ quản lý thời gian

# Cấu hình trang Web
st.set_page_config(page_title="Crypto RSI Dashboard", layout="wide")
st.title("📊 Biểu Đồ RSI Top 100 Coin")

# Khởi tạo sàn OKX (Rất thân thiện) 
# 'enableRateLimit': True giúp bot tự động phanh lại nếu sàn yêu cầu
exchange = ccxt.okx({
    'enableRateLimit': True,
})

# Hàm lấy Top 100
@st.cache_data(ttl=3600) 
def get_top_100_usdt():
    tickers = exchange.fetch_tickers()
    usdt_pairs = {k: v for k, v in tickers.items() if k.endswith('/USDT')}
    sorted_pairs = sorted(usdt_pairs.items(), key=lambda x: x[1]['quoteVolume'], reverse=True)
    return [pair[0] for pair in sorted_pairs[:100]]

# Hàm tính RSI
def get_rsi(symbol, timeframe, period=14):
    try:
        bars = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=100)
        df = pd.DataFrame(bars, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['RSI'] = RSIIndicator(close=df['close'], window=period).rsi()
        return round(df['RSI'].iloc[-1], 2)
    except:
        return None

# Giao diện chọn Khung thời gian
timeframe = st.selectbox("⏳ Chọn khung thời gian:", ["15m", "1h", "4h", "1d"], index=1)

# Nút Cập nhật dữ liệu
if st.button("🔄 Cập nhật dữ liệu ngay bây giờ"):
    st.write(f"Đang kéo dữ liệu RSI khung {timeframe}... Sếp đợi xíu nhé ⏳")
    
    progress_bar = st.progress(0)
    top_coins = get_top_100_usdt()
    results = []
    
    for i, coin in enumerate(top_coins):
        rsi_val = get_rsi(coin, timeframe)
        if rsi_val is not None:
            results.append({"Coin": coin.replace('/USDT', ''), "RSI": rsi_val, "Index": i+1})
        progress_bar.progress((i + 1) / 100)
        
        # TUYỆT CHIÊU CHỐNG BLOCK: Dừng 0.1 giây sau khi soi xong 1 con
        time.sleep(0.1)
        
    df_res = pd.DataFrame(results)
    
    # LỌC TÊN
    display_text = [coin if (r >= 70 or r <= 30) else "" for coin, r in zip(df_res['Coin'], df_res['RSI'])]

    # --- PHẦN VẼ BIỂU ĐỒ ---
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df_res['Index'],
        y=df_res['RSI'],
        mode='markers+text',
        text=display_text,
        textposition="top center",
        marker=dict(
            size=10,
            color=['#FF6347' if r >= 70 else '#00FF7F' if r <= 30 else 'gray' for r in df_res['RSI']],
            line=dict(width=1, color='DarkSlateGrey')
        )
    ))

    fig.add_hrect(y0=0, y1=30, fillcolor="#98FB98", opacity=0.2, line_width=0)
    fig.add_hrect(y0=0, y1=20, fillcolor="#00FF7F", opacity=0.3, line_width=0, annotation_text="Strong Oversold")
    fig.add_hrect(y0=70, y1=100, fillcolor="#FFB6C1", opacity=0.15, line_width=0) 
    fig.add_hrect(y0=80, y1=100, fillcolor="#FF6347", opacity=0.25, line_width=0, annotation_text="Strong Overbought")
    fig.add_hline(y=70, line_dash="dash", line_color="#FF6347")
    fig.add_hline(y=30, line_dash="dash", line_color="#00FF7F")

    fig.update_layout(
        title=f"Scatter Plot RSI - Top 100 Coin (Khung {timeframe})",
        xaxis_title="Thứ hạng Coin (Theo Volume)",
        yaxis_title="Giá trị RSI",
        yaxis=dict(range=[0, 100]),
        height=1000 
    )

    st.plotly_chart(fig, use_container_width=True)
