import streamlit as st
import ccxt
import pandas as pd
import plotly.graph_objects as go
from ta.momentum import RSIIndicator
import time

# Cấu hình trang Web
st.set_page_config(page_title="Crypto RSI Dashboard", layout="wide")
st.title("📊 Biểu Đồ RSI Top 100 Coin (Bản Tooltip Xịn)")

# Khởi tạo sàn KuCoin (hoặc Binance tùy sếp đang xài ổn cái nào)
exchange = ccxt.kucoin({
    'enableRateLimit': True,
})

@st.cache_data(ttl=3600) 
def get_top_100_data():
    tickers = exchange.fetch_tickers()
    usdt_pairs = {k: v for k, v in tickers.items() if k.endswith('/USDT')}
    sorted_pairs = sorted(usdt_pairs.items(), key=lambda x: x[1]['quoteVolume'], reverse=True)
    # Trả về cả tên coin và dữ liệu ticker (giá, % thay đổi)
    return sorted_pairs[:100]

def get_rsi(symbol, timeframe, period=14):
    try:
        bars = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=100)
        df = pd.DataFrame(bars, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['RSI'] = RSIIndicator(close=df['close'], window=period).rsi()
        return round(df['RSI'].iloc[-1], 2)
    except:
        return None

timeframe = st.selectbox("⏳ Chọn khung thời gian:", ["15m", "1h", "4h", "1d"], index=1)

if st.button("🔄 Cập nhật dữ liệu ngay bây giờ"):
    st.write(f"Đang kéo dữ liệu RSI khung {timeframe}... Sếp đợi xíu nhé ⏳")
    
    progress_bar = st.progress(0)
    top_100_data = get_top_100_data()
    results = []
    
    for i, (symbol, ticker) in enumerate(top_100_data):
        rsi_val = get_rsi(symbol, timeframe)
        if rsi_val is not None:
            # Lấy thêm thông tin Giá và Biến động 24h
            price = ticker.get('last', 0)
            change_24h = ticker.get('percentage', 0)
            
            results.append({
                "Coin": symbol.replace('/USDT', ''), 
                "RSI": rsi_val, 
                "Index": i+1,
                "Price": price,
                "Change24h": round(change_24h, 2) if change_24h else 0
            })
        progress_bar.progress((i + 1) / 100)
        time.sleep(0.1)
        
    df_res = pd.DataFrame(results)

    # --- PHẦN VẼ BIỂU ĐỒ VÀ TOOLTIP ---
    fig = go.Figure()

    # Tạo nội dung cho Tooltip khi rê chuột (Hovertemplate)
    hovertemplate = (
        "<b>%{customdata[0]} (Top %{x})</b><br>" +
        "RSI (" + timeframe + "): %{y}<br>" +
        "Price: $%{customdata[1]}<br>" +
        "24h Change: %{customdata[2]}%<br>" +
        "<extra></extra>" # Ẩn đi những thông tin rác thừa của Plotly
    )

    fig.add_trace(go.Scatter(
        x=df_res['Index'],
        y=df_res['RSI'],
        mode='markers+text',
        text=df_res['Coin'],
        textposition="top center",
        # Đưa dữ liệu phụ vào customdata để Tooltip lôi ra xài
        customdata=df_res[['Coin', 'Price', 'Change24h']], 
        hovertemplate=hovertemplate,
        marker=dict(
            size=10,
            color=['#FF6347' if r >= 70 else '#00FF7F' if r <= 30 else 'gray' for r in df_res['RSI']],
            line=dict(width=1, color='DarkSlateGrey')
        )
    ))

    # Vẽ nền
    fig.add_hrect(y0=0, y1=30, fillcolor="#98FB98", opacity=0.2, line_width=0)
    fig.add_hrect(y0=70, y1=100, fillcolor="#FFB6C1", opacity=0.15, line_width=0) 
    fig.add_hline(y=70, line_dash="dash", line_color="#FF6347")
    fig.add_hline(y=30, line_dash="dash", line_color="#00FF7F")

    fig.update_layout(
        title=f"Scatter Plot RSI - Top 100 Coin (Khung {timeframe})",
        xaxis_title="Thứ hạng Coin (Theo Volume)",
        yaxis_title="Giá trị RSI",
        yaxis=dict(range=[0, 100]),
        height=800,
        hoverlabel=dict(
            bgcolor="black",
            font_size=14,
            font_family="Arial",
            font_color="white"
        )
    )

    st.plotly_chart(fig, use_container_width=True)
