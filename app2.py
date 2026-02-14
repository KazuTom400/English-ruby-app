import streamlit as st

# --- ここを追加：session_stateの初期化 ---
if 'html_content' not in st.session_state:
    st.session_state['html_content'] = "" # 最初は空っぽにしておく
# ---------------------------------------

# その後の既存コード...
import alkana
import jaconv
import streamlit.components.v1 as components
import re

# 1. ページ設定：一番最初に書く必要があります
st.set_page_config(
    page_title="英語の表→ルビ付き英語の表",
    page_icon="📋",
    layout="centered"
)

# 2. デザイン調整：Streamlitのヘッダー・フッターを消し、フォントを統一
st.markdown("""
    <script>
        var html = window.parent.document.getElementsByTagName('html')[0];
        html.setAttribute('lang', 'ja');
        html.setAttribute('class', 'notranslate');
        html.setAttribute('translate', 'no');
    </script>
    <style>
    /* Streamlit標準のメニューやボタンをすべて隠す */
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display:none;}
    [data-testid="stHeader"] {display:none;}
    [data-testid="stToolbar"] {display:none;}
    
    /* フォントと背景の設定 */
    html, body, [class*="css"], .stMarkdown, .stSlider, .stButton, .stTextArea {
        font-family: "UD デジタル 教科書体 NK-R", "UD Digi Kyokashotai NK-R", sans-serif !important;
    }
    .stApp { background-color: #f9f4e6; color: #5d4037; }
    .stButton>button { background-color: #8d6e63; color: white; border-radius: 5px; font-weight: bold; width: 100%; border: none; }
    
    /* アプリ内のタイトルは控えめな見出しにする */
    h3 { color: #5d4037; text-align: center; margin-top: -80px; margin-bottom: 20px; }
    </style>
""", unsafe_allow_html=True)

# --- 賢いルビ振りロジック ---
def get_kana_smart(word, custom_dict):
    lower_word = word.lower()
    if lower_word in custom_dict: return custom_dict[lower_word]
    kana = alkana.get_kana(lower_word)
    if kana: return kana
    if lower_word.endswith("s") and len(lower_word) > 1:
        singular = lower_word[:-2] if lower_word.endswith("es") else lower_word[:-1]
        stem = custom_dict.get(singular) or alkana.get_kana(singular)
        if stem:
            if lower_word.endswith("es"): return stem + "イズ"
            return stem + ("ツ" if singular.endswith("t") else "ス" if singular.endswith(("k", "p", "f")) else "ズ")
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

# --- メイン画面 ---
st.markdown('<h3 class="notranslate" translate="no">📋 英語の表→ルビ付き英語の表</h3>', unsafe_allow_html=True)

text_input = st.text_area(
    "▼ 英文を入力、またはExcel・Wordの表から貼り付けてください", 
    height=200, 
    placeholder="Excelの1列をコピーしてここに貼り付けると、自動で1マスずつ分割されます！",
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

custom_dict = {
    "i": "アイ", "my": "マイ", "ken": "ケン", "tokyo": "トウキョウ", "'s": "ズ", "'t": "ト",
    "smartphone": "スマートフォン", "iphone": "アイフォン", "internet": "インターネット"
}

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
    html_header = f"""
    <html xmlns:o='urn:schemas-microsoft-com:office:office' 
          xmlns:w='urn:schemas-microsoft-com:office:word' 
          lang="ja" class="notranslate" translate="no">
    <head><meta charset="utf-8">{style}</head><body><table>"""
    
    lines = text_input.strip().split('\n')
    body_content = ""
    for l in lines:
        if l.strip():
            ruby_line = text_to_ruby_html(l, custom_dict)
            body_content += f"<tr><td>{ruby_line}</td></tr>"
            
    st.session_state['table_content'] = html_header + body_content + "</table></body></html>"

if 'table_content' in st.session_state:
    st.markdown("---")
    st.subheader("👀 プレビュー")
    st.warning("⚠️ **注意：直接コピーせず、下のボタンからWordを保存してください。**")
    components.html(st.session_state['table_content'], height=500, scrolling=True)
    
    st.markdown("---")
    st.subheader("💾 Word形式で保存")
    # パスワード入力なしで、即ダウンロードボタンを表示
    st.success("作成が完了しました！下のボタンから保存できます。")
    st.download_button(
        label="📄 Wordファイルをダウンロード",
        data=st.session_state['html_content'],
        file_name="ruby_print.doc",
        mime="application/msword"
    )


