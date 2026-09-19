---
name: logic-animation-video
description: 制作中文横屏逻辑谜题动画，统一黑白讲解人物、灰底黄色道具，采用逐字声学对齐、确定性道具模型、统一封面和发布文案；严格分离公开Skill、私有素材、私有进度交接。
---

# 中文逻辑谜题动画制作

## 仓库边界是强制要求
1. 当前公开库只放通用规则、工具、空白配置；不放素材、成片、配音、真实逐字JSON、发布包、任务状态、HANDOFF或历史会话备份。
2. 项目专属素材和重建工程放私有assets库。进度、用户确认、待办、验证证据、任务清单放独立私有agent-progress库。
3. 跨库以repo+commit+path+sha256引用，不反复复制内容，不在任何仓库保存凭据。
4. 每轮按agent-progress-skill读取权威HEAD检查点，工作中和结束时追加新检查点。禁止将“当前进度”追加到本Skill或README。

## 执行顺序
- 读取 `references/repository-boundaries.md` 与 `references/production-standard.md`（含第 9 节解谜短视频结构范式），从统一私有进度库确定任务编号和资产版本。研究指定参考创作者时按 `references/reference-study-playbook.md` 执行，证据只进私有进度库。
- 先校验题设、解法和理想化假设；修改旧题保留编号和原片，不能冒充新题。
- 先测真实旁白时长，使用声学逐字对齐，所有动画、计数和字幕共享事件时间轴。
- 生成精确逻辑对象和多姿态角色；代码绘制文字、计数和公式，生图只承担美术。
- 组件一律图像生成＋抠图透明PNG，严禁代码手绘组件；仅非常简单元素与精确图示可代码绘制（见references/production-standard.md §7）。
- 先检查分镜、边界条件和音画先后，再渲染1080p横屏MP4。技术解码不等于逻辑或人工听感验收。
- 每期交付视频、统一封面、SRT、逐字时间数据、标题简介、关键词/话题、置顶评论建议。发布包只装发布素材；制作方法留Skill，进度证据留agent-progress。
- 按授权提交对应仓库并核验远程可见性、commit和hash；未获授权不代发平台。先验证备份，再清理本地重复物；128MB工作区按需恢复。

## 工具入口
- `tools/episode.py`：参数化角色、声学字幕显示、音效/底乐和成片拼接，输入实际项目目录。
- `tools/video_core.py`：通用二维绘制，不含角色图片或某集数据。
- `tools/align_characters.py`：根据准确原稿和干净音频做字符声学对齐，结果存入指定私有项目目录。
- `tools/validate_video.py`：编码、尺寸、帧率、完整解码检查；输出应存agent-progress的对应项目证据目录，不提交本库。
- `tools/check_repository_boundary.py`：公开Skill目录白名单和禁止媒体/进度文件检查。
- `tools/study_frames.py`：参考研究用抽帧拼图、亮度时间线、场景切换与响度测量；只处理公开可得文件，输出存私有证据目录。

项目专属渲染脚本属于assets中的项目工程；不能为了“可复现”把整个私有项目拖回公开Skill。

## 进度协议只使用Agent Progress

读取 https://github.com/defidehathorn389-max/agent-progress-skill 的SKILL.md；实际状态从私有agent-progress选择对应project读取HEAD指向的检查点。不要在本库或素材库另写HANDOFF，不再建视频专属进度仓库。CURRENT为派生视图，校验后以HEAD为准。

## 新选题门禁

制作新一期前必须读取进度项目中的catalog/episodes.json与制作清单：比较题名、别名、puzzle_key和核心解法，不只匹配标题。所有已完成、制作中、待审及历史题都参与比较；换道具/人物/数字但关键机制相同仍是重复题。没有访问最新清单不能宣称查重通过。选题后先登记唯一编号、机制和制作状态，再生成，防止中断后重复选题。修订沿用编号与revision。只复用角色、片头片尾和模板，不重做旧题冒充新一期。

新一期先推荐3个通过查重的题目，逐一说明机制区别，等待用户选择后登记占号；仅在用户明确授权自行选题时跳过选择确认。续作说明新增内容，不冒充全新题。

查重之外还要核对私有 catalog 中的 `reference-coverage-*.json`（已研究参考账号的题目机制清单）：同机制题若对方已发布，提案必须写明差异化角度，或优先推荐未覆盖机制。每个提案同时给出 ≤4 字局名与完整问句标题（见 production-standard 第 9 节）。
