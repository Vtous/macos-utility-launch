# 安装包、公开源码与 GitHub

## 先确定交付状态

区分本机可运行、可下载分发、Developer ID 签名、苹果公证、跨机实测。功能完成也可能尚未具备理想的公开安装体验，应在下载处如实写明。

`package_app.py` 接收已完成签名的 App，不负责编译、重签或公证。它会临时复制并验证，生成 ZIP 后解包再验证，比较文件内容和符号链接，最后写 SHA-256。输出目录须新建，避免覆盖已发布产物。

不要对原安装应用递归清除隔离属性；不要指导用户全局关闭 Gatekeeper。涉及系统阻止打开时，先解释实际签名状态，再参考当前苹果官方的可信应用处理方式。

## 公开文件清单

准备清单只包含实际需要的源码、构建资源、测试、脚本、许可证和文档。`prepare_public.py` 使用明确相对文件名，不展开整个目录；详见 [脚本说明](script-tools.md)。

常见需要排除的内容：日常规则、导入导出、测试证据、应用/配置备份、编译缓存、私钥、环境文件、访问令牌和私人路径。公开的示例配置使用虚构内容，并明显区分于日常配置。

本地完整排障记录与公开验证范围分别维护。脚本不检查二进制内部秘密、图片上的私人内容或 Git 历史；这些必须另行审阅。扫描发现时只输出文件和问题类型，不把秘密正文写到终端或日志。

已有仓库也检查历史和提交身份，不能只看当前目录。根据用户选择设置发布作者与邮箱；GitHub 隐私邮箱是一种选择，不擅自改变全局 Git 配置。开发者证书是公开签名身份；不要承诺站外分发可以隐藏个人开发者姓名。

## 许可证与资源来源

公开可见不等于默认采用 MIT。沿用已有有效许可证和用户选择；没有决定时在发布前明确许可方式。保留复制代码、字体和素材所需的授权与版权声明。仓库可用性检查不能替代商标或版权审查。

## GitHub 信息结构

按项目选择发布渠道。GitHub 适合源码协作与站外下载；这一节在用户选择 GitHub 时执行，不因开发了 macOS 软件就自动公开项目。

- **Repositories** 放项目源码与文档。
- **Releases** 放版本说明、可下载安装包、校验和。用户通常从这里下载。
- Projects 用于任务规划；Packages 适用于相应软件包或镜像，不为普通 ZIP 建立无用发布流程。

先发现当前可用的 GitHub 连接器，能完成的操作优先用连接器。缺少创建仓库、修改仓库介绍或上传本地发行附件时，优先检查 GitHub 官方 CLI（`gh`），用后台命令补齐；不要立即切到浏览器。工具可能在默认 PATH，也可能在 `~/.local/bin/gh`。不要从浏览器提取 token，也不要把某次工具缺少功能、某台电脑没有 CLI 当成永久条件。

用户已要求公开发布时，可在内容准备、审阅和验证后执行。用户只要求“准备好，下次发布”时，交付干净材料并停止在本地。创建仓库不等于源码与附件都发布完成。

## 后台发布路径

先用 `gh --version` 和 `gh auth status --hostname github.com` 检查环境。不要输出 `gh auth token`，不要把凭据放入项目配置、参数、终端日志或 skill。现有插件的授权不等于 CLI 已登录。

CLI 尚未安装时，先确认主机架构和已有安装方式。按 GitHub 官方安装指引使用现有包管理器，或从 `cli/cli` 官方 Releases 获取适配的安装包，核对官方校验和/digest 后安装到用户目录。不要为装一个 CLI 强制增加整套包管理器或开发新的 GUI。核对新登录 shell 中的 PATH；当前代理会话若仍使用旧的环境快照，可先使用已核实的绝对路径。安装、登录、可读和可写是不同状态，分别验证后再报告。

需要登录时，让用户在 GitHub 官方授权页面完成一次登录与权限确认；无需代理控制 Chrome。CLI OAuth 权限可能包含 `repo`、`read:org`、`gist`、`workflow`，以当时授权页面和 `gh auth status` 为准。其中 `repo` 可读写公开及私有仓库，须向用户解释实际授权范围。用户不希望授予默认范围时，可另按当前 GitHub 文档设计受限凭据方案，不擅自扩大授权。正常凭据应进入系统凭据存储；登录后检查实际存储位置，不默认接受明文回退。

在 macOS 上，如需避免 CLI 自动打开用户的浏览器，可只为这次登录设置浏览器命令：

```sh
GH_BROWSER=/usr/bin/true gh auth login --hostname github.com --git-protocol https --web --skip-ssh-key
```

这不会跳过 GitHub 授权。CLI 给出官方设备授权地址与一次性代码后，继续其等待流程，让用户在自己的浏览器确认 GitHub CLI 的权限；不代点授权，不让用户把密码或长期令牌发到聊天，不把临时代码存入项目文件。登录完成后核对实际账号和凭据存储。先只读检查目标仓库及发行版；未做过写操作时明确说明，不能只凭读成功就声称创建或上传已经实测。

以下示例中的 `OWNER/REPO`、文件路径、版本与提交需替换为本次已审阅值。它们是命令配方，不应未经任务授权自动全部执行。

**新仓库：** 明确名称、账号与可见性。只有新仓库才运行创建命令；插件可以继续在该仓库写入审阅过的源码。

```sh
gh repo create OWNER/REPO --public --add-readme --description "Reviewed bilingual description"
```

若已有干净 Git 工作区，可按实际需要采用 `--source` 和 `--push`。不要把包含私人配置的开发目录直接作为发布源；已有远端仓库时，不重新初始化一段独立历史再强制推送，先取得远端历史并检查差异。

**已有项目更新：** 插件提交文本改动，或在正确的本地 checkout 中用正常 Git 提交/推送。更新前核对远端头、diff 和作者隐私邮箱；不要用 `--force` 解决正常同步问题。

**新版本与附件：** 先生成本地发行说明和 SHA-256，创建草稿，上传文件，核对远端内容后再发布。指定已核对的目标提交，避免并发分支更新导致版本指错源码。

```sh
gh release create v1.2.3 --repo OWNER/REPO --target FULL_COMMIT_SHA \
  --title "Reviewed release title" --notes-file release-notes.md --draft
gh release upload v1.2.3 --repo OWNER/REPO dist/App.zip dist/SHA256SUMS
gh release view v1.2.3 --repo OWNER/REPO --json databaseId,isDraft,targetCommitish,assets
gh api repos/OWNER/REPO/releases/RELEASE_ID
gh release edit v1.2.3 --repo OWNER/REPO --draft=false --latest
```

将示例中的 `RELEASE_ID` 替换为前一步返回的 `databaseId`。草稿使用 CLI 查询或按 release ID 读取；按 tag 的 REST 查询面向已发布版本，不要把它查不到草稿误判为创建失败。草稿检查包括文件名、数量、目标标签/提交、大小及各附件 digest。支持时可使用 `gh release verify-asset`，否则用 API digest 或下载后 SHA-256 对照本地。最后确认草稿状态解除和下载链接可用。

上传中断先读取远端草稿和已存在的附件，恢复缺少的部分，不创建重复版本。不要默认使用 `--clobber`：它会先删旧附件再上传，失败可能丢失原文件。对正式版本优先使用新版本号；更新既有文件需要符合当次授权及平台限制。

仓库介绍、主题和主页可用 `gh repo edit`，不为这些常规操作占用用户浏览器。只有后台工具确实不可用且用户愿意配合时，才采用网页；需要系统文件窗口时先协调短暂的前台使用时段。

官方资料：[创建仓库](https://cli.github.com/manual/gh_repo_create)、[创建发行版](https://cli.github.com/manual/gh_release_create)、[上传附件](https://cli.github.com/manual/gh_release_upload)、[CLI 登录](https://cli.github.com/manual/gh_auth_login)。实际使用前以所安装版本的帮助及当前官方文档为准。

## 中英文发布内容

按读者需要选择双语同页或互相链接的两个 README，至少写清：

- 产品解决什么问题，典型使用例子；
- 已实现功能，使用步骤和暂停/退出方式；
- 架构、构建最低系统目标与实际测试的系统/机型；
- 权限、联网、数据位置与第三方服务的真实边界；
- 签名及公证状态，安装方式、使用限制；
- 构建命令、验证范围、许可证和反馈入口。

Release 给出具体版本、该版内容、下载文件、系统要求和校验和。不要抄入本机用户规则或把文档双语写成应用已完成双语界面。检查 Markdown 渲染，中文冒号附近的粗体必要时加空格，避免符号原样显示。

## 发布完成的证据

核对目标账号、仓库可见性、分支/标签和实际文件；校验远端安装包 digest 与本地产物一致。若平台不提供 digest，下载后核对 SHA-256。确认 Release 不再是草稿、链接可见并且文档图片可加载。

## 公证与付费的后续接入

OtterMate 案例没有实际完成 Developer ID 公证或订阅支付，这些不能作为本 skill 已验证能力宣传。实际接入时查询当前官方资料与支持地区，不预设价格、结算门槛或商户资格。

公证需要检查适用的会员、证书、签名、运行时与票据流程。证书和凭据留在本机安全存储，不进入项目或 skill。参考苹果 [Developer ID](https://developer.apple.com/developer-id/) 和 [公证文档](https://developer.apple.com/documentation/security/notarizing-macos-software-before-distribution)。

GitHub 下载加独立支付，收款由支付服务结算；App Store 内购由苹果按其协议结算。支付渠道选择需结合主体地区和客户地区；自动订阅还需后端验证、续费/取消/退款状态同步与授权策略。这里仅为接入范围提示，不包含现成支付系统。
