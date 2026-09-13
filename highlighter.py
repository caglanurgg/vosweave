import re
import unicodedata

def make_accent_free_pattern(word):
    """
    Kelimedeki e, a, i, o, u harflerini aksanlı varyasyonlarını kapsayacak 
    regex gruplarına dönüştürür. (Örn: 'melodi' -> 'm[eéèêë]l[oóòôö]d[iíìîï]')
    """
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
    """
    Fransızca, İspanyolca ve İngilizce gibi dillerdeki aksanları (é, à, ç) 
    ve fiil/isim çekimlerini (captiver -> captivé, melodie -> mélodies) kökten yakalayan 
    evrensel akıllı highlighter motoru.
    """
    if not heatmap_vocab:
        return text

    # İç içe çakışmaları önlemek için uzun kelimeler her zaman öncelikli
    sorted_words = sorted(heatmap_vocab.keys(), key=len, reverse=True)

    for word in sorted_words:
        status = heatmap_vocab[word]
        
        if "I know this" in status:
            class_name = "highlight-green"
        elif "I've seen this" in status:
            class_name = "highlight-yellow"
        elif "New to me" in status:
            class_name = "highlight-red"
        else:
            continue

        # 1. Korean
        if re.search(r'[\uac00-\ud7a3]', word):
            pattern = re.compile(re.escape(word), re.IGNORECASE)
            
        # 2. French, Spanish, English, Nederlands
        else:
            # Fiil ve isim kökünü esnetme (Romance Language Stemmer)
            stem = word
            
            # Fiil son ekleri (-er, -ir, -re, -ar) esnetmesi
            if len(word) > 4 and word.endswith(('er', 'ir', 're', 'ar')):
                stem = word[:-2]
            # İsim/Sıfat sonundaki tekil/çoğul veya dişil ek esnetmesi
            elif len(word) > 4 and word.endswith(('e', 's', 'x')):
                stem = word[:-1]

            # Aksan toleranslı regex deseni oluştur
            flexible_stem = make_accent_free_pattern(stem)

            # [a-zA-Za-zA-ZÀ-ÿ]* deseni aksanlı karakterler ve çekim takılarını kapsar
            pattern = re.compile(r'(?<!\w)' + flexible_stem + r'[\wÀ-ÿ]*(?!\w)', re.IGNORECASE)

        text = pattern.sub(f'<span class="{class_name}">\\g<0></span>', text)

    return text