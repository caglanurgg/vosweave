import re

def make_accent_free_pattern(word):
    accent_map = {
        'a': '[aàáâãäå]',
        'e': '[eéèêë]',
        'i': '[iíìîï]',
        'o': '[oóòôö]',
        'u': '[uúùûü]',
        'c': '[cç]',
        's': '[sß]'
    }
    pattern_str = ""
    for char in word.lower():
        pattern_str += accent_map.get(char, re.escape(char))
    return pattern_str

def highlight_text(text, heatmap_vocab):
    if not heatmap_vocab or not text:
        return text

    sorted_words = sorted(heatmap_vocab.keys(), key=len, reverse=True)

    for word in sorted_words:
        val = heatmap_vocab[word]
        # Sözlük içi status değerini al
        if isinstance(val, dict):
            status = val.get("status", "")
        else:
            status = str(val)

        if "I know this" in status:
            class_name = "highlight-green"
        elif "I've seen this" in status:
            class_name = "highlight-yellow"
        elif "New to me" in status:
            class_name = "highlight-red"
        else:
            continue

        clean_word = word.strip()
        if not clean_word:
            continue

        # Korece karakter kontrolü
        if re.search(r'[\uac00-\ud7a3]', clean_word):
            pattern = re.compile(re.escape(clean_word), re.IGNORECASE)
        else:
            pattern_str = make_accent_free_pattern(clean_word)
            # Kelime ve olası ekleri yakala
            pattern = re.compile(rf'\b({pattern_str}(?:s|es|ed|ing|en|er)?)\b', re.IGNORECASE)

        def replace_match(m):
            return f'<span class="{class_name}">{m.group(0)}</span>'

        # Sadece HTML dışındaki metinleri boya
        parts = re.split(r'(<[^>]+>)', text)
        for i in range(len(parts)):
            if not parts[i].startswith('<'):
                parts[i] = pattern.sub(replace_match, parts[i])
        text = ''.join(parts)

    return text