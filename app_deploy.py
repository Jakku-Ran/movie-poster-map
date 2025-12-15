import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import json
import random
from datetime import datetime, timedelta

# --- 設定頁面與 CSS ---
st.set_page_config(page_title="特典映畫 | Live Map", layout="wide", page_icon="🎬")

st.markdown("""
<style>
    .main-title {
        font-size: 3em;
        font-weight: bold;
        color: #FFFFFF;
        background-color: #000000;
        padding: 20px;
        text-align: center;
        text-transform: uppercase;
        letter-spacing: 2px;
    }
    .movie-title {
        font-size: 1.2em;
        font-weight: bold;
        margin-top: 10px;
        margin-bottom: 5px;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    div[data-testid="column"] button {
        width: 100%;
    }
    /* 調整 Radio Button 的樣式 */
    div[role="radiogroup"] {
        background-color: #f0f2f6;
        padding: 10px;
        border-radius: 10px;
    }
</style>
""", unsafe_allow_html=True)

# --- 預設圖與影城資料庫 ---
PLACEHOLDER_IMG = "https://dummyimage.com/300x450/5c5c5c/ffffff&text=No+Poster"
CINEMA_DB = {
    "台北信義威秀": [25.0355, 121.5670], "台北京站威秀": [25.0494, 121.5173],
    "板橋大遠百威秀": [25.0137, 121.4646], "新竹巨城威秀": [24.8096, 120.9747],
    "台中大遠百威秀": [24.1643, 120.6416], "台南南紡威秀": [22.9912, 120.2338],
    "高雄大遠百威秀": [22.6139, 120.3042], "台北欣欣秀泰": [25.0543, 121.5256],
    "新北板橋秀泰": [25.0107, 121.4593], "高雄夢時代秀泰": [22.5951, 120.3069]
}

# --- 讀取資料函式 ---
@st.cache_data
def load_movies_safe():
    data = []
    try:
        with open('movies.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
    except:
        pass
    return data

# --- 模擬數據函式 ---
def get_inventory_mock(movie_title):
    inventory_data = {}
    random.seed(movie_title) 
    for cinema_name in CINEMA_DB.keys():
        stock = 0 if random.random() < 0.2 else random.randint(1, 100)
        inventory_data[cinema_name] = stock
    return inventory_data

def get_timeline_mock(movie_title):
    data = []
    base_time = datetime.now()
    actions = ["網友回報", "影城公告", "系統更新"]
    for i in range(5): 
        time_offset = base_time - timedelta(hours=i*random.randint(1, 5), minutes=random.randint(0, 59))
        cinema = random.choice(list(CINEMA_DB.keys()))
        stock_change = random.randint(-10, 0)
        data.append({
            "更新時間": time_offset.strftime("%Y-%m-%d %H:%M"),
            "資料來源": random.choice(actions),
            "相關影城": cinema,
            "庫存變動": f"{stock_change} 份" if stock_change != 0 else "無變動"
        })
    df = pd.read_json(json.dumps(data))
    return df

# --- 頁面視圖 ---

def show_home_page(movies):
    """首頁：海報牆視圖"""
    st.markdown('<div class="main-title">現正熱映特典一覽</div>', unsafe_allow_html=True)
    st.caption("點擊下方電影查看各地影城庫存分佈。")
    st.write("") 

    if not movies:
        st.warning("目前沒有電影資料，請確認 movies.json 是否存在。")
        return

    cols_per_row = 4
    rows = len(movies) // cols_per_row + (1 if len(movies) % cols_per_row > 0 else 0)

    for row_idx in range(rows):
        cols = st.columns(cols_per_row)
        for col_idx in range(cols_per_row):
            movie_idx = row_idx * cols_per_row + col_idx
            if movie_idx < len(movies):
                movie = movies[movie_idx]
                with cols[col_idx]:
                    img_url = movie.get('poster_url') if movie.get('poster_url') else PLACEHOLDER_IMG
                    st.image(img_url, use_container_width=True)
                    st.markdown(f'<div class="movie-title" title="{movie["title"]}">{movie["title"]}</div>', unsafe_allow_html=True)
                    if st.button("查看庫存地圖", key=f"btn_{movie['id']}"):
                        st.session_state['selected_movie'] = movie
                        st.rerun()

def show_detail_page():
    """詳情頁：地圖與回報功能"""
    movie = st.session_state['selected_movie']
    
    if st.button("← 返回首頁"):
        st.session_state['selected_movie'] = None
        st.rerun()

    st.markdown(f'<div class="main-title" style="font-size: 2em;">{movie["title"]}</div>', unsafe_allow_html=True)

    col1, col2 = st.columns([1, 2])

    with col1:
        # 左側：海報
        img_url = movie.get('poster_url') if movie.get('poster_url') else PLACEHOLDER_IMG
        st.image(img_url, use_container_width=True)
        
        # --- 新增功能：使用者回報區塊 (修改版) ---
        st.divider()
        st.subheader("📢 協助回報數據")
        with st.form("report_form"):
            target_cinema = st.selectbox("選擇影城", list(CINEMA_DB.keys()))
            
            # 這裡改用 Radio Button (單選)
            status_option = st.radio(
                "目前庫存狀態",
                ["🟢 還有剩餘", "🔴 已發送完畢"],
                horizontal=True # 讓選項橫向排列，比較好看
            )
            
            submitted = st.form_submit_button("送出回報")
            
            if submitted:
                st.success(f"感謝！已收到您回報：{target_cinema} 為「{status_option}」。")
                st.balloons() 

        if movie.get('sheet_url'):
            st.link_button("📊 查看原始 Excel 表單", movie['sheet_url'])

    with col2:
        # 右側：地圖與時間軸
        st.subheader("🗺️ 全台影城庫存分佈")
        inventory = get_inventory_mock(movie['title'])
        m = folium.Map(location=[23.97565, 120.9738819], zoom_start=7, tiles="cartodb dark_matter")

        for name, coord in CINEMA_DB.items():
            stock = inventory.get(name, 0)
            color = "green" if stock > 50 else ("orange" if stock > 0 else "red")
            radius = 15 if stock > 50 else (10 if stock > 0 else 5)

            folium.CircleMarker(
                location=coord, radius=radius, color=color, fill=True, fill_color=color, fill_opacity=0.7,
                popup=folium.Popup(f"<b>{name}</b><br>剩餘: {stock} 份", max_width=200),
                tooltip=f"{name}: {stock}份"
            ).add_to(m)
            
        st_folium(m, width=None, height=500, key="detail_map")

        st.divider()
        st.subheader("📅 最新資料更新紀錄")
        timeline_df = get_timeline_mock(movie['title'])
        st.dataframe(timeline_df, hide_index=True, use_container_width=True)

# --- 主程式邏輯 ---
def main():
    if 'selected_movie' not in st.session_state:
        st.session_state['selected_movie'] = None

    movies_data = load_movies_safe()

    if st.session_state['selected_movie'] is None:
        show_home_page(movies_data)
    else:
        show_detail_page()

if __name__ == "__main__":
    main()