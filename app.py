def get_kana_smart(word, custom_dict):
    lower_word = word.lower()
    
    # 1. 辞書（カスタム・alkana）を直接チェック
    if lower_word in custom_dict: return custom_dict[lower_word]
    res = alkana.get_kana(lower_word)
    if res: return res

    # 2. 接頭辞の処理 (dis-, un-, re- など)
    # 単語の頭を切り取って、残りの部分が辞書にあるか確認する
    prefixes = {
        "dis": "ディス", "un": "アン", "re": "リ", "pre": "プリ", "non": "ノン", 
        "anti": "アンチ", "mis": "ミス", "multi": "マルチ", "inter": "インター", "sub": "サブ"
    }
    for p, p_kana in prefixes.items():
        if lower_word.startswith(p) and len(lower_word) > len(p) + 2:
            stem = lower_word[len(p):]
            stem_kana = alkana.get_kana(stem) or custom_dict.get(stem)
            if stem_kana:
                return p_kana + stem_kana

    # 3. 複合語の分割 (evergreen, background, underground など)
    # 単語を2つに割って、両方が辞書にある組み合わせを探す
    if len(lower_word) >= 6:
        for i in range(3, len(lower_word) - 2):
            part1 = lower_word[:i]
            part2 = lower_word[i:]
            k1 = alkana.get_kana(part1) or custom_dict.get(part1)
            k2 = alkana.get_kana(part2) or custom_dict.get(part2)
            if k1 and k2:
                return k1 + k2

    # 4. 既存の活用形ロジック (進行形、過去形、複数形)
    # -ing
    if lower_word.endswith("ing") and len(lower_word) > 5:
        stem = lower_word[:-3]
        for s in [stem, stem + "e", stem[:-1]]:
            res = alkana.get_kana(s)
            if res: return res + "イング"
            
    # -ed
    if lower_word.endswith("ed") and len(lower_word) > 3:
        stem = lower_word[:-2]
        for s in [stem, stem + "e", stem[:-1]]:
            res = alkana.get_kana(s)
            if res: return res + "ド"

    # -s / -es
    if lower_word.endswith("s") and len(lower_word) > 2:
        singular = lower_word[:-2] if lower_word.endswith("es") else lower_word[:-1]
        stem_kana = alkana.get_kana(singular) or custom_dict.get(singular)
        if stem_kana:
            suffix = "ツ" if singular.endswith("t") else "ス" if singular.endswith(("k", "p", "f")) else "ズ"
            return stem_kana + suffix
            
    return None
