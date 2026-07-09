#!/usr/bin/env python3
"""每日生成：从语料库取当天 3 句，用 edge-tts 合成语音，输出到 site/。

用法:
  python scripts/generate.py            # 生成「今天(JST)」的内容，已存在则跳过
  python scripts/generate.py --force    # 强制重新生成今天
  python scripts/generate.py 2026-07-12 # 生成指定日期（补数据用）
"""
import asyncio
import json
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import edge_tts

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"
JA_VOICE = "ja-JP-NanamiNeural"   # 换声音改这里，候选: ja-JP-KeitaNeural(男声)
EN_VOICE = "en-US-JennyNeural"    # 候选: en-US-GuyNeural(男声), en-US-AriaNeural
JST = timezone(timedelta(hours=9))


def target_date() -> date:
    for a in sys.argv[1:]:
        if not a.startswith("-"):
            return date.fromisoformat(a)
    return datetime.now(JST).date()


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
    start = date.fromisoformat(corpus["start"])
    days = corpus["days"]

    today = target_date()
    day = days[(today - start).days % len(days)]
    dstr = today.isoformat()

    data_dir = SITE / "data"
    audio_dir = SITE / "audio" / dstr
    data_dir.mkdir(parents=True, exist_ok=True)
    out_file = data_dir / f"{dstr}.json"

    if out_file.exists() and "--force" not in sys.argv:
        print(f"skip: {dstr} already generated")
    else:
        audio_dir.mkdir(parents=True, exist_ok=True)
        scenes = []
        for i, s in enumerate(day["scenes"], 1):
            ja_path = audio_dir / f"ja{i}.mp3"
            en_path = audio_dir / f"en{i}.mp3"
            await synth(s["ja"], JA_VOICE, ja_path)
            await synth(s["en"], EN_VOICE, en_path)
            scenes.append({
                **s,
                "ja_audio": f"audio/{dstr}/ja{i}.mp3",
                "en_audio": f"audio/{dstr}/en{i}.mp3",
            })
        out_file.write_text(
            json.dumps({"date": dstr, "scenes": scenes}, ensure_ascii=False, indent=1),
            encoding="utf-8",
        )
        print(f"generated: {dstr}")

    dates = sorted(p.stem for p in data_dir.glob("????-??-??.json"))
    (data_dir / "index.json").write_text(json.dumps(dates), encoding="utf-8")
    print(f"index: {len(dates)} day(s)")


if __name__ == "__main__":
    asyncio.run(main())
