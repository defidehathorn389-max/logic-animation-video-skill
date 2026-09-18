# Logic Animation Video Skill

仅存通用制作规则、可复用工具与空白配置模板。本库公开，不存视频、图片、音频、实际字幕、发布包、项目清单或进度交接。

- 入口：[SKILL.md](SKILL.md)
- 规范：[references/production-standard.md](references/production-standard.md)
- 三库边界：[references/repository-boundaries.md](references/repository-boundaries.md)
- 工具：`tools/`；空白模板：`templates/`

## 三库协作
- Skill（公开）：本仓库。
- 素材（私有）：[logic-animation-video-assets](https://github.com/defidehathorn389-max/logic-animation-video-assets)。
- 进度交接（私有）：[logic-animation-video-handoff](https://github.com/defidehathorn389-max/logic-animation-video-handoff)。

私有库需用户授权。没有权限时请求授权，不把其内容复制到公开Skill绕过权限。具体哪一期完成、当前选择、待办、提交版本均只读私有交接库。

## 使用
安装requirements.txt；重新做声学对齐另安装requirements-alignment.txt。中文字体选Noto Sans CJK SC并验证face。
将本库与私有素材库放在同一父目录；项目源文件可设置环境变量 `LOGIC_VIDEO_SKILL_ROOT` 指向本库，再导入本库tools。不将项目原素材复制到这里。

运行前先读取交接库的当前任务，按资产清单下载所需文件；完成后素材回素材库、进度和验证证据回交接库，只有可复用规则改动才提交本库。
