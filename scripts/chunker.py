"""
长文本智能分段器。
超过阈值时，把文本切成多段，每段独立生成投喂包；
最终再生成一个"汇总投喂包"，用于多段笔记的归并。

策略：
  - 按字符数硬切（默认 12000 字符/段，含一定 overlap）
  - 尽量在句子边界（中文：。！？；英文：. ! ?）切
  - 段间重叠 200 字符，保证上下文连贯
"""
import re
from dataclasses import dataclass, field


@dataclass
class Chunk:
    idx: int           # 第几段（从 1 开始）
    total: int         # 共多少段
    text: str          # 段内容
    start_char: int    # 在原文中的起始字符位置
    end_char: int      # 结束位置
    overlap_with_prev: int = 0


DEFAULT_CHUNK_SIZE = 12000
DEFAULT_OVERLAP = 200
SENTENCE_ENDINGS = re.compile(r"[。！？!?\.](?:\s|$)")


def find_split_point(text: str, target: int, search_window: int = 500) -> int:
    """
    在 target 附近找一个句子结束点，避免切在句中。
    """
    lo = max(0, target - search_window)
    hi = min(len(text), target + search_window)
    region = text[lo:hi]
    matches = list(SENTENCE_ENDINGS.finditer(region))
    if not matches:
        return target
    # 找离 target 最近的句子结束
    best = min(matches, key=lambda m: abs((lo + m.end()) - target))
    return lo + best.end()


def chunk_text(text: str,
               chunk_size: int = DEFAULT_CHUNK_SIZE,
               overlap: int = DEFAULT_OVERLAP) -> list[Chunk]:
    """
    把长文本切成多段。返回 Chunk 列表。
    """
    if len(text) <= chunk_size:
        return [Chunk(idx=1, total=1, text=text, start_char=0, end_char=len(text))]

    chunks: list[Chunk] = []
    cursor = 0
    while cursor < len(text):
        target_end = cursor + chunk_size
        if target_end >= len(text):
            chunks.append(Chunk(
                idx=len(chunks) + 1, total=-1,  # total 稍后填
                text=text[cursor:].strip(),
                start_char=cursor,
                end_char=len(text),
                overlap_with_prev=overlap if chunks else 0,
            ))
            break
        end = find_split_point(text, target_end)
        chunks.append(Chunk(
            idx=len(chunks) + 1, total=-1,
            text=text[cursor:end].strip(),
            start_char=cursor,
            end_char=end,
            overlap_with_prev=overlap if chunks else 0,
        ))
        cursor = max(end - overlap, cursor + 1)

    total = len(chunks)
    for c in chunks:
        c.total = total
    return chunks


def need_chunking(text: str, threshold: int = DEFAULT_CHUNK_SIZE) -> bool:
    return len(text) > threshold


if __name__ == "__main__":
    sample = ("这是第一句话。这是第二句话。" * 1500)
    print(f"原文长度：{len(sample)}")
    chunks = chunk_text(sample, chunk_size=5000, overlap=200)
    print(f"切成 {len(chunks)} 段：")
    for c in chunks:
        print(f"  段 {c.idx}/{c.total}：{len(c.text)} 字符 "
              f"({c.start_char}-{c.end_char})")
