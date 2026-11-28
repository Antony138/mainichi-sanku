# 毎日場面 mainichi-sanku

每天早上 6:00（JST）自动更新**一个实用场景的日语对话**（约 6 句，日・英・中对照），网页逐句点读（点哪句读哪句，日语英语都能点），支持整段连播、循环、慢速、盲听模式、间隔复习、WIP 收藏，可离线。

**网页**: https://antony138.github.io/mainichi-sanku/

手机用法：Safari/Chrome 打开 → 分享 → **添加到主屏幕**，以后点图标秒开。

## 工作原理

```
GitHub Actions (每天 21:00 UTC = 6:00 JST)
  └─ scripts/generate.py
       ├─ 从 corpus/corpus.json 取当天场景：lessons 里没出过的优先，否则按日期轮换 days（30 个场景循环）
       ├─ edge-tts 逐句合成神经语音 mp3，对话双方自动分配不同声线
       │    日语: Nanami(女)/Keita(男)  英语: Jenny(女)/Guy(男)
       └─ 写入 site/data/YYYY-MM-DD.json + site/audio/YYYY-MM-DD/*.mp3
  └─ commit 生成内容 → 部署 site/ 到 GitHub Pages
```

页面（`site/index.html`）是纯静态 PWA：Service Worker 离线缓存，历史归档可回看，自动带出 3 天前 / 7 天前的场景做间隔复习。2026-07-16 以前的「每日三句」旧数据仍可回看。

**顶部导航条**（滚动时吸附在顶端）：左边是 WIP 筛选按钮，右边是历史日期。点场景标题右侧的 **★ WIP** 把正在重点练的场景收藏起来，日期上会出现 ★；点顶部 **★ WIP** 只列 WIP 场景，chip 直接显示场景标题，一点就跳过去练。收藏存在浏览器 `localStorage`（键 `msk_wip`，日期 → 场景标题），不上传、换设备不同步。

## 已学内容：放进场景 + 高亮

上课学过的语法和词会在页面上**自动高亮**（语法=黄色荧光笔，词汇=绿色），点一下弹出说明（变法、例句、哪节课学的）；每个场景标题下面也会列出本场景用到的已学点。高亮对所有日期都生效，包括历史和「温故」复习区。

两处配合：

1. **`site/learned.json`**：已学清单。每条一个语法点或词：

   ```json
   {"id": "kereba", "kind": "grammar", "label": "い形容词＋ければ",
    "pattern": "[\u4e00-\u9fff]*[ぁ-ゖ]?ければ",
    "note": "い形容词去「い」＋ければ：如果……的话",
    "example": "暑い → 暑ければ", "source": "italki · 11/26"}
   ```

   - `kind`：`grammar` 或 `vocab`（决定颜色）。
   - `pattern`：正则，匹配去掉振假名后的日文句子。**更具体的写在前面**（例如 `〜なければ`、`よければ` 排在 `ければ` 前），同一处只高亮第一个匹配到的条目。
   - 改完 push 即生效（只改页面数据，不用重新生成音频）。

2. **`corpus/corpus.json` 的 `lessons`**：专门用已学内容写的场景，格式和 `days` 一样，可加 `scenario.learned_from`（例如 `"italki 11/26"`，显示在已学标签旁）。每天生成时，`lessons` 里**还没出过的场景按顺序优先**（每个出一次，之后也会在 3 天／7 天的「温故」里再出现），都出过了再回到 `days` 轮换。`generate.py` 会检查每个 `lessons` 场景至少用到一个已学点。

**上完一节课后**：往 `learned.json` 加新语法点，往 `lessons` 加 1–2 个用到它们的场景，push。想今天就看到，到 Actions 手动 Run workflow 勾 **force**。

## 语料格式

`corpus/corpus.json` 的 `days` 数组每项是一个场景：

```json
{
 "scenario": {
  "title_ja": "コンビニで会計", "title_cn": "便利店结账",
  "desc": "场景说明（中文）", "tip": "一句话用法提示（可选）"
 },
 "lines": [
  {"speaker": "店員", "ja": "…", "ruby": "…<ruby>漢字<rt>かな</rt></ruby>…", "en": "…", "cn": "…"}
 ]
}
```

- `ruby` 去掉标签后必须与 `ja` 完全一致（`generate.py` 会校验，不一致直接报错）。
- 声音按说话人**出场顺序**分配：第 1 位 Nanami/Jenny，第 2 位 Keita/Guy（第 3 位起回绕）。
- 语料轮完一圈（30 天）自动从头循环；往 `days` 追加新场景即可扩充。

## 常用操作

- **加场景 / 换主题**：编辑 `corpus/corpus.json`，按上面的格式往 `days` 追加。
- **加上课学的内容**：见上面「已学内容」。
- **改完语料立即生效**：GitHub Actions 页面手动 Run workflow，勾选 **force** 即可重新生成今天。
- **换声音**：改 `scripts/generate.py` 顶部的 `JA_VOICES` / `EN_VOICES`。候选列表：`edge-tts --list-voices`。
- **手动补某天**：`python scripts/generate.py 2026-07-12`（本地跑需 `pip install edge-tts`）。
- **调界面**：改 `site/index.html`，push 后自动重新部署。

## 成本

全部免费：GitHub Actions（公开仓库免费）+ GitHub Pages + edge-tts（微软 Edge 朗读接口，无需 API key）。
