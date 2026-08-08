# 测试记录与验收清单

本文件是 office-visual-spec 的验收基线，只在模板或脚本改动后用于回归检查，不参与日常生成。

## 验收命令

以下命令中的 `python` 均指 `.venv` 内的解释器（Windows：`.venv\Scripts\python.exe`，macOS/Linux：`.venv/bin/python`）；没有 `.venv` 时先运行 install.bat / install.sh。

```bash
# 一键安装（首次使用；Windows 用 install.bat，macOS/Linux 用 bash install.sh）
install.bat
bash install.sh

# 环境自检（参考项，不阻塞开工；渲染失败时回查）
python scripts/doctor.py

# 仅溢出检查（唯一入口，禁止手写探针）
python scripts/render-html.py ppt-web templates/ppt-web.html --check-only

# 结构自检
node scripts/validate-html.mjs templates/a4-summary.html

# 标准导出：类型 + 输入 + 输出目录
python scripts/render-html.py a4 templates/a4-summary.html out/
python scripts/render-html.py html-ppt templates/ppt-16-9.html out/
python scripts/render-html.py ppt-web templates/ppt-web.html out/
python scripts/render-html.py xhs templates/xhs-cards.html out/
python scripts/render-html.py mobile-long templates/mobile-long.html out/
python scripts/render-html.py infographic templates/infographic.html out/
python scripts/render-html.py html-page templates/html-page.html out/
```

## 验收基线

- 所有模板（及交付前示例）通过 `validate-html.mjs`，失败数 0。
- 每个分页容器 `scrollHeight ≤ clientHeight`，溢出直接失败。
- PNG 输出像素 = 逻辑尺寸 × scale；A4 长图 1588 × 13476，静态 PPT 2560 × 4320，小红书 2160 × 8640（scale 2）。
- 手机长图默认 3x，宽 3240px；HTML 页面默认 860px 宽。
- PNG 主输出是完整长图，单页图在 `png/pages/`。
- PDF：A4 6 页、静态 PPT 3 页、交互 PPT 5 页、小红书 3 页、信息图 1 页；手机长图为单页长 PDF。
- 长 PNG 会把 `vh` 变量覆盖为固定 px，不能出现拆页；手机长图 PDF 由长图直出，不拆页。
- 间距、页边距、对齐一致；框框模块宽高可波动，但信息密度平衡。
- doctor 失败项（❌）为参考项：不阻塞开工，渲染/导出失败时按提示补齐依赖后回查；警告项（⚠️，Node）不影响渲染导出；任一渲染步骤 FAIL 时脚本退出码必须为 1。
- 交互 PPT 溢出检查必须走内置 `check_overflow(web=True)`；手写探针会被动画状态干扰，不是有效验证方式。
- 自检时必须写出实际运行命令，不能只写“已验证”。
- AI/CI 运行 bat 时加 `/nopause` 或设置 `OVS_NO_PAUSE=1`，不应挂起。

## 回归重点

- vw/vh 基准：A4 `1vw=7.94 / 1vh=11.23`；PPT `1vw=12.8 / 1vh=7.2`；小红书 `1vw=10.8 / 1vh=14.4`；信息图 `1vw=10.8 / 1vh=12.15`。
- 模块库 `references/modules.md` 与各类型文件引用一致，无断链。
- 固定画布可用 vw/vh；自然高度类型只用固定 px 或 vw。
