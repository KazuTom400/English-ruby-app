import streamlit as st
import alkana
import jaconv
import streamlit.components.v1 as components
import re

# ページ設定
st.set_page_config(
    page_title="英語ルビ振り文章作成ツール【通常モード】",
    page_icon="📚",
    layout="centered"
)

# ---------------------------------------------------------
# Google翻訳による誤変換を防ぐための設定
# ---------------------------------------------------------
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
    h1 { font-family: "UD デジタル 教科書体 NK-B", sans-serif !important; color: #5d4037; text-align: center; font-size: 1.8rem !important; }
    </style>
""", unsafe_allow_html=True)

# セッション状態の初期化
if 'html_content' not in st.session_state: st.session_state['html_content'] = ""
if 'converted' not in st.session_state: st.session_state['converted'] = False

# --- 賢いルビ振りロジック (修正版) ---
def get_kana_smart(word, custom_dict):
    # すべて小文字にして判定
    lower_word = word.lower()
    
    # 1. カスタム辞書に完全一致があるか (don't など)
    if lower_word in custom_dict:
        return custom_dict[lower_word]
    
    # 2. alkanaで取得できるか
    kana = alkana.get_kana(lower_word)
    if kana:
        return kana
    
    # 3. アポストロフィを含む短縮形 (doesn't, she's など) の分解処理
    if "'" in lower_word:
        parts = lower_word.split("'")
        prefix = parts[0]
        suffix = "'" + parts[1]
        
        # 前半（does）と後半（'t）をそれぞれ変換して合体
        p_kana = custom_dict.get(prefix) or alkana.get_kana(prefix)
        s_kana = custom_dict.get(suffix)
        
        if p_kana and s_kana:
            return p_kana + s_kana
        elif p_kana: # 後半が辞書にない場合は前半のみ
            return p_kana

    # 4. 複数形の処理
    if lower_word.endswith("s") and len(lower_word) > 1:
        singular = lower_word[:-1]
        stem = custom_dict.get(singular) or alkana.get_kana(singular)
        if stem:
            suffix = "ツ" if singular.endswith("t") else "ス" if singular.endswith(("k", "p", "f")) else "ズ"
            return stem + suffix
            
    return None

# --- メイン UI ---
st.markdown('<h1 class="notranslate" translate="no">📚 英語ルビ振り文章作成ツール</h1>', unsafe_allow_html=True)

text_input = st.text_area("▼ ここに英文を入力してください", height=150, 
                         value="She's my best friend. Tom's cat is cute. I don't like apples. He doesn't swim.")

st.subheader("📏 レイアウト微調整")
col1, col2 = st.columns(2)
with col1:
    font_size = st.slider("本文の大きさ (pt)", 10, 40, 18)
    ruby_size = st.slider("ルビの大きさ (pt)", 5, 20, 9)
with col2:
    line_height = st.slider("行の間隔（高さ）", 1.0, 4.0, 2.5, 0.1)

if st.button("ルビ付きテキストを作成する"):
    if text_input:
        # カスタム辞書の拡充
        custom_dict = {
            "i": "アイ", "my": "マイ", "me": "ミー", "mine": "マイン",
            "'s": "ズ", "'t": "ト", "n't": "ト", "'m": "ム", "'re": "アー", 
            "'ve": "ブ", "'ll": "ル", "'d": "ド",
            "don't": "ドーント", "doesn't": "ダズント", "can't": "キャント",
            "isn't": "イズント", "aren't": "アーント", "won't": "ウォント"
        }

        style = f"""
            <style>
                body {{
                    font-family: 'UD デジタル 教科書体 NK-R', 'UD Digi Kyokashotai NK-R', serif;
                    font-size: {font_size}pt;
                    color: #000000;
                    line-height: {line_height};
                }}
                ruby {{ ruby-align: center; }}
                rt {{
                    color: #000000;
                    font-family: 'UD デジタル 教科書体 NK-R', sans-serif;
                    font-size: {ruby_size}pt;
                }}
            </style>
        """
        
        html = f"""
        <html xmlns:o='urn:schemas-microsoft-com:office:office' 
              xmlns:w='urn:schemas-microsoft-com:office:word' 
              lang="ja" class="notranslate" translate="no">
        <head><meta charset='utf-8'>{style}</head>
        <body><div class=WordSection1><p class=MsoNormal>
        """
        
        # 処理ロジック
        lines = text_input.split('\n')
        for line in lines:
            # 修正した正規表現: 単語（アポストロフィ含む）か、記号かを分ける
            words = re.findall(r"[a-zA-Z']+|[.,!?;:\"()\-]", line)
            for word in words:
                # 記号のみの場合
                if re.match(r"^[.,!?;:\"()\-]$", word):
                    html += f"<span>{word}</span> "
                    continue
                
                # 単語の処理
                kana = get_kana_smart(word, custom_dict)
                if kana:
                    z_kana = jaconv.h2z(kana)
                    html += f'<ruby class="notranslate" translate="no"><rb>{word}</rb><rt>{z_kana}</rt></ruby> '
                else:
                    html += f"<span>{word}</span> "
            html += "<br>" 

        html += "</p></div></body></html>"
        st.session_state['html_content'] = html
        st.session_state['converted'] = True

# 3. 結果表示
if st.session_state['converted']:
    st.markdown("---")
    st.subheader("👀 プレビュー")
    components.html(st.session_state['html_content'], height=400, scrolling=True)
    
    st.markdown("---")
    st.subheader("💾 Word形式で保存")
    st.success("作成が完了しました！下のボタンから保存できます。")
    
    bom_html = "\ufeff" + st.session_state['html_content']

    st.download_button(
        label="📄 Word形式（HTML）をダウンロード",
        data=bom_html,
        file_name="ruby_print.doc",
        mime="text/html"
    )
