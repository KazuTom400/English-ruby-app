import streamlit as st
import alkana
import jaconv
import streamlit.components.v1 as components
import re

# 1. ページ構成
st.set_page_config(page_title="英語ルビ振りツール Pro", page_icon="📚", layout="centered")

st.markdown("""
    <style>
    #MainMenu, header, footer, .stDeployButton {visibility: hidden;}
    html, body, [class*="css"], .stMarkdown, .stButton, .stTextArea {
        font-family: "UD デジタル 教科書体 NK-R", sans-serif !important;
    }
    .stApp { background-color: #f9f4e6; color: #5d4037; }
    .stButton>button { 
        background-color: #8d6e63; color: white; border-radius: 8px; 
        font-weight: bold; width: 100%; height: 3em;
    }
    h1 { color: #5d4037; text-align: center; font-size: 1.8rem !important; }
    </style>
""", unsafe_allow_html=True)

if 'html_content' not in st.session_state: st.session_state['html_content'] = ""
if 'converted' not in st.session_state: st.session_state['converted'] = False

# 2. 【核心】語尾対応を強化したロジック
def get_kana_smart(word, custom_dict):
    lower_word = word.lower()
    
    # --- 1. 直接ヒット ---
    if lower_word in custom_dict: return custom_dict[lower_word]
    res = alkana.get_kana(lower_word)
    if res: return res

    # --- 2. 接尾辞（Suffixes）の処理：smoothly, powerful 対策 ---
    suffixes = {
        "ly": "リー", "ful": "フル", "less": "レス", "ment": "メント",
        "ness": "ネス", "tion": "ション", "able": "エイブル"
    }
    for s, s_kana in suffixes.items():
        if lower_word.endswith(s) and len(lower_word) > len(s) + 2:
            stem = lower_word[:-len(s)]
            # happily (y->i) のようなケースへの対応
            stems_to_try = [stem]
            if stem.endswith("i"): stems_to_try.append(stem[:-1] + "y")
            
            for stm in stems_to_try:
                res = alkana.get_kana(stm) or custom_dict.get(stm)
                if res: return res + s_kana

    # --- 3. 動詞・名詞の活用形 (-ing, -ed, -s) ---
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

    # --- 4. 接頭辞の分離 (dis-, un-) ---
    prefixes = {"dis": "ディス", "un": "アン", "re": "リ", "pre": "プリ", "anti": "アンチ"}
    for p, p_kana in prefixes.items():
        if lower_word.startswith(p) and len(lower_word) > len(p) + 2:
            stem = lower_word[len(p):]
            res = alkana.get_kana(stem) or custom_dict.get(stem)
            if res: return p_kana + res

    # --- 5. 複合語の分割 (evergreen) ---
    if len(lower_word) >= 6:
        for i in range(3, len(lower_word) - 2):
            part1, part2 = lower_word[:i], lower_word[i:]
            k1, k2 = alkana.get_kana(part1), alkana.get_kana(part2)
            if k1 and k2: return k1 + k2
            
    return None

# 3. メインUI
st.markdown('<h1>📚 英語ルビ振り文章作成ツール</h1>', unsafe_allow_html=True)
# 【ここを追加！】クローラー用の静的な説明文
st.write("""
英語のテキストに自動でカタカナのルビ（読み仮名）を振ることができるオンラインツールです。
独自のアルゴリズムにより、-ingや-edなどの活用形、smoothlyなどの副詞にも正確にルビを付与します。
英文読解のスピードアップや、多読のトレーニングに最適です。
""")

with st.container():
    st.info("💡 使い方：下のボックスに英文を入力して、生成ボタンを押すだけでWord形式での保存も可能です。")

# 入力エリア（既存のコード）
default_text = "The system is running smoothly. It is a powerful and evergreen tool."
text_input = st.text_area("▼ 英文を入力", height=150, value=default_text)

with st.expander("🎨 レイアウト設定", expanded=True):
    col1, col2, col3 = st.columns(3)
    with col1: font_size = st.slider("本文サイズ", 10, 40, 18)
    with col2: ruby_size = st.slider("ルビサイズ", 5, 20, 9)
    with col3: line_height = st.slider("行間", 1.0, 4.0, 2.8, 0.1)

# 4. 実行エンジン
if st.button("ルビ付きテキストを生成する"):
    if text_input:
        custom_dict = {
            "a": "ア", "an": "アン", "the": "ザ", "i": "アイ", "my": "マイ", "me": "ミー", 
            "'s": "ズ", "'t": "ト", "n't": "ト", "is": "イズ", "don't": "ドーント"
        }
        
        style = f"<style>body {{ font-family: 'UD デジタル 教科書体 NK-R', sans-serif; font-size: {font_size}pt; line-height: {line_height}; background-color: transparent; color: #5d4037; }} ruby {{ ruby-align: center; }} rt {{ font-size: {ruby_size}pt; color: #8d6e63; }}</style>"
        
        html_body = ""
        lines = text_input.split('\n')
        for line in lines:
            tokens = re.split(r"([a-zA-Z0-9'-]+)", line)
            for token in tokens:
                if not token: continue
                if re.match(r"[a-zA-Z0-9'-]+", token):
                    kana = get_kana_smart(token, custom_dict)
                    if kana:
                        html_body += f'<ruby><rb>{token}</rb><rt>{jaconv.h2z(kana)}</rt></ruby>'
                    else:
                        html_body += f"<span>{token}</span>"
                else:
                    html_body += f"<span>{token}</span>"
            html_body += "<br>"

        st.session_state['html_content'] = f'<html lang="ja" class="notranslate" translate="no"><head><meta charset="utf-8">{style}</head><body>{html_body}</body></html>'
        st.session_state['converted'] = True

# 5. 表示とダウンロード
if st.session_state['converted']:
    st.markdown("---")
    components.html(st.session_state['html_content'], height=400, scrolling=True)
    st.download_button(label="📄 Word形式で保存", data="\ufeff" + st.session_state['html_content'], file_name="ruby_text.doc", mime="text/html")
