import streamlit as st
import alkana
import jaconv
import streamlit.components.v1 as components

# ページ設定
st.set_page_config(
    page_title="英語ルビ振りプリント作成ツール",
    page_icon="📚",
    layout="centered"
)

# ---------------------------------------------------------
# Google翻訳による誤変換を防ぐための設定（ここを追加！）
# ---------------------------------------------------------
components.html("""
    <script>
        // ブラウザに「このページは日本語だよ」と伝える
        document.documentElement.setAttribute('lang', 'ja');
    </script>
    <meta name="google" content="notranslate">
""", height=0)

# ---------------------------------------------------------
# デザイン調整（ベージュ基調）
# ---------------------------------------------------------
st.markdown("""
    <style>
    /* 1. 翻訳ポップアップや余計なメニューを消す */
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* 2. 背景色を「ベージュ（生成り色）」に */
    .stApp {
        background-color: #f9f4e6;
        color: #5d4037;
    }
    
    /* 3. サイドバーを少し濃いベージュに */
    [data-testid="stSidebar"] {
        background-color: #f0e6d2;
    }
    
    /* 4. ボタンを「革製品」のようなブラウンに */
    .stButton>button {
        background-color: #8d6e63;
        color: white;
        border-radius: 5px;
        font-weight: bold;
        padding: 0.5rem 2rem;
        width: 100%;
        border: none;
    }
    .stButton>button:hover {
        background-color: #6d4c41;
        color: white;
    }

    /* 5. タイトル文字 */
    h1 {
        font-family: "Yu Mincho", "Hiragino Mincho ProN", serif;
        color: #5d4037;
        text-align: center;
    }
    
    /* インフォメーションボックスの色味調整 */
    .stAlert {
        background-color: #fff8e1;
        color: #5d4037;
    }
    </style>
    """, unsafe_allow_html=True)

# セッション状態の初期化
if 'html_content' not in st.session_state:
    st.session_state['html_content'] = ""
if 'converted' not in st.session_state:
    st.session_state['converted'] = False

# ---------------------------------------------------------
# サイドバー
# ---------------------------------------------------------
st.sidebar.title("📚 メニュー")
st.sidebar.markdown("### 👨‍🏫 このツールについて")
st.sidebar.info("""
**英語ルビ振りプリント作成ツール**
学校の先生や、お子様の英語学習をサポートする保護者の方に向けて開発しました。

教科書や自作の英文に、読みやすいフリガナ（ルビ）を自動で振ることができます。
""")
st.sidebar.caption("Ver 1.9 (No Translate)")

# ---------------------------------------------------------
# メインアプリ
# ---------------------------------------------------------
# タイトルに translate="no" クラスを付けて念押しで翻訳ガード
st.markdown('<h1 class="notranslate">📚 英語ルビ振りプリント作成ツール</h1>', unsafe_allow_html=True)

# 使い方
st.info("""
**💡 使い方**
1. 下のボックスに英文を入力して**「ルビ付きテキストを作成する」**を押します。
2. プレビューを確認します。
3. パスワードを入れて**Enterキー**を押し、**Wordファイル**として保存します。
""")

# 1. 英文入力エリア
text_input = st.text_area(
    "▼ ここに英文を入力してください", 
    height=150, 
    value="My name is Ken. I like Sushi and Tempura in Tokyo.",
    placeholder="教科書の本文や、自作の例文を入力してください。"
)

# 2. 作成ボタン
if st.button("ルビ付きテキストを作成する"):
    if text_input:
        words = text_input.split()
        
        # Word用HTML生成
        html = """
        <html xmlns:o='urn:schemas-microsoft-com:office:office' 
              xmlns:w='urn:schemas-microsoft-com:office:word' 
              xmlns='http://www.w3.org/TR/REC-html40'
              lang="ja" class="notranslate" translate="no">
        <head>
            <meta charset='utf-8'>
            <title>Ruby Print</title>
            <style>
                body {
                    font-family: 'UD デジタル 教科書体 NK-R', 'UD Digi Kyokashotai NK-R', 'Century', serif;
                    font-size: 16pt;
                    color: #000000;
                    line-height: 2.0;
                }
                ruby { ruby-align: center; }
                rt {
                    color: #000000;
                    font-family: 'UD デジタル 教科書体 NK-R', 'UD Digi Kyokashotai NK-R', serif;
                    font-size: 9pt;
                }
            </style>
        </head>
        <body>
        <div class=WordSection1><p class=MsoNormal>
        """
        
        custom_dict = {
            "i": "アイ", "my": "マイ", "ken": "ケン",
            "tokyo": "トウキョウ", "osaka": "オオサカ", "youtube": "ユーチューブ"
        }

        for word in words:
            clean_word = word.strip(".,!?\"")
            lower_word = clean_word.lower()
            kana = ""

            if lower_word in custom_dict:
                kana = custom_dict[lower_word]
            else:
                kana = alkana.get_kana(lower_word)
                if kana is None:
                    potential_kana = jaconv.alphabet2kana(lower_word)
                    if potential_kana != lower_word:
                        kana = potential_kana
                    else:
                        kana = ""

            ruby_tag = f"""<ruby class="notranslate" translate="no"><rb>{clean_word}</rb><rt>{kana}</rt></ruby><span> </span>"""
            html += ruby_tag

        html += "</p></div></body></html>"
        
        # 結果を保存
        st.session_state['html_content'] = html
        st.session_state['converted'] = True
    else:
        st.warning("まずは英文を入力してください。")

# 3. 結果表示エリア
if st.session_state['converted']:
    st.markdown("---")
    st.subheader("プレビュー")
    
    st.components.v1.html(st.session_state['html_content'], height=200, scrolling=True)
    
    st.markdown("---")
    st.subheader("Word形式で保存")
    
    password = st.text_input("利用パスワードを入力（入力後にEnterキーを押してください）", type="password")
    SECRET_PASS = "ruby2026-march"

    if password == SECRET_PASS:
        st.success("認証されました。")
        st.download_button(
            label="📄 Wordファイルをダウンロード",
            data=st.session_state['html_content'],
            file_name="textbook_print.doc",
            mime="application/msword"
        )
    elif password:
        st.error("パスワードが違います。")
        
    st.caption(f"※Word出力機能のご利用にはパスワードが必要です。[詳細はこちら（Note）](https://note.com/cool_toad2065/n/n2dd510cc185a?app_launch=false)")