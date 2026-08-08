# 二级索引：输出类型与读取路由

本文件是 office-visual-spec 的二级索引。主 `SKILL.md` 只负责入口、工作流和硬规则；到这里选择当前输出类型要读的文件。

## 使用顺序

1. 主 `SKILL.md` 已给出入口和提问规则。
2. 读本文件，按输出类型查路由表。
3. 只读当前类型对应的 reference；需要模块或导出时，再读对应的共享文件。
4. 模糊请求先读 `references/confirmation.md`，确认后再回到本索引。

## 输出类型路由表

| 输出类型 | 只读 | 模板 | vw/vh 基准 |
| --- | --- | --- | --- |
| A4 摘要 | `references/a4-summary.md` | `templates/a4-summary.html` | 1vw=7.94 / 1vh=11.23 |
| HTML PPT（静态截图） | `references/html-ppt.md` | `templates/ppt-16-9.html` | 1vw=12.8 / 1vh=7.2 |
| HTML 页面 | `references/html-page.md` | `templates/html-page.html` | 不强制 |
| 交互式网页 PPT | `references/ppt-web.md` | `templates/ppt-web.html` | 1vw=12.8 / 1vh=7.2 |
| 小红书卡片系列 | `references/xhs-cards.md` | `templates/xhs-cards.html` | 1vw=10.8 / 1vh=14.4 |
| 手机长图 / 连续长文 | `references/mobile-long.md` | `templates/mobile-long.html` | 1vw=10.8 |
| 信息图 | `references/infographic.md` | `templates/infographic.html` | 1vw=10.8 / 1vh=12.15 |

## 共享文件

| 场景 | 读取 |
| --- | --- |
| 请求不明确 | `references/confirmation.md` |
| 组合美化模块 / 功能区映射 / vw-vh 基准 | `references/modules.md` |
| 导出 PNG / PDF / 图片集 | `references/render.md` |
| 风格颜色调整 | `references/style-adjustment.md` |

## 读取规则

- 类型文件自包含：字体、颜色、组件、布局、自检都在文件内。
- 模块组装时最多再读一个共享文件：`references/modules.md`。
- 导出前必须按 `references/render.md` 标准管线，不临场发明参数。
- 固定画布类型用 `vw` / `vh` 直接排版；自然高度类型用固定 px 或 `vw`。
- 分页、打印、文字可复制等硬规则见主 `SKILL.md`，不允许被类型文件覆盖。

## 包内文件索引

```text
SKILL.md                      # 主入口：提问、工作流、硬规则
references/README.md          # 本文件：二级索引
references/confirmation.md    # 模糊请求傻瓜式确认
references/a4-summary.md      # A4 摘要
references/html-ppt.md        # HTML PPT（静态截图）
references/html-page.md       # HTML 页面
references/ppt-web.md         # 交互式网页 PPT
references/xhs-cards.md       # 小红书卡片系列
references/mobile-long.md     # 手机长图 / 连续长文
references/infographic.md     # 信息图
references/modules.md         # 美化模块库 + vw/vh 基准 + 功能区映射
references/render.md          # 渲染与导出契约
references/style-adjustment.md# 风格调整流程
templates/                    # 各类型模板
scripts/                      # 自检与标准渲染管线
examples/                     # 参考样本
TEST-NOTES.md                 # 验收清单（回归检查用）
```
