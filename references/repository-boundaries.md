# 仓库边界与跨库恢复

| 类型 | 归属 | 可见性 |
|---|---|---|
| 制作原则、通用绘制/对齐/编码/校验工具、空白schema | skill | 公开 |
| 人物、视频、音频、封面、字幕、真实对齐数据、每期文案 | assets | 私有 |
| 特定项目渲染脚本、具体数字模型、重建输入配置、素材hash清单 | assets | 私有 |
| 用户决定、当前任务、待办、版本采用状态、完成记录、QA结果 | agent-progress | 私有 |
| 凭据、认证配置 | 不进任何仓库 | 临时授权 |

## 写入流程
1. 先查私有agent-progress的任务与源资产版本。
2. 从assets按路径和hash读取素材，结果回assets，通用规则变更才进skill。
3. 在agent-progress记录assets/skill各自的commit、path、sha256，不嵌入整支视频或复制Skill正文。
4. 写入前扫描提交和ZIP：skill禁止媒体与状态文件；发布ZIP禁止交接、QA报告和制作规范。
5. 上传后验证两个私有库仍为private、skill仍为public，并核验远程对象。
6. 确認备份成功后清理本地重复件，保留当前需要的文件与无凭据恢复索引。

可执行模板中的repo URL可以指向实际仓库，但不得记录当前项目路径、用户确认结果、运行日志或令牌。没有私有库授权时不得声称已读取其中进度。

## ASSET-MANIFEST 生成注意（2026-09-20 发现）
- 用 `git ls-files` 列文件时必须 `git -c core.quotepath=off ls-files -z`（或 `git ls-tree -r -z`），否则中文文件名会被写成带引号的八进制转义键（如 `"episodes/LOGIC-017/r1/\346\226\207\346\241\210…md"`），与远端树对不上；当前 manifest 里有 9 个这样的键和 1 个陈旧 blob（LOGIC-016/r4/发布文案.md）。
- 生成后立即用 GitHub trees API（`git/trees/<sha>?recursive=1`）核对：manifest 键 ⊆ 远端 blob 路径、blob sha 相等；不一致就重生成，不要手改单条。
- 写入 manifest 的 sha 用 git blob id 与 sha256 二选一要写明字段名，不能混用。
