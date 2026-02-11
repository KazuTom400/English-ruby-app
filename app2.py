import streamlit as st
import alkana
import jaconv
import streamlit.components.v1 as components
import re

# ページ設定
st.set_page_config(page_title="英語ルビ振り【表形式・詳細調整版】", layout="centered")

# ---------------------------------------------------------
# デザイン調整：UI全体をUDデジタル教科書体に
# ---------------------------------------------------------
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display:none;}
    
    /* アプリ全体のフォント設定 */
    html, body, [class*="css"], .stMarkdown, .stSlider, .stButton, .stTextArea {
        font-family: "UD デジタル 教科書体 NK-R", "UD Digi Kyokashotai NK-R", "BIZ UDPGothic", sans-serif !important;
    }

    .stApp { background-color: #f9f4e6; color: #5d4037; }
    .stButton>button { background-color: #8d6e63; color: white; border-radius: 5px; width: 100%; }
    
    h1 {
        font-family: "UD デジタル 教科書体 NK-B", "UD Digi Kyokashotai NK-B", sans-serif !important;
        color: #5d4037;
        text-align: center;
        margin-top: -50px;
    }
    </style>
""", unsafe_allow_html=True)

# --- ロジック関数 (変更なし) ---
def get_kana_smart(word, custom_dict):
    lower_word = word.lower()
    if lower_word in custom_dict: return custom_dict[lower_word]
    kana = alkana.get_kana(lower_word)
    if kana: return kana
    if lower_word.endswith("s") and len(lower_word) > 1:
        singular = lower_word[:-1]
        stem = custom_dict.get(singular) or alkana.get_kana(singular)
        if stem: return stem + ("ツ" if singular.endswith("t") else "ス" if singular.endswith(("k", "p", "f")) else "ズ")
    return None

def text_to_ruby_html(input_text, custom_dict):
    tokens = re.findall(r"[\w]+|['][\w]+|[.,!?;:\"()\-]", input_text)
    html_output = ""
    strip_chars = '.,!?"'
    for w in tokens:
        clean_word = w.strip(strip_chars)
        kana = get_kana_smart(clean_word, custom_dict)
        if kana:
            html_output += f'<ruby><rb>{w}</rb><rt>{jaconv.h2z(kana)}</rt></ruby><span> </span>'
        else:
            html_output += f"<span>{w} </span>"
    return html_output

# --- メイン UI ---
st.markdown('<h1 class="notranslate">📋 英語ルビ振り【表形式・詳細調整版】</h1>', unsafe_allow_html=True)

text_input = st.text_area("▼ 英文を1行ずつ入力してください", height=150, 
                         value="He can jump the highest in this school.\nThis bag is the newest of the five.")

st.subheader("📏 サイズ調整")
col1, col2 = st.columns(2)
with col1:
    font_size = st.slider("文字の大きさ (pt)", 10, 40, 20)
    ruby_size = st.slider("ルビの大きさ (pt)", 5, 20, 10)
with col2:
    cell_padding = st.slider("マスの余白 (px)", 0, 50, 10)
    line_height = st.slider("行の間隔", 1.0, 3.5, 2.5, 0.1)

custom_dict = {"i": "アイ", "my": "マイ", "'s": "ズ", "'t": "ト"}

if st.button("ルビ付き表を作成・更新する"):
    # ★ プレビューとWord用のフォント指定もUDデジタル教科書体に統一 ★
    style = f"""
    <style>
        body {{ 
            font-family: 'UD デジタル 教科書体 NK-R', 'UD Digi Kyokashotai NK-R', 'Century', serif; 
        }}
        table {{ width: 100%; border-collapse: collapse; border: 2px solid black; }}
        td {{ 
            border: 2px solid black; 
            padding: {cell_padding}px; 
            font-size: {font_size}pt; 
            line-height: {line_height}; 
            background-color: white; 
        }}
        ruby {{ ruby-align: center; }}
        rt {{ font-size: {ruby_size}pt; color: #000; }}
    </style>
    """
    html_header = f"<html><head><meta charset='utf-8'>{style}</head><body><table border='1'>"
    lines = text_input.strip().split('\n')
    body_content = "".join([f"<tr><td>{text_to_ruby_html(l, custom_dict)}</td></tr>" for l in lines if l.strip()])
    st.session_state['table_content'] = html_header + body_content + "</table></body></html>"

# --- 結果表示・保存セクション (以下省略) ---
# (前回のパスワード・ダウンロード・フッター部分を続けてください)
