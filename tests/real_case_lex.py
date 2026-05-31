"""
真实用例 Plan B：用一段真实公开的英文播客字幕，跑投喂包生成。
模拟 Lex Fridman / Latent Space 类节目的开场访谈片段。
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from build_prompt import save_bundle
from detect_language import detect_language


def main():
    # 模拟真实英文 AI 播客片段（仿照 Lex Fridman / Latent Space 访谈风格）
    meta = {
        "title": "Lex Fridman Podcast - On the Future of AI Agents (excerpt)",
        "uploader": "Lex Fridman",
        "duration_sec": 1200,
        "upload_date": "20260520",
        "url": "https://www.youtube.com/watch?v=example",
    }

    subtitle_text = """Welcome to the Lex Fridman Podcast. Today I'm joined by a leading
researcher in AI agents. We're going to talk about what makes agents different from
chatbots, where the field is heading, and what it means for the future of work.

Let me start with a simple question: what is an AI agent, and how is it different
from the large language models we've been using?

That's a great place to begin. A chatbot is essentially a function. You give it
input, it gives you output. An agent, by contrast, has goals, can plan multiple
steps ahead, can use tools, can observe the world, and can recover from failures.
The chatbot is reactive. The agent is proactive.

So the agent has agency in the philosophical sense?

Yes, but with important caveats. Today's agents have what I'd call bounded agency.
They operate within a sandbox of tools and instructions. True agency in the human
sense involves judgment about values, preferences, long-term consequences. We're
not there yet, and we may not want to get there too quickly.

What are the biggest unsolved problems in building reliable agents?

There are three. First, memory. Most agents have a very short attention span. They
forget what happened five minutes ago. Second, evaluation. We don't have good ways
to measure whether an agent is doing a good job, especially over long horizons.
Third, alignment under autonomy. The more independent an agent is, the harder it
is to ensure it stays aligned with what you actually want.

Let's dig into memory. Why is it so hard?

The transformer architecture has a fixed context window. Beyond that window, the
model has no memory. There are workarounds - retrieval-augmented generation,
vector databases, summarization techniques. But none of these give the agent a
true persistent self. It's like talking to someone with severe amnesia who has
read your file before the conversation.

What about evaluation? You said we don't have good benchmarks.

The benchmarks we have are static. Pass at one, function call accuracy, math
problems. Real agents need to be evaluated on dynamic tasks: did the agent succeed
at the overall goal? Did it handle unexpected situations? Did it know when to ask
for help? These are hard to measure automatically. You often need humans in the
loop, which doesn't scale.

The third problem you mentioned was alignment under autonomy. Can you elaborate?

When you give a chatbot one instruction, you can check the output before acting on
it. When you give an agent a goal, it might take hundreds of actions to achieve it.
You can't review every action. So you need the agent to have internalized the right
values, the right constraints. This is much harder than just having a good model.

What gives you hope about the field?

The pace of progress. Five years ago, we couldn't have a coherent conversation with
an AI. Today, we have agents writing code, doing research, managing schedules. The
distance covered is enormous. I think the next five years will bring agents that
collaborate with humans in much more sophisticated ways. We'll work alongside them
the way we work alongside expert colleagues today.

What should young researchers entering this field focus on?

Three things. Read the foundational papers, even the old ones. Build something
that runs end to end, however small. And find a real human user who needs your
agent to work. The combination of theory, practice, and real-world feedback is
what produces good researchers.

Thank you for this conversation. It's been illuminating.

My pleasure. Always good to think out loud about these questions.
"""

    print("=" * 60)
    print("🎬 真实用例：Lex Fridman 风格 AI 访谈片段")
    print("=" * 60)

    lang = detect_language(subtitle_text)
    print(f"\n🌐 语言检测：{lang}")
    print(f"📊 字幕长度：{len(subtitle_text)} 字符")

    out_dir = ROOT / "output" / "bundles"
    prompt_path, ctx_path = save_bundle(meta, subtitle_text, lang, "manual-real-case", out_dir)

    print(f"\n📦 投喂包生成完成：")
    print(f"   {prompt_path}")
    print(f"\n✅ 现在可以把这份投喂包丢给 AI 拿结构化笔记了。")


if __name__ == "__main__":
    main()
