---
name: office-visual-spec
description: |
  暖纸红印严格视觉规范 + 工作流。生成 PDF 摘要、HTML PPT、手机长图、小红书卡片、信息图或 HTML 页面时使用。
  流程：先提问确认输出类型，再生成可编辑 HTML，自检后交付，最后按 references/render.md 标准管线导出 PNG/PDF。
  使用共享美化模块库按功能区组装，支持多种美化方案；固定画布尺寸用 vw/vh 描述，导出稳定。
  交互式网页 PPT（ppt-web）：固定 1280×720 画布 + 等比缩放舞台（任意分辨率下 16:9 恒定比例），横向翻页 deck，滚轮 / 键盘 ←→ / 触屏滑动翻页，ESC 索引，B 键低功耗；动效纯 CSS keyframes，零外部依赖。
---

# Office Visual Spec

## 0. AI 执行摘要（每次必读）

0. **环境自检（每次必做）**：首次使用或环境不确定时，先运行 `python scripts/doctor.py`。doctor 未通过前不要开始生成和渲染；缺依赖时运行 `install.bat`（Windows）或 `bash install.sh`（macOS/Linux）。AI 自动化给 bat 加 `/nopause` 或设置 `OVS_NO_PAUSE=1`；浏览器检测失败时设置 `OVS_BROWSER` 后重跑 doctor。
1. 最高优先级：先问，再写；信息不够不开始生成。
2. 信息足够后进入排版阶段：画面比例（间距、页边距、对齐）是第一要素，先定骨架，避免内容挤在一起或贴边。
3. 先读 `references/README.md` 二级索引，由它路由到类型文件和共享文件。
4. 产出必须是可编辑 HTML：单一 `<style>`、CSS 变量、真实文字。
5. 分页容器用 `<div class="sheet">`，必须是 body 直接子元素；交互式网页 PPT（ppt-web）除外。
6. 分页同时写 `page-break-after: always` 和 `break-after: page`；卡片、步骤、引文统一 `break-inside: avoid`。
7. 禁止远程 CSS/字体、正文转图片、强制水印、大面积深色或大面积红色。
8. 尺寸比例用 `vw` / `vh`；固定画布类型直接使用，自然高度类型用固定 px/vw。
9. 风格不满意时，先让用户发参考图或描述，再改 token，不整份重写。

> **溢出检查唯一入口**：`scripts/render-html.py` 内置 `check_overflow`（交互 PPT 用 `web=True`）。禁止手写 CDP、禁止自定义 scrollHeight 探针、禁止用临时脚本测溢出。

## 1. 生成前必问

- 输出类型：A4 摘要 / HTML PPT（静态截图） / 手机长图 / 小红书卡片系列 / 信息图 / HTML 页面 / 交互式网页 PPT
- 内容处理：照搬原文 / 总结改写 / 混合引用
- 结构形态：分段层级版 / 连续长文无分段版
- 风格：默认暖纸红印；不满意时请用户提供参考或描述
- 内容功能区：封面 / 小标题 / 流程 / 时间线 / 对比 / 数据 / 清单 / 人物 / 观点 / 引用 / 行动清单 / 结尾（可多选）
- 美化强度：克制 / 中等 / 丰富

用户只懂说“做 PPT”时，用下面的话问，等用户确认后再开始：

> 你是想要哪种？
> 1. 静态图版 PPT：做完是一张张 PPT 图片，可以导出 PDF/PNG，适合直接发出去。
> 2. 动态网页 PPT：可以在网页上翻页、有动效，适合演示和分享。

如果用户请求是“把 XX 做成图片 / 做个图 / 做个 PPT”这类模糊请求，先读 `references/confirmation.md`，问清楚后再进入类型文件。

确认规则：一轮问完；用户已提供的信息不再问，缺什么问什么；最后把完整计划复述一遍，等用户确认后再开始。

## 2. 入口与路由

1. 第一步：读 `references/README.md`，它是二级索引，决定当前输出类型读哪个文件。
2. 第二步：按索引只读当前类型对应的 reference；需要组合美化模块时读 `references/modules.md`；需要导出时读 `references/render.md`。
3. 模糊请求先读 `references/confirmation.md`，确认后再回到索引。

## 3. 工作流

0. **环境自检**：首次使用或环境不确定时，先运行 `python scripts/doctor.py`，未通过前不开始生成和渲染。
1. **提问确认**：输出类型、内容处理、结构形态、风格、内容功能区、美化强度；用户只说“做 PPT”时先解释静态/动态两种 PPT。
2. **读索引**：按 `references/README.md` 路由到类型文件；需要时读 `references/modules.md` 选模块。
3. **生成可用 HTML**：单一 `<style>`、CSS 变量、真实文字、目标尺寸排版；固定画布按 vw/vh 基准排版，自然高度按 px/vw 排版。
4. **自检 Review**：文字可选中、无溢出、无重叠、分页无空白页、同层级一致；重点检查间距、页边距、对齐。溢出检查必须运行 `python scripts/render-html.py <type> <html> --check-only` 并写出实际命令，禁止手写探针。
5. **输出交付结果**：HTML 路径、尺寸、页数、可导出格式。
6. **调整阶段**：先改 HTML → 生成预览并打开小工具 → 用户确认满意后再结束；每次只改需要改的部分。
7. **导出**：按 `references/render.md` 的标准管线输出 PNG/PDF，不做临场发明。

## 4. 硬规则（不可违反）

- 正文是真实文本，可复制、可搜索、可编辑。
- 所有样式放在单个 `<style>` 内，不依赖远程 CSS。
- 字体只用系统字体栈，不依赖远程字体。
- 分页容器使用 `<div class="sheet">`，禁止用 `<section>`；交互式网页 PPT（ppt-web）除外，其 `.sheet` 放在 `#deck` 内。
- 手机长图/连续长文禁止使用 `.sheet`。
- 卡片、步骤、引文使用 `break-inside: avoid`。
- 模块组合必须标注基础间隔；框框模块是自由框，宽高可波动但信息密度要平衡，且 `break-inside: avoid`。
- 禁止强制水印；页脚署名由用户决定。
- 禁止大面积深色填充，禁止大面积红色铺底。
- 文字不溢出页面，元素不重叠。
- 溢出检查唯一入口是 `scripts/render-html.py` 内置 `check_overflow`（交互 PPT 用 `web=True`）；禁止手写 CDP / scrollHeight 探针。
- 排版阶段第一要素：页面四边留白、模块间距、同类元素对齐必须统一；先满足间距和对齐，再谈装饰。
- 框框模块是自由框：宽度和高度都可以波动，但不能破坏间距、对齐和信息密度平衡。
- 固定画布类型可用 `vw` / `vh`；自然高度/自适应类型禁止依赖 `vh` / `vmin`（高度不固定）。

**版式原则（摘要，完整规则见 `references/modules.md`「构成流程」）**：
- 封面页位置自由：主层是唯一视觉中心，位置由内容和用户要求决定；硬边界是页边距一致、无溢出、无重叠、重心明确；固定画布类型重心自检参考见 modules.md（主层建议 ≤ 画布高 80%，任一侧留白超过另一侧 2 倍时重新审视）。
- 内页按「模块构成自由」：先分析该页内容功能再选模块，允许非对称、单卡、无卡片、数据格、引文大字等版式；边界是 ① 一个视觉主层 ② 间距/页边距/对齐全篇一致 ③ 无溢出无重叠 ④ 风格语言一致。
- 模板是基础底稿，不是唯一答案：同类模块替换和按视觉中心逻辑移动位置是被允许的自由度；替换后仍满足页边距、无溢出、风格一致；交付时写明本次构成。

## 5. 常见错误

- 自然高度/自适应类型误用 vh/vmin，导致比例随视口漂移；固定画布类型用 vw/vh 锁基准。
- 模块间距、页边距、对齐不统一，或画面信息密度严重失衡。
- 长文本一行画完，不允许换行。
- 标题用宋体。
- 长文模式强制分段。
- 正文做成图片。
- 只把分页写在 `@media print` 里。
- 用 `<section>` 做分页容器。

## 6. 包结构

- `references/README.md`：二级索引，路由表和包内文件索引
- `references/<type>.md`：各输出类型完整规范
- `references/modules.md`：共享美化模块库 + 各类型 `vw/vh` 基准 + 功能区映射
- `references/render.md`：渲染与导出契约
- `references/confirmation.md`：模糊请求确认问答
- `references/style-adjustment.md`：风格调整流程
- `templates/`：各类型模板
- `scripts/`：自检、doctor 诊断和标准渲染管线
- `install.bat / install.sh / doctor.bat / doctor.sh / requirements.txt`：一键安装与环境自检
- `examples/`：参考样本
