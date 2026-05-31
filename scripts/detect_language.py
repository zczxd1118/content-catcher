"""检测文本主要语言，决定走哪个模板。"""
import re


def detect_language(text: str, hint: str | None = None) -> str:
    """
    返回 'zh' / 'en' / 'unknown'。
    优先用 hint（字幕 API 给的语言码），其次按字符比例判断。
    """
    if hint:
        h = hint.lower()
        if h.startswith("zh"):
            return "zh"
        if h.startswith("en"):
            return "en"

    # 取前 3000 字符做样本
    sample = text[:3000]
    chinese = len(re.findall(r"[\u4e00-\u9fff]", sample))
    english_words = len(re.findall(r"[a-zA-Z]{2,}", sample))

    # 中文字符占比 > 5% 就当中文
    if chinese > 50 and chinese / max(len(sample), 1) > 0.05:
        return "zh"
    if english_words > 30:
        return "en"
    return "unknown"


if __name__ == "__main__":
    print(detect_language("这是一段中文测试文本，包含足够多的汉字。" * 20))  # zh
    print(detect_language("This is an English test sentence with plenty of words to detect." * 5))  # en
    print(detect_language(""))  # unknown
