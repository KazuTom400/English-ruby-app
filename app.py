import streamlit as st
import alkana
import jaconv
import streamlit.components.v1 as components
import re

# 1. ページ設定とスタイル
st.set_page_config(
    page_title="英語ルビ振り文章作成ツール",
    page_icon="📚",
    layout="centered"
)

# スタイル設定（変更なし）
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

if 'html_content' not in st.session_state: st.session_state['html_content'] = ""
if 'converted' not in st.session_state: st.session_state['converted'] = False

# 2. 強化されたルビ振りロジック
def get_kana_smart(word, custom_dict):
    lower_word = word.lower()
    
    # a) カスタム辞書（最優先）
    if lower_word in custom_dict:
        return custom_dict[lower_word]
    
    # b) alkana で直接ヒット
    kana = alkana.get_kana(lower_word)
    if kana: return kana
    
    # c) 語尾変化への対応 (死角1, 2対応)
    # 進行形 -ing
    if lower_word.endswith("ing") and len(lower_word) > 5:
        stem = lower_word[:-3]
        # eを取る(making) or 重複末尾(running) への簡易対応
        for s in [stem, stem + "e", stem[:-1]]:
            res = alkana.get_kana(s)
            if res: return res + "イング"
            
    # 過去形 -ed
    if lower_word.endswith("ed") and len(lower_word) > 3:
        stem = lower_word[:-2] if lower_word.endswith("ed") else lower_word[:-1]
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
            
    # e) 複数形 (既存ロジックを流用)
    if lower_word.endswith("s") and len(lower_word) > 2:
        singular = lower_word[:-1]
        stem = custom_dict.get(singular) or alkana.get_kana(singular)
        if stem:
            suffix = "ツ" if singular.endswith("t") else "ス" if singular.endswith(("k", "p", "f")) else "ズ"
            return stem + suffix
            
    return None

# 3. メインUI
st.markdown('<h1 class="notranslate" translate="no">📚 英語ルビ振り文章作成ツール</h1>', unsafe_allow_html=True)

text_input = st.text_area("▼ 英文を入力（日本語混じり、iPhone15などもOK！）", height=150, 
                         value="A cat is running. 私は iPhone15 を使って YouTube を見ています。")

st.subheader("📏 レイアウト微調整")
col1, col2 = st.columns(2)
with col1:
    font_size = st.slider("本文の大きさ (pt)", 10, 40, 18)
    ruby_size = st.slider("ルビの大きさ (pt)", 5, 20, 9)
with col2:
    line_height = st.slider("行の間隔（高さ）", 1.0, 4.0, 2.5, 0.1)

# 4. 変換実行
if st.button("ルビ付きテキストを作成する"):
    if text_input:
        custom_dict = {
            "a": "ア", "an": "アン", "the": "ザ", "i": "アイ", "my": "マイ", "me": "ミー", 
            "'s": "ズ", "'t": "ト", "n't": "ト", "'m": "ム", "'re": "アー", 
            "don't": "ドーント", "doesn't": "ダズント", "can't": "キャント", "youtube": "ユーチューブ"
        }

        style = f"<style>body {{ font-family: 'UD デジタル 教科書体 NK-R', sans-serif; font-size: {font_size}pt; line-height: {line_height}; background-color: transparent; }} ruby {{ ruby-align: center; }} rt {{ font-size: {ruby_size}pt; }}</style>"
        
        html_body = ""
        lines = text_input.split('\n')
        for line in lines:
            # 【死角4, 5への対策】
            # re.findall ではなく re.split を使い、英数字+記号の塊を「抽出」しつつ、それ以外（日本語やスペース）を「保持」する
            tokens = re.split(r"([a-zA-Z0-9'-]+)", line)
            
            for token in tokens:
                if not token: continue
                
                # 英単語・数字・ハイフンを含む塊の場合のみルビ判定
                if re.match(r"[a-zA-Z0-9'-]+", token):
                    kana = get_kana_smart(token, custom_dict)
                    if kana:
                        z_kana = jaconv.h2z(kana)
                        html_body += f'<ruby><rb>{token}</rb><rt>{z_kana}</rt></ruby>'
                    else:
                        html_body += f"<span>{token}</span>"
                else:
                    # 日本語、スペース、記号などはそのまま出力
                    html_body += f"<span>{token}</span>"
            html_body += "<br>"

        st.session_state['html_content'] = f'<html lang="ja" class="notranslate" translate="no"><head><meta charset="utf-8">{style}</head><body>{html_body}</body></html>'
        st.session_state['converted'] = True

# 5. 表示とダウンロード
if st.session_state['converted']:
    st.markdown("---")
    st.subheader("👀 プレビュー")
    components.html(st.session_state['html_content'], height=400, scrolling=True)
    
    st.markdown("---")
    st.subheader("💾 Word形式で保存")
    bom_html = "\ufeff" + st.session_state['html_content']
    st.download_button(label="📄 Word形式（HTML）をダウンロード", data=bom_html, file_name="ruby_text.doc", mime="text/html")
