# Part C-3 · payload_json 取数排障详解

> 由 SKILL.md V1.4.0 拆分而出。SKILL.md 主文档保留 C-1/C-2 runtime 契约和 C-4 以后的页面级排障；遇到 payload_json 截断 / 解析失败 / 数据链路怀疑时回这里。

---

## 三种"拿不到 payload"的细分

```text
1. runtime 里根本没有 payload_json     → 数据集没出 / 卡片配置错
2. payload_json 在，但没被正确解包      → 解析逻辑问题
3. payload_json 在，但字符串本身已损坏  → 数据链路截断
```

## 最快判断方式

- 卡片里临时输出 `data/config/helpers` 摘要
- 抓 live 页 iframe 的 `window.PR_REPORT_CONTEXT`
- 抓浏览器里真实发出的 `/api/card/.../data` 请求和响应

## payload_json 硬规则

```javascript
JSON.parse(payload_json)  // 这才是最终判断标准
```

如果报：
- `Unterminated string`
- `Unexpected end of JSON input`
- 其他明显截断类错误

**优先判断为"数据链路把长字符串截断了"，不是图表 JS 自身问题。**

这种情况下：
- ❌ 不要继续堆兼容解析逻辑
- ❌ 不要再试图用更多递归去"猜"
- ✅ **优先改数据方案**

## 超长字符串的实战结论

实战观察：live 页 runtime 明明有 `payload_json` 列，但里面的 JSON 字符串中途被截断 → `JSON.parse` 失败。

页面表现：
- 有 `report_date`
- 标题能出来
- 正文和 sections 都空
- 或直接显示 `Unable to resolve payload_json`

## 推荐方案：拆列，不是整包 JSON

不要把整份报告压成一个超长 `payload_json` 字段过图表数据链路。**拆成多列**：

```text
report_date
send_window
key_insights_md
safety_intro_md
productivity_intro_md
service_intro_md
quality_intro_md
... 各 section 对应的明细列 / 明细子表
```

让前端直接读拆列后的字段，比 runtime 再 `JSON.parse(payload_json)` 稳得多。
