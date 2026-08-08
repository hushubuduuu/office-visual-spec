# 渲染与导出契约

本文件定义所有输出类型的 HTML → PNG / PDF 标准路径，禁止临场发明参数。统一入口是 `scripts/render-html.py`。

导出架构与本地 HTML 编辑器一致：

- **PNG = 当前设备完整长图**，不做分页裁切。
- **PDF = 分页整本 PDF**，按画布高度逐页切分。
- **`png/pages/` = 逐页图片集**，需要单页图片时使用。
- 手机长图输出单页长 PDF `pdf/mobile-long.pdf`，由长图直出，与 PNG 画面一致。

## 输出矩阵

| 类型 | HTML 画布（CSS px） | PDF 页面 | PNG 方式 | 分页/打印规则 |
| --- | --- | --- | --- | --- |
| A4 摘要 | 794 × 1123 | 每页 A4 | 完整长图：794 宽，高 = 页数 × 1123；图集在 `png/pages/` | `@page { size: A4; margin: 0 }`，每章一个 `.sheet` |
| HTML PPT（静态） | 1280 × 720 | 每页 1280 × 720 | 完整长图：1280 宽，高 = 页数 × 720；图集在 `png/pages/` | `@page { size: 1280px 720px; margin: 0 }`，动画静态化 |
| 交互网页 PPT | 1280 × 720 舞台 | 打印降级为静态分页 | 横向 deck，逐页截图 `png/page-XX.png` | 导出前关动效/低功耗；`@media print` 静态降级 |
| HTML 页面 | 默认 860 宽，高度随内容 | 默认 A4 连续流 | 整页长图截图 | 不强制分页 |
| 小红书卡片 | 1080 × 1440 | 每卡一页 | 完整长图：1080 宽，高 = 页数 × 1440；图集在 `png/pages/` | `@page { size: 1080px 1440px; margin: 0 }` |
| 手机长图 | 1080 宽，高度随内容 | 单页长 PDF（视觉稿） | 整页长图截图 | 无 `.sheet`，不拆页 |
| 信息图 | 1080 × 1215（按模板） | 单页 | 整页截图 | `@page { size: 1080px 1215px; margin: 0 }` |

PNG 规则：`输出像素 = HTML 画布 CSS 像素 × scale`。不要先乘 2 再套 `--force-device-scale-factor`，否则会变成 4 倍像素。

## 标准命令

脚本统一用 `.venv` 内的 python 运行（Windows：`.venv\Scripts\python.exe`；macOS/Linux：`.venv/bin/python`）。没有 `.venv` 时先运行 `install.bat` / `install.sh`；doctor 或 render 被系统 python 调用时会自动切换到 `.venv`，但命令示例统一按 venv python 写：

```text
.venv\Scripts\python.exe scripts\render-html.py <type> <input.html> <outdir> [--scale 2] [--width 1080]   # Windows
.venv/bin/python scripts/render-html.py <type> <input.html> <outdir> [--scale 2] [--width 1080]          # macOS / Linux
```

> 下文出现 `python scripts/render-html.py ...` 时，均指 `.venv` 内的解释器。

- `<type>`：`a4 | html-ppt | ppt-web | html-page | xhs | mobile-long | infographic`
- `--scale`：PNG 倍率；A4/PPT/卡片/信息图默认 2，手机长图默认 3
- `--width`：仅 `html-page` / `mobile-long` 生效，覆盖默认逻辑宽度
- 长图会自动读取内容高度，再按该高度截图，不会截断也不会留下大片空白
- 仅做溢出检查：`python scripts/render-html.py <type> <input.html> --check-only`（venv python，见上文）；交互 PPT 自动使用 `web=True`，禁止手写探针。

输出结构：

```text
out/
  png/<type>-full.png        # 完整长图（PNG 主输出）
  png/pages/page-XX.png     # 逐页图片集
  pdf/<type>.pdf            # 分页整本 PDF（A4/静态PPT/小红书/HTML页面）
  pdf/mobile-long.pdf       # 手机长图：单页长 PDF，由长图直出
```

例外：ppt-web 只产出 `png/page-XX.png`（横向 deck 逐页截图，无 `-full.png`、无 `pages/`）；infographic 只产出 `png/infographic-full.png` + `pdf/infographic.pdf`，无 `pages/`。

## Chrome Headless 标准参数

```text
--headless=new
--disable-gpu
--disable-background-networking
--disable-component-update
--disable-sync
--metrics-recording-only
--no-first-run
--host-resolver-rules=MAP * ~NOTFOUND, EXCLUDE localhost
--hide-scrollbars
--force-device-scale-factor=<scale>
--window-size=<w>,<h>
--virtual-time-budget=12000
--user-data-dir=<独立临时目录>
```

`<w>,<h>` 是逻辑 CSS 尺寸，`<scale>` 只控制输出像素倍率。

平台差异（自动处理，agent 无需干预）：macOS 默认不传 `--user-data-dir`（改用 `--incognito` 内存隔离，避免部分 macOS 构建挂起），仅探针空输出时自动用临时 profile 重试一次；`--virtual-time-budget` 在部分环境会挂起（chromium issue 40219957，间歇性/环境相关），脚本检测到后自动移除并重试，截图回退把动画压缩到瞬时完成、PDF 回退（print-to-pdf 为 t=0 同步快照）把动画静态化；`OVS_NO_VIRTUAL_TIME=1` 可强制禁用 budget 路径。详见 README「macOS 注意事项」。

已知限制：无预算回退路径下（虚拟时钟不推进），`ppt-web` 逐页 PNG 依赖页面 `setTimeout` 翻页定时器，可能截到同一页；此时请重试导出，或改用预算路径可用的环境。

- 默认禁止渲染时联网；确需联网时设置环境变量 `OVS_ALLOW_NETWORK=1`。
- 默认启用浏览器沙箱；脚本会自动探测沙箱可用性，仅在带沙箱无法启动时降级并在终端显示 WARN。`OVS_NO_SANDBOX=1` 可强制关闭沙箱。
- 可用 `OVS_BROWSER` 指定浏览器路径或命令；可用 `OVS_DEBUG=1` 显示完整错误信息。
- 临时 profile 使用唯一临时目录，脚本会重试清理；异常强杀时可能残留 `%TEMP%\ovs-*`。

## 逐页截图方法

所有 `.sheet` 必须是 `<div class="sheet">`，且是同一层级的唯一元素类型。

```css
.sheet { display: none !important; }
.sheet:nth-of-type(N) { display: block !important; }
```

截图时统一注入 `body/sheet/canvas { margin: 0; box-shadow: none }`，避免屏幕预览的 24px 外边距把画布底部裁掉。

截图前先做溢出检查（`scripts/render-html.py` 自动执行）：

```js
Array.from(document.querySelectorAll('.sheet, .canvas')).forEach(s => {
  if (s.scrollHeight > s.clientHeight + 1) {
    throw new Error('sheet overflow: ' + s.scrollHeight + ' > ' + s.clientHeight);
  }
});
```

> 验证入口：以上检查已内置在 `render-html.py`，用 `--check-only` 运行即可。禁止另写 CDP / scrollHeight 探针；手写探针会被动画状态干扰。
> 幽灵数字注意：大字号 ghost 数字建议用衬线字体，或加 `height:1em; overflow:hidden`，否则无衬线下 `scrollHeight` 虚高会导致 `check_overflow` 误报。


## 交互网页 PPT 截图

- 等待 700ms 翻页 lock 结束后再调用 `go(i)`。
- 截图前强制 `[data-anim]` 可见。
- 不要用整页滚动截图，否则横向 deck 会变成一张长图。

## PDF 导出

- 用 `--print-to-pdf` + `--no-pdf-header-footer`。
- HTML 内必须写对应类型的 `@page`。
- 导出后用 PDF 阅读器检查页数，不能多出空白页。
- 可复制文字 PDF 用 Headless 打印；截图 PDF 只是视觉稿。
- 手机长图的单页长 PDF 由已渲染的长图直接生成，与 PNG 画面一致；不使用 A4 分页打印。
- 长 PNG 会把 `vh` 视口拉长，标准管线会对已知 `vh` 变量注入固定 px 覆盖，避免内容被撑高拆页。

## 辅助脚本（可选）

标准管线之外另有三个独立脚本，参数见各自 `--help`，均用 `.venv` 内 python 运行：

- `scripts/pptx_template.py <out.pptx>`：生成 PPTX 模板，供 python-pptx 二次加工。
- `scripts/pdf_from_html.py <out.pdf> --input <input.html>`：Headless 打印为可复制文字的 PDF。
- `scripts/long_essay_to_png.py <input.html> <out.png> [--width 1080]`：连续长文 → 长图 PNG。

任何一步失败退出码非零；`OVS_DEBUG=1` 可看完整错误。

## 验证清单

- [ ] 每个 `.sheet` 是 `<div class="sheet">`
- [ ] 每页 `scrollHeight ≤ clientHeight`
- [ ] PNG 尺寸 = 逻辑尺寸 × scale，不出现 4 倍像素
- [ ] `png/<type>-full.png` 高度 = 页数 × 单页高度 × scale
- [ ] `png/pages/` 单页图与 PDF 页面布局一致
- [ ] PDF 页数符合预期，无空白页
- [ ] 打印模式下无拆页、无内容重叠
- [ ] 手机长图/HTML 页面按内容高度截图，无截断
