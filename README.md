# 毎日場面 mainichi-sanku

每天早上 6:00（JST）自动更新**一个实用场景的日语对话**（约 6 句，日・英・中对照），网页逐句点读（点哪句读哪句，日语英语都能点），支持整段连播、循环、慢速、盲听模式、间隔复习，可离线。

**网页**: https://antony138.github.io/mainichi-sanku/

手机用法：Safari/Chrome 打开 → 分享 → **添加到主屏幕**，以后点图标秒开。

## 工作原理

```
GitHub Actions (每天 21:00 UTC = 6:00 JST)
  └─ scripts/generate.py
       ├─ 从 corpus/corpus.json 按日期轮换取当天场景（30 个场景循环）
       ├─ edge-tts 逐句合成神经语音 mp3，对话双方自动分配不同声线
       │    日语: Nanami(女)/Keita(男)  英语: Jenny(女)/Guy(男)
       └─ 写入 site/data/YYYY-MM-DD.json + site/audio/YYYY-MM-DD/*.mp3
  └─ commit 生成内容 → 部署 site/ 到 GitHub Pages
```

页面（`site/index.html`）是纯静态 PWA：Service Worker 离线缓存，历史归档可回看，自动带出 3 天前 / 7 天前的场景做间隔复习。2026-07-16 以前的「每日三句」旧数据仍可回看。

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
- **改完语料立即生效**：GitHub Actions 页面手动 Run workflow，勾选 **force** 即可重新生成今天。
- **换声音**：改 `scripts/generate.py` 顶部的 `JA_VOICES` / `EN_VOICES`。候选列表：`edge-tts --list-voices`。
- **手动补某天**：`python scripts/generate.py 2026-07-12`（本地跑需 `pip install edge-tts`）。
- **调界面**：改 `site/index.html`，push 后自动重新部署。

## 成本

全部免费：GitHub Actions（公开仓库免费）+ GitHub Pages + edge-tts（微软 Edge 朗读接口，无需 API key）。
