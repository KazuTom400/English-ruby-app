import streamlit as st
import alkana
import jaconv
import streamlit.components.v1 as components
import re

# ページ設定
st.set_page_config(page_title="英語ルビ振り【表形式・詳細調整版】", layout="centered")

# ---------------------------------------------------------
# 【ガード1】ブラウザ全体への翻訳停止命令
# ---------------------------------------------------------
st.markdown("""
    <script>
        // 親ウィンドウ（Streamlit本体）のhtmlタグに翻訳拒否を設定
        var html = window.parent.document.getElementsByTagName('html')[0];
        html.setAttribute('lang', 'ja');
        html.setAttribute('class', 'notranslate');
        html.setAttribute('translate', 'no');
    </script>
    <style>
    /* 不要なメニューを非表示 */
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display:none;}
    
    /* 全体のデザインとフォント */
    html, body, [class*="css"], .stMarkdown, .stSlider, .stButton, .stTextArea {
        font-family: "UD デジタル 教科書体 NK-R", "UD Digi Kyokashotai NK-R", "BIZ UDPGothic", sans-serif !important;
    }
    .stApp { background-color: #f9f4e6; color: #5d4037; }
    .stButton>button { background-color: #8d6e63; color: white; border-radius: 5px; width: 100%; }
    h1 { font-family: "UD デジタル 教科書体 NK-B", sans-serif !important; color: #5d4037; text-align: center; margin-top: -50px; }
    </style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# ロジック関数 (翻訳拒否属性を追加)
# ---------------------------------------------------------
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
        
        # 【ガード2】英単語を含むスパンに translate="no" を付与
        if kana:
            z_kana = jaconv.h2z(kana)
            html_output += f'<ruby class="notranslate" translate="no"><rb>{w}</rb><rt>{z_kana}</rt></ruby><span> </span>'
        else:
            html_output += f'<span class="notranslate" translate="no">{w} </span>'
            
    return html_output

# --- メイン UI ---
st.markdown('<h1 class="notranslate" translate="no">📋 英語ルビ振り【表形式・詳細調整版】</h1>', unsafe_allow_html=True)

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
    # 【ガード3】生成されるHTML全体のhtmlタグに翻訳拒否を設定
    style = f"""
    <style>
        body {{ font-family: 'UD デジタル 教科書体 NK-R', sans-serif; }}
        table {{ width: 100%; border-collapse: collapse; border: 2px solid black; }}
        td {{ border: 2px solid black; padding: {cell_padding}px; font-size: {font_size}pt; line-height: {line_height}; background-color: white; }}
        ruby {{ ruby-align: center; }}
        rt {{ font-size: {ruby_size}pt; color: #000; }}
    </style>
    """
    html_header = f'<html lang="ja" class="notranslate" translate="no"><head><meta charset="utf-8">{style}</head><body><table border="1">'
    
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
    components.html(st.session_state['table_content'], height=400, scrolling=True)
    
    st.markdown("---")
    st.markdown("### 📄 Word形式で保存・利用する")
    
    # Noteへの誘導
    st.success(f"""
    **🔑 パスワードと使い方の確認** Wordに表を貼り付ける方法や、必要なパスワードについては  
    こちらの **[👉 Note解説記事（パスワード案内）](https://note.com/cool_toad2065/n/n2dd510cc185a)** をご確認ください。
    """)
    
    password = st.text_input("利用パスワードを入力してください", type="password")
    SECRET_PASS = st.secrets.get("PASSWORD", "test")

    if password == SECRET_PASS:
        st.success("認証に成功しました。")
        st.download_button(
            label="📄 表形式のWordファイルをダウンロード",
            data=st.session_state['table_content'],
            file_name="ruby_table_final.doc",
            mime="application/msword"
        )
    elif password:
        st.error("パスワードが正しくありません。Note記事内のパスワードをご確認ください。")


st.markdown(f"""
    <style>
        .footer-links {{
            text-align: center;
            margin-top: 50px;
            padding-top: 20px;
            border-top: 1px solid #d7ccc8;
            font-size: 0.9rem;
            font-family: sans-serif;
        }}
        /* 全てのリンクを強制的に「青色」にし、下線を引く */
        .footer-links a {{
            color: #0000ee !important; /* 標準的なリンクの青 */
            text-decoration: underline !important;
            margin: 0 10px;
            font-weight: bold;
        }}
        .footer-links a:hover {{
            color: #ff4500 !important; /* ホバー時はオレンジに */
        }}
    </style>
    <div class="footer-links">
        <a href="https://m-lab-apps.com/privacy.html" target="_blank" rel="noopener noreferrer">プライバシーポリシー</a> | 
        <a href="https://docs.google.com/forms/d/e/1FAIpQLSdX6jh-6_EPE6UTPnoWgKQtzpDgxNK5wOM1fGVxdvf2APLW9g/viewform?usp=header" target="_blank">お問い合わせ</a>
        <p style="margin-top:10px; color: #a1887f; text-decoration: none;">© 2026 M-Lab Apps</p>
    </div>
""", unsafe_allow_html=True)