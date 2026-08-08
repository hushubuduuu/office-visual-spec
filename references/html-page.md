# 通用 HTML 页面生成规范

## 输出与模板

- 模板：`templates/html-page.html`；可复制后按内容修改。
- vw/vh 基准：不强制；用 vw 或固定 px 描述。

## 模块组装

- 本类型功能区：页面头 / 章节 / 引用 / 结尾。
- 构成优先于模板：模板是基础底稿，不是唯一答案；先分析内容、选模块、再构成画面，在保持本类型硬规则（尺寸、分页、页边距、无溢出、风格一致）的前提下允许一定自由度，禁止 100% 照搬模板出品；封面页位置自由（左上、居中、右下等均可，见 `references/modules.md` 构成流程），内页按「模块构成自由」。
- 参考与替换：可参考模板中每个模块的大小权重，用同类模块替换（如同一功能区卡片、步骤、清单互换），并按视觉中心逻辑移动位置；替换后仍满足页边距、无溢出、风格一致。
- 模块从 `references/modules.md` 共享库选择，按 `references/modules.md` 的功能区映射。
- 模块尺寸用 `vw` 描述，或按内容宽度比例换算为固定 px。
- 排版阶段优先级：间距、页边距、对齐 > 模块内容 > 装饰；先完成提问，再按此顺序处理。
- 宽度自适应，不设固定画布；不强制 `.sheet` 分页。
- 不做固定比例缩放，高度随内容。

## 设计令牌

### 4.1 色板（HTML / PDF）

| Token | Hex | 用途 |
| --- | --- | --- |
| paper | #FDFDFB | 页面背景、反白文字 |
| ink | #181614 | 主标题、正文强调、深色方块 |
| body | #2E2A27 | 正文 |
| narrative | #3C3632 | 叙事段落 |
| muted | #7E7872 | 标签、眉标、页脚 |
| red | #D31212 | 强调、红条、印章 |
| deep-red | #A80E0E | 重点词 |
| divider | #EBE6DF | 分隔线、卡片描边 |
| card | #FFFBF9 | 卡片底 |
| on-accent | #FDFDFB | 反白文字 |

### 4.2 色板（PPT）

| Token | Hex |
| --- | --- |
| paper | #FAF8F5 |
| ink | #221E1A |
| body | #443F3A |
| narrative | #554F49 |
| muted | #8E877F |
| red | #C60D0D |
| deep-red | #A50A0A |
| divider | #E2DDD5 |
| card | #FDF9F7 |
| on-accent | #FAF8F5 |

### 4.3 字体

- 衬线正文：`Georgia, STSongti-SC, Songti SC, Noto Serif CJK SC, Source Han Serif SC, SimSun, serif`
- 黑体标题与长文正文：`system-ui, -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, Helvetica Neue, PingFang SC, Noto Sans CJK SC, Microsoft YaHei, sans-serif`
- 标题必须黑体加粗，禁止用 Light 细体或宋体做标题。
- 长文模式标题和正文都用黑体，字距为零。

## 扩展主题

新增主题时只覆盖 CSS 变量，不改变组件结构和分页规则：

```css
:root {
  --paper: #...;
  --ink: #...;
  --body: #...;
  --muted: #...;
  --red: #...;
  --divider: #...;
  --card: #...;
  --on-accent: #...;
}
```

## 主题注册表

内置主题与完整 CSS 变量值见 `references/modules.md`（默认「暖纸红印」）。新增主题只覆盖上面的变量，不改变组件结构和分页规则。

## 页面规则

- 页面宽度自适应，高度随内容。
- 不强制分页；内容很长时允许自然滚动。
- 手机阅读建议正文 ≥36px（1080 基准）；桌面阅读建议正文 ≥18px。

## 组件与美化

- 组件库、字号层级、间距基准、功能区映射统一见 `references/modules.md`；html-page 属自然高度类型，其中的固定画布 vw/vh 基准不适用，禁止依赖 `vh` / `vmin`。
- 可读性底线：手机阅读（1080 基准）正文 ≥36px、主标题 ≥160px；桌面阅读正文 ≥18px。
- 间距与对齐：同层级模块纵向间隔一致、页边距左右一致、文字不贴卡片；卡片双层阴影，每页 2–4 种装饰，风格语言一致。

## 自检与交付

## 自检清单

- [ ] 文字可选中、可复制
- [ ] 无溢出、无重叠
- [ ] 分页无空白页
- [ ] 标题不孤立，卡片不拆页
- [ ] 同层级字号、字重、颜色一致
- [ ] 手机长图达到大字标准：正文 ≥36px、主标题 ≥160px（1080 基准）
- [ ] 卡片有双层阴影，不平扁平
- [ ] 每页有 2–4 种装饰
- [ ] 卡片间距一致，文字不贴卡片
- [ ] 封面和结尾页都有文档类型标签
- [ ] 结尾页与开头页一样丰富
- [ ] 背景无大面积红晕/光晕
- [ ] 交互式网页 PPT：每页 frame `scrollHeight ≤ offsetHeight`（无溢出、页脚不被挤压）
- [ ] 交互式网页 PPT：封面标题 100px、按钮行同一水平线
- [ ] 交互式网页 PPT：ESC 索引缩略图内容可见；翻页 / 圆点 / 键盘 / 滚轮可用

可运行 `scripts/validate-html.mjs <html>` 做静态自检。

## 交付清单

- HTML 文件路径
- 目标尺寸
- 页数/卡片数
- 可导出格式：PNG / 图片集 / 视觉 PDF / Headless 可复制 PDF / 其他 skill 生成 PPTX
- 本次构成说明：用了哪些模块、为什么这样选、与模板的差异点

## 常见错误

- 自然高度页面误用 `vh` / `vmin`，高度随视口漂移。
- 正文小于可读字号（1080 基准 <36px / 桌面 <18px）。
- 模块间距、页边距、对齐不统一，信息密度失衡。
- 内容溢出页面底部被裁切——用 `scripts/render-html.py --check-only` 检查（唯一入口）。

## 导出 PDF / PNG 注意事项

- PNG：整页长图截图，导出前关闭编辑框线。
- PDF：浏览器打印，文字可复制；视觉稿可用截图。
- 不强制分页，空白页不作为问题。

- 标准渲染参数见 `references/render.md`，不要临场发明参数。

## 风格调整

风格不满意时，再读取 `references/style-adjustment.md`。
