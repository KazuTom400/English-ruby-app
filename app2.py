import streamlit as st
import alkana
import jaconv
import streamlit.components.v1 as components
import re

# --- 1. ページ設定 ---
st.set_page_config(
    page_title="英語の表→ルビ付き英語の表 Pro",
    page_icon="📋",
    layout="centered"
)

# session_stateの初期化
if 'table_content' not in st.session_state:
    st.session_state['table_content'] = ""

# 2. デザイン調整（既存のスタイルを維持）
st.markdown("""
    <style>
    #MainMenu, header, footer, .stDeployButton, [data-testid="stHeader"], [data-testid="stToolbar"] {visibility: hidden; display:none;}
    html, body, [class*="css"], .stMarkdown, .stSlider, .stButton, .stTextArea {
        font-family: "UD デジタル 教科書体 NK-R", sans-serif !important;
    }
    .stApp { background-color: #f9f4e6; color: #5d4037; }
    .stButton>button { background-color: #8d6e63; color: white; border-radius: 5px; font-weight: bold; width: 100%; border: none; height: 3em; }
    h3 { color: #5d4037; text-align: center; margin-top: -60px; margin-bottom: 20px; }
    </style>
""", unsafe_allow_html=True)

# --- 3. 【Pro版】高度なルビ振りロジック ---
def get_kana_smart(word, custom_dict):
    lower_word = word.lower()
    
    # 1. 直接ヒット
    if lower_word in custom_dict: return custom_dict[lower_word]
    res = alkana.get_kana(lower_word)
    if res: return res

    # 2. 接尾辞（Suffixes）対応
    suffixes = {"ly": "リー", "ful": "フル", "less": "レス", "ment": "メント", "ness": "ネス", "tion": "ション", "able": "エイブル"}
    for s, s_kana in suffixes.items():
        if lower_word.endswith(s) and len(lower_word) > len(s) + 2:
            stem = lower_word[:-len(s)]
            stems_to_try = [stem]
            if stem.endswith("i"): stems_to_try.append(stem[:-1] + "y")
            for stm in stems_to_try:
                res = alkana.get_kana(stm) or custom_dict.get(stm)
                if res: return res + s_kana

    # 3. 活用形対応
    if lower_word.endswith("ing") and len(lower_word) > 5:
        stem = lower_word[:-3]
        for s in [stem, stem + "e", stem[:-1]]:
            res = alkana.get_kana(s)
            if res: return res + "イング"
    if lower_word.endswith("ed") and len(lower_word) > 3:
        stem = lower_word[:-2]
        for s in [stem, stem + "e", stem[:-1]]:
            res = alkana.get_kana(s)
            if res: return res + "ド"
    if lower_word.endswith("s") and len(lower_word) > 2:
        singular = lower_word[:-2] if lower_word.endswith("es") else lower_word[:-1]
        res = alkana.get_kana(singular)
        if res:
            suffix = "ツ" if singular.endswith("t") else "ス" if singular.endswith(("k", "p", "f")) else "ズ"
            return res + suffix

    # 4. 接頭辞対応
    prefixes = {"dis": "ディス", "un": "アン", "re": "リ", "pre": "プリ", "anti": "アンチ"}
    for p, p_kana in prefixes.items():
        if lower_word.startswith(p) and len(lower_word) > len(p) + 2:
            stem = lower_word[len(p):]
            res = alkana.get_kana(stem) or custom_dict.get(stem)
            if res: return p_kana + res

    # 5. 複合語の分割
    if len(lower_word) >= 6:
        for i in range(3, len(lower_word) - 2):
            part1, part2 = lower_word[:i], lower_word[i:]
            k1, k2 = alkana.get_kana(part1), alkana.get_kana(part2)
            if k1 and k2: return k1 + k2
    return None

# --- 4. メイン画面 ---
st.markdown('<h3 class="notranslate" translate="no">📋 英語の表→ルビ付き英語の表 Pro</h3>', unsafe_allow_html=True)

# 説明文（クローラー対策）
st.write("ExcelやWordから英文を貼り付けるだけで、高度な解析ロジックを用いたルビ付きの美しい表を自動生成します。")

text_input = st.text_area(
    "▼ 英文を入力、またはExcel・Wordの表から貼り付けてください", 
    height=200, 
    placeholder="1行ごとに1マスの表が作成されます。",
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

# カスタム辞書
custom_dict = {
    "a": "ア", "an": "アン", "the": "ザ", "i": "アイ", "my": "マイ", "me": "ミー", 
    "ken": "ケン", "tokyo": "トウキョウ", "'s": "ズ", "'t": "ト", "n't": "ト", "is": "イズ"
}

if st.button("ルビ付き表を作成・更新する"):
    # スタイル定義
    style = f"""
    <style>
        body {{ font-family: "UD デジタル 教科書体 NK-R", sans-serif; background-color: white; padding: 10px; }}
        table {{ width: 100%; border-collapse: collapse; border: 2px solid black; }}
        td {{ border: 2px solid black; padding: {cell_padding}px; font-size: {font_size}pt; line-height: {line_height}; vertical-align: middle; color: #000; }}
        ruby {{ ruby-align: center; }}
        rt {{ font-size: {ruby_size}pt; color: #555; }}
    </style>
    """
    
    html_header = f"""
    <html lang="ja" class="notranslate" translate="no">
    <head><meta charset="utf-8">{style}</head><body><table>"""
    
    body_content = ""
    lines = text_input.strip().split('\n')
    
    for line in lines:
        if not line.strip(): continue
        
        # Pro版のトークン分割ロジックを採用
        ruby_line = ""
        tokens = re.split(r"([a-zA-Z0-9'-]+)", line)
        for token in tokens:
            if not token: continue
            if re.match(r"[a-zA-Z0-9'-]+", token):
                kana = get_kana_smart(token, custom_dict)
                if kana:
                    z_kana = jaconv.h2z(kana)
                    ruby_line += f'<ruby><rb>{token}</rb><rt>{z_kana}</rt></ruby>'
                else:
                    ruby_line += f"<span>{token}</span>"
            else:
                ruby_line += f"<span>{token}</span>"
        
        body_content += f"<tr><td>{ruby_line}</td></tr>"
            
    st.session_state['table_content'] = html_header + body_content + "</table></body></html>"

# 5. 表示とダウンロード
if st.session_state['table_content']:
    st.markdown("---")
    st.subheader("👀 プレビュー")
    st.warning("⚠️ **注意：直接コピーせず、下のボタンからWordを保存してください。**")
    components.html(st.session_state['table_content'], height=500, scrolling=True)
    
    st.markdown("---")
    st.subheader("💾 Word形式で保存")
    bom_html = "\ufeff" + st.session_state['table_content']

    st.download_button(
        label="📄 Word形式（HTML）をダウンロード",
        data=bom_html,
        file_name="ruby_table.doc",
        mime="text/html"
    )
