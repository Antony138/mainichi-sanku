# 毎日三句 mainichi-sanku

每天早上 6:00（JST）自动更新三句「中・日・英」对照例句，网页逐句点读（点哪句读哪句），支持慢速、单句循环、盲听模式、间隔复习，可离线。

**网页**: https://antony138.github.io/mainichi-sanku/

手机用法：Safari/Chrome 打开 → 分享 → **添加到主屏幕**，以后点图标秒开。

## 工作原理

```
GitHub Actions (每天 21:00 UTC = 6:00 JST)
  └─ scripts/generate.py
       ├─ 从 corpus/corpus.json 按日期轮换取当天 3 个场景句
       ├─ edge-tts 合成日语(Nanami)/英语(Jenny)神经语音 mp3
       └─ 写入 site/data/YYYY-MM-DD.json + site/audio/YYYY-MM-DD/*.mp3
  └─ commit 生成内容 → 部署 site/ 到 GitHub Pages
```

页面（`site/index.html`）是纯静态 PWA：Service Worker 离线缓存，历史归档可回看，自动带出 3 天前 / 7 天前的句子做间隔复习。

## 常用操作

- **加语料 / 换主题**：编辑 `corpus/corpus.json`，往 `days` 数组追加天数即可（每天 3 个场景，含 `scene/ja/ruby/en/cn` 字段）。语料轮完一圈会自动从头循环。
- **换声音**：改 `scripts/generate.py` 顶部的 `JA_VOICE` / `EN_VOICE`。候选列表：`edge-tts --list-voices`。
- **手动补某天**：`python scripts/generate.py 2026-07-12`（本地跑需 `pip install edge-tts`），或在 GitHub Actions 页面手动 Run workflow。
- **调界面**：改 `site/index.html`，push 后自动重新部署。

## 成本

全部免费：GitHub Actions（公开仓库免费）+ GitHub Pages + edge-tts（微软 Edge 朗读接口，无需 API key）。
