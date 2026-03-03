import streamlit as st
import alkana
import jaconv
import streamlit.components.v1 as components
import re

# 1. ページ設定（変更なし）
st.set_page_config(page_title="英語ルビ振りツール", page_icon="📚", layout="centered")

st.markdown("""
    <style>
    #MainMenu, header, footer, .stDeployButton {visibility: hidden;}
    html, body, [class*="css"], .stMarkdown, .stButton, .stTextArea {
        font-family: "UD デジタル 教科書体 NK-R", sans-serif !important;
    }
    .stApp { background-color: #f9f4e6; color: #5d4037; }
    .stButton>button { background-color: #8d6e63; color: white; border-radius: 5px; font-weight: bold; width: 100%; }
    h1 { color: #5d4037; text-align: center; font-size: 1.8rem !important; }
    </style>
""", unsafe_allow_html=True)

if 'html_content' not in st.session_state: st.session_state['html_content'] = ""
if 'converted' not in st.session_state: st.session_state['converted'] = False

# 2. 英語特化型・賢いルビ振りロジック
def get_kana_smart(word, custom_dict):
    lower_word = word.lower()
    
    # a) カスタム辞書（最優先）
    if lower_word in custom_dict:
        return custom_dict[lower_word]
    
    # b) alkana で直接ヒット
    kana = alkana.get_kana(lower_word)
    if kana: return kana
    
    # c) 語形変化の吸収 (死角1: -ing, -ed)
    # 現在進行形
    if lower_word.endswith("ing") and len(lower_word) > 5:
        stem = lower_word[:-3]
        # running -> run, making -> make, playing -> play の各パターンを試行
        for s in [stem, stem + "e", stem[:-1]]:
            res = alkana.get_kana(s)
            if res: return res + "イング"
            
    # 過去形・過去分詞
    if lower_word.endswith("ed") and len(lower_word) > 3:
        stem = lower_word[:-2]
        # played -> play, stopped -> stop, baked -> bake の各パターン
        for s in [stem, stem + "e", stem[:-1]]:
            res = alkana.get_kana(s)
            if res: return res + "ド"

    # d) アポストロフィ分解 (she's -> she + 's)
    if "'" in lower_word:
        parts = lower_word.split("'")
        prefix = parts[0]
        suffix = "'" + parts[1]
        p_kana = custom_dict.get(prefix) or alkana.get_kana(prefix)
        s_kana = custom_dict.get(suffix)
        if p_kana and s_kana: return p_kana + s_kana

    # e) 複数形・三単現 (watches, boxes などの -es にも簡易対応)
    if lower_word.endswith("s") and len(lower_word) > 2:
        singular = lower_word[:-2] if lower_word.endswith("es") else lower_word[:-1]
        stem = custom_dict.get(singular) or alkana.get_kana(singular)
        if stem:
            # 語尾に応じた発音の使い分け
            suffix = "ツ" if singular.endswith("t") else "ス" if singular.endswith(("k", "p", "f")) else "ズ"
            return stem + suffix
            
    return None

# 3. メインUI
st.markdown('<h1>📚 英語ルビ振り文章作成ツール</h1>', unsafe_allow_html=True)

text_input = st.text_area("▼ 英文を入力（iPhone15 や running もOK！）", height=150, 
                         value="The cat is running. iPhone15 is semi-conductor based. It's amazing!")

col1, col2 = st.columns(2)
with col1:
    font_size = st.slider("本文サイズ", 10, 40, 18)
    ruby_size = st.slider("ルビサイズ", 5, 20, 9)
with col2:
    line_height = st.slider("行間", 1.0, 4.0, 2.5, 0.1)

# 4. 変換実行
if st.button("ルビ付きテキストを作成する"):
    if text_input:
        # 基本語の辞書
        custom_dict = {
            "a": "ア", "an": "アン", "the": "ザ", "i": "アイ", "my": "マイ", "me": "ミー", 
            "'s": "ズ", "'t": "ト", "n't": "ト", "'m": "ム", "'re": "アー", "is": "イズ",
            "don't": "ドーント", "doesn't": "ダズント", "can't": "キャント"
        }

        style = f"<style>body {{ font-family: 'UD デジタル 教科書体 NK-R', sans-serif; font-size: {font_size}pt; line-height: {line_height}; background-color: transparent; }} ruby {{ ruby-align: center; }} rt {{ font-size: {ruby_size}pt; }}</style>"
        
        html_body = ""
        lines = text_input.split('\n')
        for line in lines:
            # 【死角4, 6への対策】
            # 英数字、ハイフン、アポストロフィを含む塊を一つの単語として抽出
            # それ以外（スペースや記号）を保持するために re.split を使用
            tokens = re.split(r"([a-zA-Z0-9'-]+)", line)
            
            for token in tokens:
                if not token: continue
                
                # 単語の塊（英数字含む）であればルビ判定へ
                if re.match(r"[a-zA-Z0-9'-]+", token):
                    kana = get_kana_smart(token, custom_dict)
                    if kana:
                        z_kana = jaconv.h2z(kana)
                        html_body += f'<ruby><rb>{token}</rb><rt>{z_kana}</rt></ruby>'
                    else:
                        html_body += f"<span>{token}</span>"
                else:
                    # スペースや記号はそのまま出力
                    html_body += f"<span>{token}</span>"
            html_body += "<br>"

        st.session_state['html_content'] = f'<html lang="en"><head><meta charset="utf-8">{style}</head><body>{html_body}</body></html>'
        st.session_state['converted'] = True

# 5. 表示とダウンロード（変更なし）
if st.session_state['converted']:
    st.markdown("---")
    components.html(st.session_state['html_content'], height=400, scrolling=True)
    st.download_button(label="📄 Word形式で保存", data="\ufeff" + st.session_state['html_content'], file_name="ruby_text.doc", mime="text/html")
