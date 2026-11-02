# Partitur

[English](README.md)

Partitur 是乐曲的总谱：每个声部都写在其中，演奏者各自照谱演奏。
演奏者可以更换，乐谱始终保留。

Partitur 是一种由一位用户和多个 AI 代理会话共同开展软件项目的方法，
支持 Claude Code、Codex，或两者同时使用。它为每个会话分配角色，
将会话需要的信息保存在文件和 Git 中，而不是留在对话里；
任何改动都必须经过审查和用户决定，才能进入主分支。
任何会话都可以随时结束，接替的会话根据记录继续工作。

它提炼自一个真实科研软件项目（“来源项目”）的工作实践，
并持续记录哪些规则已经在该项目中实际使用过。

## 原则

其余安排都由以下六个理念决定；有疑问时，先判断适用哪一条。

1. **由你决定。** 会话负责讨论、提案和审查；只有你说出 `AtE`
   （approval to execute，批准执行）后，才可以写入。
   如果希望会话仅在同意方案时执行，就使用 `AtEiYA`（AtE if you agree）。
   执行 `/ptt-*` 命令表示你批准该命令自身的记录操作，不代表其他授权；
   执行你已经看过的草稿时除外。
2. **先领取角色，再开展工作。** 会话可以是设计者、集成者，或某个任务的持有者，
   但必须通过命令领取后才具备这一身份。已经有人持有的角色不能再被领取。
3. **依靠记录，而非记忆。** 重要信息保存在记录库的文件中，
   因此会话随时可以清空上下文或被替换，后续会话根据记录继续工作。
4. **审查给出建议，由你作出决定。** 代码只能通过请求进入主分支：
   集成者审查，你作出决定，合并前先记录决定。
5. **上级对下级的工作负责。** 设计者监督自己创建的任务；
   持有者只有得到上级批准才能离任；下级仍有事项等待处理时，上级不能离任；
   上级应留意失去响应的持有者，并释放其任务。
6. **用标签说明确定程度。** 决策标记为 Agreed（已达成共识）、Proposed（提议中）
   或 Open（待定）；证据标记为 Source（来自源代码）、Inferred（推断）、
   Tested（已测试）或 Unknown（未知）。Partitur 自身的每条规则也会注明
   是否经过实践，见[规则索引](rules.md)。

## 什么时候用哪个命令

| 你想要…… | 在哪个会话中 | 命令 |
| --- | --- | --- |
| 开始或接手设计工作 | 任意空闲会话 | `/ptt-take designer` |
| 将讨论形成任务 | 设计者 | `/ptt-mktask`，然后 `/ptt-mktask release N` |
| 让会话承担一个任务 | 任意空闲会话 | `/ptt-take N`（也可以使用任务名称） |
| 查看会话的身份 | 任意会话 | `/ptt-whoami`；查看所有人用 `/ptt-whoami all` |
| 查看与会话有关的新记录及待办事项 | 任意持有者 | `/ptt-inbox`（启用提示词钩子后，也会随你的下一条消息送达） |
| 在 `/clear` 后或新会话中继续持有原角色 | 继续工作的会话 | `/ptt-resume`（接续在安静点留下交接标记的持有者；否则指定名字） |
| 提交已完成的工作供审查 | 任务持有者 | `/ptt-pr-submit` |
| 回复审查意见 | 任务持有者 | 先用 `/ptt-pr-draft-reply` 查看修改计划和回复全文，再用 `/ptt-pr-reply` 发布（提交前同样可以先用 `/ptt-pr-submit draft`） |
| 审查并执行你的决定 | 集成者（通过 `/ptt-take integrator` 领取） | `/ptt-pr-review` |
| 报告任务完成／验收任务 | 持有者／其上级 | `/ptt-done` / `/ptt-close N` |
| 不再持有角色或任务 | 持有它的会话 | `/ptt-leave`（任务需要上级执行 `/ptt-leave approve N` 批准） |
| 清理已合并的分支 | 集成者 | `/ptt-pr-cleanup` |

在 Codex 中，命令以 `$` 开头，而不是 `/`。表格未覆盖的内容可以直接问会话：
它会阅读 Partitur 的文档并解释，例如“如何退出一个任务？”或“集成者做什么？”。

## 开始使用

环境要求：Git 2.28 或更高版本、Python 3.8 或更高版本，以及支持符号链接的系统
（Linux 或 macOS；Windows 上使用 WSL）；安装 Claude Code、Codex，或两者。

1. **为项目安装。** 在项目的工作区根目录（存放项目各代码检出目录的目录）
   启动一个会话，称为*安装会话*，然后说：“从
   https://github.com/QiaoLei-88/Partitur 为这个项目安装 Partitur”。
   会话会把 Partitur 克隆到一个长期保留的位置（默认 `~/partitur`，也可以由你指定），
   先告诉你将要运行的命令，然后运行：

   ```
   ~/partitur/bin/install --scope project
   ```

   你也可以自己克隆并运行这条命令（在 Claude Code 会话中执行
   `! ~/partitur/bin/install --scope project`，让会话看到输出）。
   安装器会检测 Claude Code 和 Codex（可以用 `--tool claude`、`codex` 或 `all`
   明确选择），并报告创建的内容：
   记录库 `workspace/`，其中包含规则文件 `PROJECT-RULES.md`、任务与请求目录、工具和技能，
   根设计任务 `T0000`（设计者的章程和交接记录）、集成者文件、
   供代理工具读取的链接，以及向每个会话显示其新消息的提示词钩子
   （Claude Code 为 `.claude/settings.json`；Codex 的见下文）。安装器会列出发现的代码仓库；
   更深层目录中的仓库可以在 `workspace/pr/repos` 中添加一行。
   如果你是在普通终端中运行安装命令，则在工作区根目录启动安装会话，并说：
   “阅读 partitur-install-report.md，帮我完成 Partitur 安装”。
   安装器会把输出和后续步骤写入该文件（不提交，完成后删除）。
2. **与安装会话一起填写两个文件**：`workspace/PROJECT-RULES.md` 末尾的
   “Project Rules”（项目规则，填写你的领域规则；Partitur 自身的规则位于上方
   带标记的区块中），以及 `workspace/tasks/open/T0000-design/charter.md`
   中的占位内容。后者是根设计者的章程，仅首次直接填写，此后由你提出修订；
   同目录下的 `status.md` 是设计者的交接记录。
   已有规则文件的项目会保留原文件：安装器报告“not merged”，由会话比较两套规则。
   会话会直接删除重复内容、保留你的领域规则；只有遇到实际冲突时才询问你，
   并就是否采纳 Partitur 规则区块统一询问一次。
   经你批准后，使用 `--merge-rules` 加入规则区块。随后记录这些内容：

   ```
   workspace/bin/ptt record -m "install Partitur" workspace
   ```

   此后，对 `workspace/` 的所有写入都通过 `ptt` 完成。
   安装期间达成共识的设计内容，应在记录前写入 T0000 的章程或 `status.md`。
   然后结束安装会话；它不领取任何角色。
3. **在工作区根目录新开会话**，分别领取角色：一个会话执行
   `/ptt-take designer`，另一个执行 `/ptt-take integrator`。
   每个会话都从记录开始，而不是依靠安装时的对话。
   如果 T0000 尚未填写（例如已有项目的交接材料保存在别处），
   设计者会根据项目现有材料提出填写方案。
   与设计者讨论第一项工作并将其形成任务，然后在第三个会话中用 `/ptt-take`
   领取该任务。请求需要等待有会话持有集成者角色才能处理；
   提交请求时若没有集成者，`ptt` 会提示。

可选：每台机器运行一次 `~/partitur/bin/install --scope user`，
为你的所有会话链接 Partitur，使任意目录中的会话都认识它
（之后在下一个项目中说“为这个项目安装 Partitur”就不再需要链接）。
安装报告会给出这一建议；之后对项目执行 `--update` 时，会移除项目自己的链接。

### 如果你是被要求从这个链接安装 Partitur 的会话

1. 先说明将克隆到哪里、将运行什么，等待用户确认：用户的请求指定了操作，
   位置由用户确认。克隆到长期保留的位置，默认 `~/partitur`：
   项目会通过绝对路径链接到这份克隆，因此不能放在临时目录中。
   如果该位置已存在，请询问：复用它（`git -C <clone> pull`），还是另选位置。
2. 在工作区根目录运行 `<clone>/bin/install --scope project`
   （如果项目还要支持本机未安装的工具，加上 `--tool all`），并报告输出。
3. 阅读 `<clone>/SKILL.md` 中的“Installing Partitur for a project”一节，
   以及工作区根目录中的 `partitur-install-report.md`，与用户一起完成其中的步骤。
4. 以后更新：先 `git -C <clone> pull`，再加 `--update` 运行同一条安装命令。

始终在工作区根目录启动会话：Codex 只读取其启动目录所属 Git 根目录及其下级
目录中的 `AGENTS.md` 和技能，而工作区根目录通常不在 Git 仓库内部。

对于 Codex，安装器还会添加 `.codex/hooks.json`。
请在 Codex 中审阅并信任项目及其钩子（CLI 中使用 `/hooks`）；
在完成之前，或客户端不支持提示词钩子时，手动使用 `$ptt-inbox`。
钩子会从 Codex 事件中读取会话 ID，并在用户发送下一条消息时报告新记录。
它不会唤醒空闲会话。详见[官方钩子文档](https://learn.chatgpt.com/docs/hooks)。
钩子使用工作区的绝对路径，因此会话切换目录后仍能工作；
如果移动了工作区，请更新路径，并重新审阅、信任该钩子。

Codex 的 shell 命令使用 `CODEX_THREAD_ID` 绑定持有者，
不可用时回退到 `CODEX_SESSION_ID`。
Claude Code 继续使用 `CLAUDE_CODE_SESSION_ID`；
`PTT_SESSION_ID` 可以覆盖任一工具提供的值。
新会话或分叉会话只有通过 `$ptt-resume <holder name>` 才能接续原持有者；
此后，原会话会失去通过 `ptt` 写入的权限。
继续同一会话或压缩其上下文不会释放持有者身份。
运行 `$ptt-whoami` 检查绑定，需要时通过 resume 重新加载交接记录。

要将项目升级到新版 Partitur，请拉取本仓库，并在第 1 步的命令中加上
`--update` 后重新运行。项目会在 `workspace/.partitur-version` 中记录
安装时的 Partitur 提交，因此升级会替换过时内容、移除 Partitur 不再提供的内容，
同时保留你的规则、记录和自行修改的文件。
使用 `--force` 可以替换自行修改的文件，但会先将每个文件复制到备份目录。
`--uninstall` 按同样的原则移除已安装内容。
对于用户级链接，`--scope user --uninstall` 会处理检测到的工具；
如果曾为两种工具都安装过，请加上 `--tool all`。

两种工具都将 `partitur` 链接到本仓库，以访问总入口技能及文档。
`project/skills/` 中的命令模板名为 `SKILL.md.in`；
安装器填入记录库目录名后，为项目生成 `SKILL.md`。
模板本身不会被发现为命令技能。

角色与任务领取、安装命令以及提示词钩子已在源项目中使用；
[规则索引](rules.md)标出了仍为 *Proposed（提议中）* 的规则，
例如释放长期无记录的持有者，或子设计范围。

## 内容索引

- [模型](model.md)：概念、不变量、范围与嵌套、信息流。
- 角色：[用户](roles/user.md)、[设计者](roles/designer.md)、
  [专题研究者（track）](roles/track.md)、[工作者](roles/worker.md)、
  [集成者](roles/integrator.md)、[受托者](roles/delegate.md)。
- 流程：[角色与任务](flows/tasks.md)、[授权](flows/authorization.md)、
  [请求](flows/requests.md)、[交接](flows/handoff.md)、[证据](flows/evidence.md)、
  [引用](flows/references.md)。
- [规则索引](rules.md)：每条规则的 ID 和标签：*Exercised（已实践）*
  表示已在来源项目中使用；*Adopted（已采纳）* 表示已写入其规则，但尚无使用记录；
  *Proposed（提议中）* 表示 Partitur 提出的设计，尚未验证。
- [参数](parameters.md)：安装时可以选择什么，以及哪些内容是固定的。
- `bin/install`：需要运行的安装命令（每台机器一次，每个项目一次）。
- `project/`：交付给项目的内容，包括管理角色与任务的 `bin/ptt`、
  管理请求的 `bin/pr`、`bin/test-run`，以及 `ptt-*` 技能。
- `templates/`：安装时填充的文件，包括规则文件、请求 README、
  根设计任务的章程和状态、集成者文件、任务章程。
- [SKILL.md](SKILL.md)：代理会话的入口。
- [贡献指南](CONTRIBUTING.md)；测试命令：
  `python3 -m unittest discover -s tests`。

## Partitur 如何开发

Partitur 与来源项目共同演进，来源项目始终是它的实践检验场：
只有真实使用记录提供了证据，规则才会被标记为 Exercised（已实践）。
每个里程碑都由一个新代理独立审查；它能看到记录，但看不到作者的推理过程。
标签背后的证据和审查结果与开发笔记一起保存，不放在本仓库中。

## 许可证

Partitur 使用 GNU 通用公共许可证，仅限第 2 版
（SPDX：`GPL-2.0-only`）；详见 [LICENSE](LICENSE)。
