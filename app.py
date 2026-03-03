import streamlit as st
import alkana
import jaconv
import streamlit.components.v1 as components
import re

# 1. ページ構成とテーマ設定
st.set_page_config(
    page_title="英語ルビ振りツール Pro",
    page_icon="📚",
    layout="centered"
)

# UIデザインの適用（UDフォント継承と配色の最適化）
st.markdown("""
    <style>
    #MainMenu, header, footer, .stDeployButton {visibility: hidden;}
    html, body, [class*="css"], .stMarkdown, .stButton, .stTextArea {
        font-family: "UD デジタル 教科書体 NK-R", sans-serif !important;
    }
    .stApp { background-color: #f9f4e6; color: #5d4037; }
    .stButton>button { 
        background-color: #8d6e63; color: white; border-radius: 8px; 
        font-weight: bold; width: 100%; height: 3em; transition: 0.3s;
    }
    .stButton>button:hover { background-color: #6d4c41; border-color: #6d4c41; }
    h1 { color: #5d4037; text-align: center; font-size: 1.8rem !important; margin-bottom: 1rem; }
    </style>
""", unsafe_allow_html=True)

if 'html_content' not in st.session_state: st.session_state['html_content'] = ""
if 'converted' not in st.session_state: st.session_state['converted'] = False

# 2. 【核心】高度なルビ振りロジック
def get_kana_smart(word, custom_dict):
    lower_word = word.lower()
    
    # --- ステップ1: 直接ヒット ---
    if lower_word in custom_dict: return custom_dict[lower_word]
    res = alkana.get_kana(lower_word)
    if res: return res

    # --- ステップ2: 語形変化の吸収 (Suffixes) ---
    # 進行形 -ing
    if lower_word.endswith("ing") and len(lower_word) > 5:
        stem = lower_word[:-3]
        for s in [stem, stem + "e", stem[:-1]]:
            res = alkana.get_kana(s)
            if res: return res + "イング"
    # 過去形・過去分詞 -ed
    if lower_word.endswith("ed") and len(lower_word) > 3:
        stem = lower_word[:-2]
        for s in [stem, stem + "e", stem[:-1]]:
            res = alkana.get_kana(s)
            if res: return res + "ド"
    # 複数形・三単現 -s / -es
    if lower_word.endswith("s") and len(lower_word) > 2:
        singular = lower_word[:-2] if lower_word.endswith("es") else lower_word[:-1]
        res = alkana.get_kana(singular)
        if res:
            suffix = "ツ" if singular.endswith("t") else "ス" if singular.endswith(("k", "p", "f")) else "ズ"
            return res + suffix

    # --- ステップ3: 接頭辞の分離 (Prefixes) ---
    prefixes = {
        "dis": "ディス", "un": "アン", "re": "リ", "pre": "プリ", "non": "ノン", 
        "anti": "アンチ", "mis": "ミス", "multi": "マルチ", "inter": "インター", "sub": "サブ"
    }
    for p, p_kana in prefixes.items():
        if lower_word.startswith(p) and len(lower_word) > len(p) + 2:
            stem = lower_word[len(p):]
            stem_kana = alkana.get_kana(stem) or custom_dict.get(stem)
            if stem_kana: return p_kana + stem_kana

    # --- ステップ4: 複合語の分割 (Compounds) ---
    if len(lower_word) >= 6:
        for i in range(3, len(lower_word) - 2):
            part1, part2 = lower_word[:i], lower_word[i:]
            k1 = alkana.get_kana(part1) or custom_dict.get(part1)
            k2 = alkana.get_kana(part2) or custom_dict.get(part2)
            if k1 and k2: return k1 + k2
            
    return None

# 3. メインUI
st.markdown('<h1>📚 英語ルビ振り文章作成ツール</h1>', unsafe_allow_html=True)

# 入力エリア
default_text = "The disability didn't stop the evergreen project. iPhone15 is running smoothly."
text_input = st.text_area("▼ 英文を入力してください", height=150, value=default_text)

# レイアウト設定
with st.expander("🎨 レイアウト・スタイル設定", expanded=True):
    col1, col2, col3 = st.columns(3)
    with col1: font_size = st.slider("本文サイズ (pt)", 10, 40, 18)
    with col2: ruby_size = st.slider("ルビサイズ (pt)", 5, 20, 9)
    with col3: line_height = st.slider("行の間隔", 1.0, 4.0, 2.8, 0.1)

# 4. 実行エンジン
if st.button("ルビ付きテキストを生成する"):
    if text_input:
        # 基本語・特殊語の辞書
        custom_dict = {
            "a": "ア", "an": "アン", "the": "ザ", "i": "アイ", "my": "マイ", "me": "ミー", 
            "'s": "ズ", "'t": "ト", "n't": "ト", "'m": "ム", "'re": "アー", "is": "イズ",
            "don't": "ドーント", "doesn't": "ダズント", "can't": "キャント", "youtube": "ユーチューブ"
        }

        # CSSスタイル
        style = f"""
        <style>
            body {{ 
                font-family: 'UD デジタル 教科書体 NK-R', sans-serif; 
                font-size: {font_size}pt; line-height: {line_height}; 
                background-color: transparent; color: #5d4037;
            }}
            ruby {{ ruby-align: center; }}
            rt {{ font-size: {ruby_size}pt; font-family: 'UD デジタル 教科書体 NK-R', sans-serif; color: #8d6e63; }}
        </style>
        """
        
        html_body = ""
        lines = text_input.split('\n')
        for line in lines:
            # 英数字、ハイフン、アポストロフィを一つの塊として保持
            tokens = re.split(r"([a-zA-Z0-9'-]+)", line)
            for token in tokens:
                if not token: continue
                if re.match(r"[a-zA-Z0-9'-]+", token):
                    kana = get_kana_smart(token, custom_dict)
                    if kana:
                        z_kana = jaconv.h2z(kana) # 全角に変換
                        html_body += f'<ruby><rb>{token}</rb><rt>{z_kana}</rt></ruby>'
                    else:
                        html_body += f"<span>{token}</span>"
                else:
                    # スペースや記号はそのまま表示
                    html_body += f"<span>{token}</span>"
            html_body += "<br>"

        # HTML全体の組み立て
        full_html = f"""
        <html lang="ja" class="notranslate" translate="no">
        <head><meta charset="utf-8">{style}</head>
        <body>{html_body}</body></html>
        """
        st.session_state['html_content'] = full_html
        st.session_state['converted'] = True

# 5. 表示とダウンロード
if st.session_state['converted']:
    st.markdown("---")
    st.subheader("👀 プレビュー")
    components.html(st.session_state['html_content'], height=400, scrolling=True)
    
    st.markdown("---")
    st.subheader("💾 ファイル保存")
    # Wordで開けるようにBOM付きHTMLとしてダウンロード
    st.download_button(
        label="📄 Word形式（HTML）をダウンロード", 
        data="\ufeff" + st.session_state['html_content'], 
        file_name="ruby_text.doc", 
        mime="text/html"
    )
