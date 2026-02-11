import streamlit as st
import alkana
import jaconv
import streamlit.components.v1 as components
import re

# ページ設定
st.set_page_config(page_title="英語ルビ振り【英文の表→ルビ付き英文の表】", layout="centered")

# --- デザイン調整（翻訳ガード & UDデジタル教科書体） ---
st.markdown("""
    <script>
        var html = window.parent.document.getElementsByTagName('html')[0];
        html.setAttribute('lang', 'ja');
        html.setAttribute('class', 'notranslate');
        html.setAttribute('translate', 'no');
    </script>
    <style>
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display:none;}
    html, body, [class*="css"], .stMarkdown, .stSlider, .stButton, .stTextArea {
        font-family: "UD デジタル 教科書体 NK-R", "UD Digi Kyokashotai NK-R", sans-serif !important;
    }
    .stApp { background-color: #f9f4e6; color: #5d4037; }
    .stButton>button { background-color: #8d6e63; color: white; border-radius: 5px; font-weight: bold; width: 100%; }
    h1 { font-family: "UD デジタル 教科書体 NK-B", sans-serif !important; color: #5d4037; text-align: center; margin-top: -50px; }
    </style>
""", unsafe_allow_html=True)

# --- ロジック関数 ---
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
            z_kana = jaconv.h2z(kana)
            html_output += f'<ruby class="notranslate" translate="no"><rb>{w}</rb><rt>{z_kana}</rt></ruby><span> </span>'
        else:
            html_output += f'<span class="notranslate" translate="no">{w} </span>'
    return html_output

# --- メイン UI ---
st.markdown('<h1 class="notranslate" translate="no">📋 英語ルビ振り【英文の表→ルビ付き英文の表】</h1>', unsafe_allow_html=True)

# ✨ 1. 入力エリアの強化（Excel/Wordコピペへの言及）
text_input = st.text_area(
    "▼ 英文を入力、またはExcel・Wordの表から貼り付けてください", 
    height=200, 
    placeholder="【時短のコツ】Excelの1列をそのままコピーしてここに貼り付けると、自動で1マスずつに分割されます！",
    value="He can jump the highest in this school.\nThis bag is the newest of the five."
)

st.subheader("📏 サイズ・余白調整")
col1, col2 = st.columns(2)
with col1:
    font_size = st.slider("本文の大きさ (pt)", 10, 40, 20)
    ruby_size = st.slider("ルビの大きさ (pt)", 5, 20, 10)
with col2:
    cell_padding = st.slider("マスの余白 (px)", 0, 50, 10)
    line_height = st.slider("行の間隔", 1.0, 3.5, 2.5, 0.1)

custom_dict = {"i": "アイ", "my": "マイ", "'s": "ズ", "'t": "ト"}

# 2. 作成ボタン
if st.button("ルビ付き表を作成・更新する"):
    style = f"""
    <style>
        body {{ font-family: "UD デジタル 教科書体 NK-R", sans-serif; background-color: white; padding: 10px; }}
        table {{ width: 100%; border-collapse: collapse; border: 2px solid black; }}
        td {{ border: 2px solid black; padding: {cell_padding}px; font-size: {font_size}pt; line-height: {line_height}; vertical-align: middle; }}
        ruby {{ ruby-align: center; }}
        rt {{ font-size: {ruby_size}pt; color: #000; }}
    </style>
    """
    html_header = f'<html lang="ja" class="notranslate" translate="no"><head><meta charset="utf-8">{style}</head><body><table>'
    
    lines = text_input.strip().split('\n')
    body_content = ""
    for l in lines:
        if l.strip():
            ruby_line = text_to_ruby_html(l, custom_dict)
            body_content += f"<tr><td>{ruby_line}</td></tr>"
            
    st.session_state['table_content'] = html_header + body_content + "</table></body></html>"

# ✨ 3. 結果表示と「コピペ禁止」の注意喚起
if 'table_content' in st.session_state:
    st.markdown("---")
    st.subheader("👀 プレビュー")
    
    # 強力な警告メッセージの追加
    st.warning("⚠️ **注意：プレビューを直接コピー＆ペーストすると、枠線やサイズが正しく反映されません。** 教材として使用する場合は、必ず下のボタンからWordファイルをダウンロードしてください。")
    
    components.html(st.session_state['table_content'], height=500, scrolling=True)
    
    st.markdown("---")
    st.subheader("💾 Word形式で保存")
    password = st.text_input("パスワードを入力してEnter", type="password")
    
    if password == st.secrets.get("PASSWORD", "test"):
        st.success("認証されました。")
        st.download_button(
            label="📄 表形式のWordファイルをダウンロード",
            data=st.session_state['table_content'],
            file_name="english_table_print.doc",
            mime="application/msword"
        )
    elif password:
        st.error("パスワードが違います。")




