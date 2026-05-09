# 观远自定义图表排障手册

## 已验证的模式

### 1. 用完整自定义图表，不用 Lite

- 需要注入 HTML、CSS、JS 时，使用 `自定义图表`
- 页面级 DOM 操作不要用 `Lite`

### 2. 让加载器看得到注入卡，但用户不必看到

- 观远自定义图表 iframe 是懒加载的
- 如果注入卡放在首屏以下，初次进页时脚本可能根本不执行
- 可靠做法：
  - 把注入卡放在首屏
  - 查看态视觉隐藏
  - 编辑态恢复可见

### 3. overlay 和 mask 挂到页面根节点

- `__gd_overlay__` 和 `__gd_overlay_mask__` 要挂在当前页面根节点
- 不要挂到 `body`
- 挂到 `body` 的常见后果：
  - 切页后残留
  - 更容易和原生浮层打架
  - 与右侧原生锚点导航层级冲突

### 4. overlay 的 z-index 要低而够用

- 一个可用基线：
  - overlay 容器约 `8`
  - mask 约 `1`
  - 固定卡项约 `20`，按需要递减
- 目标是：
  - 高于滚动内容
  - 低于观远原生导航、菜单、工具层

### 5. 主动触发图表重排

- 左侧栏展开收起后，固定卡宽度会变化
- 被搬进 overlay 的图表内容不一定自动重排
- overlay 尺寸变化时，主动派发：
  - 立即一次 `resize`
  - 再延迟几次 `resize`

### 6. 上下文切换时要主动销毁

- 遇到以下情况要销毁 overlay：
  - URL 不再匹配目标 page id
  - 进入编辑态
  - 切到 `pageRenderType=phoneView`
  - 客户端路由离开当前页
- 只在目标桌面查看态重建

## 这类问题里常见的失败模式

### 1. 复制页面后 card id 全变

- 观远复制页面会生成新的 card id
- 继续使用原页面硬编码 id，通常不会显式报错，只会悄悄失效

### 2. 注入卡放太靠下，导致脚本从未执行

- 因为 iframe 还没创建，首屏加载时注入逻辑根本没跑

### 3. `MutationObserver` 自触发死循环

- 监听 `body subtree` 后又在回调里改样式，容易反复触发，卡死页面
- 更稳的是：
  - 低频轮询
  - 精准 rect 比较

### 4. overlay 挂到 `body` 后跨路由残留

- 离开目标页后，固定卡还留在别的页面上

### 5. 固定层和真实布局错位

- 如果真实布局上移了多少，overlay 也必须减去同样的位移
- 否则固定区上方会出现空白行

### 6. 右侧原生导航失效

- overlay z-index 提太高，会挡住原生导航
- 把原生导航节点 reparent 到 `body`，看起来可见，但交互容易坏
- 自己克隆一套导航，通常和原生行为逐步偏离

这类场景更可靠的路径是：

1. 保留原生导航
2. overlay 挂页面根节点，不挂 `body`
3. 如果历史实验改坏了原导航，恢复它的 `visibility` / `pointer-events`
4. 用真实浏览器点击验收

## 浏览器排障清单

### 1. 改代码前先看 live runtime

先检查：

- 当前 URL 和 page id
- `window` 上是否已有旧版注入 key
- `__gd_overlay__` 和 `__gd_overlay_mask__` 是否存在
- 页面里是否留有历史实验节点

### 2. 找到真正可点击的 DOM

- 不要把“看到的文本节点”误当成真正交互节点
- 对右侧锚点导航，真正有用的目标往往是：
  - 打开按钮图标
  - tab 按钮
  - pin 图标

### 3. 用 `elementFromPoint` 查层级问题

- 控件可见但点不动时，查控件中心点命中的真实元素
- 如果命中的是 fixed card 或 overlay 子节点，说明是层级问题
- 如果命中的是正确控件但还是不工作，往往是：
  - 之前点错节点
  - 某个祖先禁用了 pointer events

### 4. 最终用真实浏览器点击验收

- 最终不要只靠 `page.evaluate(... click())`
- 要用真实浏览器点击，确认：
  - tab 切换是否真的生效
  - 页面滚动位置是否真的变化
  - pin 状态是否真的切换

## `payload_json` 取数排障专用结论

### 1. runtime callback 比 `/api/card/.../data` 更重要

- 当前观远 runtime 的真实签名是：

```javascript
function renderChart(data, clickFunc, config, helpers) {}
```

- `data` 常见形态是：

```javascript
[
  [
    { name: "payload_json", data: ["{...}"] },
    { name: "report_date", data: ["2026-03-18"] }
  ]
]
```

- 所以要优先围绕 runtime `data` 写解析逻辑

### 2. 看到 `payload_json` 不代表数据可用

- 必须实际执行：

```javascript
JSON.parse(payload_json)
```

- 如果这里失败，说明数据本身坏了，不是图表没取到

### 3. `Unterminated string` 基本就是截断

- 如果报：
  - `Unterminated string`
  - `Unexpected end of JSON input`
- 优先判断为：
  - 超长 JSON 字符串在数据链路中被截断
- 这时不要继续堆前端兼容逻辑

### 4. 推荐方案是拆列，不是整包 JSON

- 长报告不要继续塞进一个 `payload_json` 大字符串
- 应拆成多列，例如：
  - `report_date`
  - `send_window`
  - `key_insights_md`
  - `safety_intro_md`
  - `productivity_intro_md`
  - `service_intro_md`
  - `quality_intro_md`
  - 以及各 section 对应的明细列 / 明细子表
- 前端直接读拆列字段，比 runtime 再 `JSON.parse(payload_json)` 稳得多

## 交付建议

- 一旦浏览器验证稳定，优先给完整替换版 JS
- 提醒用户执行：
  - `保存`
  - `发布`
  - 强刷查看页
- 页面彻底坏掉时，先用最小恢复脚本救回来：

```javascript
function renderChart() {}
new GDPlugin().init(renderChart);
```
