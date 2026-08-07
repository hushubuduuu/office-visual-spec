# office-visual-spec 包

暖纸红印严格视觉规范 + 工作流 skill 包。支持 Windows / macOS / Linux。

## 快速开始

第一次使用先安装环境：

- Windows：双击 `install.bat`
- macOS / Linux：运行 `bash install.sh`

安装完成后检查环境：

- Windows：双击 `doctor.bat`
- macOS / Linux：运行 `bash doctor.sh`

AI 或 CI 自动运行时，给 bat 加 `/nopause`，或设置 `OVS_NO_PAUSE=1`；CI 环境会自动跳过 `pause`。

`doctor` 会逐项检查 Python、依赖、Node、Chrome/Edge，并显示 ✅/❌ 和解决办法。

## 工作流

1. 提问确认输出类型、内容处理、结构形态、风格。
2. 读 `references/README.md` 二级索引，按功能区从 `references/modules.md` 选模块，从 `templates/` 选择模板，生成可编辑 HTML。
3. 运行 `scripts/validate-html.mjs` 自检。
4. 用 `scripts/render-html.py` 按 `references/render.md` 标准管线导出 PNG/PDF。
5. 交付 HTML 路径、尺寸、页数、导出文件。
6. 用户可微调；风格不满意时走 `references/style-adjustment.md`。

## 目录

```text
SKILL.md                          # 工作流 + AI 执行摘要 + 硬规则 + token
references/                       # 二级索引 README.md + 类型规范 + 模块库 modules.md
templates/                        # A4 / 静态 PPT / 交互网页 PPT / 小红书 / 手机长图 / 长文 / HTML 页面 / 信息图模板
scripts/                          # 自检、诊断和标准渲染管线
examples/                         # 参考样本（不规则分页、A4 示例、小红书成品）
install.bat / install.sh          # 一键安装
doctor.bat / doctor.sh            # 环境自检入口
requirements.txt                  # Python 依赖
```

## 使用

```bash
# 自检 HTML
node scripts/validate-html.mjs templates/ppt-16-9.html

# 标准导出：类型 + 输入 + 输出目录
python scripts/render-html.py html-ppt templates/ppt-16-9.html out/
python scripts/render-html.py mobile-long templates/mobile-long.html out/
```

所有类型的画布、PDF 页、PNG 倍率和截图规则见 `references/render.md`，不要临场发明导出参数。

## 依赖

- Python 3.10+
- `Pillow`、`PyMuPDF`、`python-pptx`（见 `requirements.txt`）
- Node.js 18+（仅自检脚本需要）
- Chrome / Edge / Chromium

macOS 用户注意：Safari 不支持 headless 渲染，请安装 Chrome、Chromium 或 Edge；安装后运行 doctor，或用 `OVS_BROWSER` 指定浏览器路径。

在中国大陆如果官方 PyPI 慢或失败，`install.bat` / `install.sh` 会自动用清华镜像重试，也可以先设置 `OVS_PIP_INDEX` 指定镜像。Node 自检脚本只用内置模块，不需要 npm 安装；浏览器需要单独安装，或设置 `OVS_BROWSER` 指向已有浏览器。

## 环境变量

| 变量 | 作用 |
| --- | --- |
| `OVS_BROWSER` | 指定浏览器路径或命令，例如 `C:\...\chrome.exe` 或 `google-chrome` |
| `OVS_ALLOW_NETWORK` | 设为 `1` 时允许渲染期间联网 |
| `OVS_NO_SANDBOX` | 设为 `1` 时强制关闭浏览器沙箱（仅容器/CI） |
| `OVS_DEBUG` | 设为 `1` 时显示完整错误信息 |
| `OVS_PIP_INDEX` | 自定义 pip 源；未设置时官方源失败会自动切换清华源 |

## 安全

- 默认禁止 Headless Chrome/Edge 联网：模板不含远程资源，渲染可信本地 HTML 时不会外传内容。
- 只渲染你信任的 HTML。默认断网挡的是网络外传，不挡页面脚本在本机的行为；渲染陌生文件前应先查看内容。
- 默认启用浏览器沙箱。脚本会自动探测沙箱可用性，仅在带沙箱无法启动时降级，并在终端显示 WARN。`OVS_NO_SANDBOX=1` 可强制关闭沙箱。
- 临时 HTML、截图和浏览器 profile 位于系统临时目录，脚本会在正常和异常路径下尽力清理；极端退出时可能残留 `%TEMP%\ovs-*`。
- 本包不含遥测、上传、日志回传或远程资源。

## 启用

将本包内容复制到你的 AI 助手 skills 目录（如 `~/.cola/skills/office-visual-spec/`），并同步对应的 skill 入口。

## 许可

MIT License
