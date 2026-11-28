#!/usr/bin/env python3
"""每日生成：从语料库取当天的场景对话，用 edge-tts 逐句合成语音，输出到 site/。

用法:
  python scripts/generate.py            # 生成「今天(JST)」的内容，已存在则跳过
  python scripts/generate.py --force    # 强制重新生成今天
  python scripts/generate.py 2026-07-12 # 生成指定日期（补数据用）

选场景：corpus.json 的 lessons（用上课学过的语法写的场景）优先，每个出一次；
都出过了就按 days 轮换。已学内容清单在 site/learned.json，页面据此高亮。
"""
import asyncio
import json
import re
import sys
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import edge_tts

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"
# 对话按说话人出场顺序轮流分配声音（edge-tts 的 ja-JP 只有这两个声线，第 3 位说话人回绕）
JA_VOICES = ["ja-JP-NanamiNeural", "ja-JP-KeitaNeural"]
EN_VOICES = ["en-US-JennyNeural", "en-US-GuyNeural"]
JST = timezone(timedelta(hours=9))


def target_date() -> date:
    for a in sys.argv[1:]:
        if not a.startswith("-"):
            return date.fromisoformat(a)
    return datetime.now(JST).date()


def validate(day: dict) -> None:
    """手改语料后的保险丝：字段齐全、ruby 去标签后与 ja 一致。"""
    for k in ("title_ja", "title_cn", "desc"):
        assert day["scenario"].get(k), f"scenario 缺字段 {k}"
    for l in day["lines"]:
        for k in ("speaker", "ja", "ruby", "en", "cn"):
            assert l.get(k), f"句子缺字段 {k}: {l.get('ja', l)}"
        plain = re.sub(r"<rt>[^<]*</rt>", "", l["ruby"]).replace("<ruby>", "").replace("</ruby>", "")
        assert plain == l["ja"], f"ruby 与 ja 不一致: {l['ja']!r} vs {plain!r}"


def load_learned() -> list[tuple[str, "re.Pattern[str]"]]:
    """site/learned.json：已学语法/词汇清单（页面用它高亮）。这里只校验正则写得对不对。"""
    f = SITE / "learned.json"
    if not f.exists():
        return []
    items = json.loads(f.read_text(encoding="utf-8"))["items"]
    out = []
    for it in items:
        for k in ("id", "label", "pattern", "note"):
            assert it.get(k), f"learned.json 条目缺字段 {k}: {it}"
        out.append((it["id"], re.compile(it["pattern"])))
    return out


def pick_day(corpus: dict, today: date, data_dir: Path) -> dict:
    """lessons 里还没出过的场景优先（按顺序，每个一次），否则按日期轮换 days。

    「出过」= 今天之前的某天 data 文件用过同名场景；不看今天自己，
    所以 --force 重新生成今天会选回同一个场景。
    """
    lessons = corpus.get("lessons", [])
    if lessons:
        used = set()
        for p in data_dir.glob("????-??-??.json"):
            if p.stem >= today.isoformat():
                continue
            sc = json.loads(p.read_text(encoding="utf-8")).get("scenario")
            if sc:
                used.add(sc.get("title_ja"))
        for d in lessons:
            if d["scenario"]["title_ja"] not in used:
                return d
    start = date.fromisoformat(corpus["start"])
    days = corpus["days"]
    return days[(today - start).days % len(days)]


async def synth(text: str, voice: str, out: Path, retries: int = 3) -> None:
    for i in range(retries):
        try:
            await edge_tts.Communicate(text, voice).save(str(out))
            return
        except Exception:
            if i == retries - 1:
                raise
            await asyncio.sleep(2 * (i + 1))


async def main() -> None:
    corpus = json.loads((ROOT / "corpus" / "corpus.json").read_text(encoding="utf-8"))
    learned = load_learned()
    for d in corpus.get("lessons", []):
        # lessons 是为了练已学内容写的：每句先校验，再确认整段至少用上一个已学点
        validate(d)
        text = "".join(l["ja"] for l in d["lines"])
        if learned:
            assert any(p.search(text) for _, p in learned), \
                f"lessons 场景没用到任何已学内容: {d['scenario']['title_ja']}"

    today = target_date()
    dstr = today.isoformat()

    data_dir = SITE / "data"
    day = pick_day(corpus, today, data_dir)
    audio_dir = SITE / "audio" / dstr
    data_dir.mkdir(parents=True, exist_ok=True)
    out_file = data_dir / f"{dstr}.json"

    if out_file.exists() and "--force" not in sys.argv:
        print(f"skip: {dstr} already generated")
    else:
        validate(day)
        audio_dir.mkdir(parents=True, exist_ok=True)
        # 音频 URL 带生成版本参数：--force 重新生成时 URL 必然变化，
        # 击穿 CDN / 浏览器 / Service Worker(cache-first) 各层缓存，避免新旧文音错配
        gen = int(time.time())
        speakers: list[str] = []
        for l in day["lines"]:
            if l["speaker"] not in speakers:
                speakers.append(l["speaker"])
        lines = []
        for i, l in enumerate(day["lines"], 1):
            vi = speakers.index(l["speaker"]) % len(JA_VOICES)
            ja_path = audio_dir / f"ja{i}.mp3"
            en_path = audio_dir / f"en{i}.mp3"
            await synth(l["ja"], JA_VOICES[vi], ja_path)
            await synth(l["en"], EN_VOICES[vi], en_path)
            lines.append({
                **l,
                "ja_audio": f"audio/{dstr}/ja{i}.mp3?g={gen}",
                "en_audio": f"audio/{dstr}/en{i}.mp3?g={gen}",
            })
        payload = {"date": dstr, "scenario": day["scenario"], "lines": lines}
        out_file.write_text(
            json.dumps(payload, ensure_ascii=False, indent=1),
            encoding="utf-8",
        )
        print(f"generated: {dstr} — {day['scenario']['title_ja']} ({len(lines)} lines)")

    dates = sorted(p.stem for p in data_dir.glob("????-??-??.json"))
    (data_dir / "index.json").write_text(json.dumps(dates), encoding="utf-8")
    print(f"index: {len(dates)} day(s)")


if __name__ == "__main__":
    asyncio.run(main())
