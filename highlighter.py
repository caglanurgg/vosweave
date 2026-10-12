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

def _build_variant_regex(clean_word):
    """
    Kök kelime sonundaki 'e' düşmelerini (capture -> capturing, captured)
    ve yaygın çekim/yapım eklerini esnek yakalayan regex deseni üretir.
    """
    clean_lower = clean_word.lower()
    
    # Kelime 'e' ile bitiyorsa: 'e' harfini opsiyonel yapıp ekleri bağla
    # capture -> captur(?:e(?:s|d|r)?|ing)?
    if clean_lower.endswith('e') and len(clean_lower) > 2:
        stem = clean_word[:-1]
        stem_pattern = make_accent_free_pattern(stem)
        return rf'{stem_pattern}(?:e(?:s|d|r)?|ing|ed)?'
    
    # Kelime sessiz harfle bitiyorsa (run -> running gibi çift sessiz veya standart ekler)
    stem_pattern = make_accent_free_pattern(clean_word)
    return rf'{stem_pattern}(?:s|es|ed|ing|en|er)?'

def highlight_text(text, heatmap_vocab):
    if not heatmap_vocab or not text:
        return text

    sorted_words = sorted(heatmap_vocab.keys(), key=len, reverse=True)

    for word in sorted_words:
        val = heatmap_vocab[word]
        variants = []
        
        # Sözlük içi status ve varsa modelden gelen varyantları al
        if isinstance(val, dict):
            status = val.get("status", "")
            # Modelin ürettiği detected_variants listesi varsa çek
            raw_variants = val.get("detected_variants", [])
            if isinstance(raw_variants, list):
                for v in raw_variants:
                    if isinstance(v, dict) and "word" in v:
                        variants.append(v["word"].strip())
                    elif isinstance(v, str):
                        variants.append(v.strip())
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
            # 1. Kök kelime için esnek son-ek deseni
            patterns = [_build_variant_regex(clean_word)]
            
            # 2. Varsa tespit edilen ek varyantları da regex desenine ekle
            for var in variants:
                if var:
                    patterns.append(_build_variant_regex(var))
            
            combined_pattern = "|".join(patterns)
            pattern = re.compile(rf'\b({combined_pattern})\b', re.IGNORECASE)

        def replace_match(m):
            return f'<span class="{class_name}">{m.group(0)}</span>'

        # Sadece HTML dışındaki metinleri boya
        parts = re.split(r'(<[^>]+>)', text)
        for i in range(len(parts)):
            if not parts[i].startswith('<'):
                parts[i] = pattern.sub(replace_match, parts[i])
        text = ''.join(parts)

    return text