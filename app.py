import streamlit as st
import alkana
import jaconv
import streamlit.components.v1 as components
import re

# ページ設定（ブラウザのタブ名も変更）
st.set_page_config(
    page_title="英語ルビ振り文章作成ツール",
    page_icon="📚",
    layout="centered"
)

# ---------------------------------------------------------
# Google翻訳による誤変換を防ぐための設定
# ---------------------------------------------------------
components.html("""
    <script>
        document.documentElement.setAttribute('lang', 'ja');
    </script>
    <meta name="google" content="notranslate">
""", height=0)

# ---------------------------------------------------------
# デザイン調整
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

    /* 5. タイトル文字（自然な改行に任せる設定） */
    h1 {
        font-family: "Yu Mincho", "Hiragino Mincho ProN", serif;
        color: #5d4037;
        text-align: center;
        font-size: 1.8rem !important;  /* 標準サイズ */
        line-height: 1.4 !important;   /* 行間を少し空ける */
        white-space: normal !important; /* 画面幅に合わせて自然に改行 */
        word-break: keep-all;          /* 単語の途中では改行しない（日本語用） */
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
# 関数：賢いルビ振りロジック（厳格モード・アポストロフィ対応）
# ---------------------------------------------------------
def get_kana_smart(word, custom_dict):
    lower_word = word.lower()
    
    # 0. カスタム辞書にあるか確認（最優先）
    if lower_word in custom_dict:
        return custom_dict[lower_word]

    # 1. 辞書検索
    kana = alkana.get_kana(lower_word)
    if kana:
        return kana

    # 2. 語尾が "s" の場合（複数形対応）
    if lower_word.endswith("s") and len(lower_word) > 1:
        singular = lower_word[:-1]
        
        # 単数形が辞書にあるかチェック
        stem_kana = None
        if singular in custom_dict:
            stem_kana = custom_dict[singular]
        else:
            stem_kana = alkana.get_kana(singular)
            
        if stem_kana:
            if singular.endswith("t"):
                return stem_kana + "ツ" # cat -> キャッツ
            elif singular.endswith(("k", "p", "f")):
                return stem_kana + "ス" # book -> ブックス
            else:
                return stem_kana + "ズ" # dog -> ドッグズ

    # 3. "es" の場合
    if lower_word.endswith("es") and len(lower_word) > 2:
        singular = lower_word[:-2]
        
        # 単数形が辞書にあるかチェック
        stem_kana = None
        if singular in custom_dict:
            stem_kana = custom_dict[singular]
        else:
            stem_kana = alkana.get_kana(singular)

        if stem_kana:
            return stem_kana + "イズ" 

    return None

# ---------------------------------------------------------
# サイドバー
# ---------------------------------------------------------
st.sidebar.title("📚 メニュー")
st.sidebar.markdown("### 👨‍🏫 このツールについて")
st.sidebar.info("""
**英語ルビ振り文章作成ツール**
学校の先生や、お子様の英語学習をサポートする保護者の方に向けて開発しました。

教科書や自作の英文に、読みやすいフリガナ（ルビ）を自動で振ることができます。
""")
st.sidebar.caption("Ver 3.0 (Renamed)")

# ---------------------------------------------------------
# メインアプリ
# ---------------------------------------------------------
# ★★★ タイトルを変更しました（改行タグなし） ★★★
st.markdown('<h1 class="notranslate">📚 英語ルビ振り文章作成ツール</h1>', unsafe_allow_html=True)

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
    value="She's my best friend. Tom's cat is cute. I can't swim.",
    placeholder="教科書の本文や、自作の例文を入力してください。"
)

# 2. 作成ボタン
if st.button("ルビ付きテキストを作成する"):
    if text_input:
        # アポストロフィ(')も区切り文字として扱い、's や 't を分離する
        tokens = re.findall(r"[\w]+|['][\w]+|[.,!?;:\"()\-]", text_input)
        
        # Word用HTML生成（ヘッダー部分）
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
        
        # ★★★ カスタム辞書 ★★★
        custom_dict = {
            # 基本単語
            "i": "アイ", "my": "マイ", "ken": "ケン",
            "tokyo": "トウキョウ", "osaka": "オオサカ", "youtube": "ユーチューブ",
            
            # デジタル用語
            "smartphone": "スマートフォン",
            "iphone": "アイフォン",
            "ipad": "アイパッド",
            "tablet": "タブレット",
            "internet": "インターネット",
            "computer": "コンピュータ",
            "video": "ビデオ",
            
            # 短縮形用辞書
            "'s": "ズ",   # She's -> シーズ
            "'t": "ト",   # can't -> キャント
            "'m": "ム",   # I'm -> アイム
            "'re": "アー", # You're -> ユーアー
            "'ve": "ブ",   # I've -> アイブ
            "'ll": "ル",   # I'll -> アイル
            "'d": "ド"    # I'd -> アイド
        }

        # トークンごとに処理
        for word in tokens:
            # 記号や数字はそのまま表示
            if re.match(r"[^a-zA-Z']", word): 
                html += f"<span>{word} </span>" 
                continue
            
            # クリーンアップ（念のため）
            clean_word = word.strip(".,!?\"")
            
            # 賢いルビ取得関数を呼び出す
            kana = get_kana_smart(clean_word, custom_dict)

            if kana:
                # 半角カナを全角に変換
                kana = jaconv.h2z(kana)
                
                # スペース処理
                ruby_tag = f"""<ruby class="notranslate" translate="no"><rb>{clean_word}</rb><rt>{kana}</rt></ruby><span> </span>"""
                html += ruby_tag
            else:
                html += f"<span>{clean_word} </span>"

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
    # ↓ 金庫（Secrets）から "PASSWORD" を取ってくる命令
    SECRET_PASS = st.secrets["PASSWORD"]

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