# macos-utility-launch · macOS 小工具开发与发布

把原生 Mac 小工具从功能原型推进到可验证、可安装、可发布的状态。

[English](README.md) · [下载最新版](https://github.com/Vtous/macos-utility-launch/releases/latest) · [Skill 入口](skills/macos-utility-launch/SKILL.md)

经验来自 [OtterMate（水獭助手）](https://github.com/Vtous/OtterMate) 的实际开发，重点保留图标小尺寸故障、配置保留、真实交互验证与公开发布中的具体经验。

## 包含内容

- 简短入口：按当前任务选择阶段，避免每次重复整套流程。
- 七份按需参考：需求与命名、原生实现与验证、视觉设计、升级与图标排障、发布与隐私、脚本说明、已脱敏的 OtterMate 案例。
- 三个可执行工具：完整 ICNS 生成、已签名 App 打包与解包复验、按清单检查和整理公开源码。
- 两份示例：产品身份/验证规格与公开文件清单。

命名和造型保留创作空间；不强制所有项目使用水獭、特定架构或固定权限。苹果公证与订阅支付只整理了后续接入范围，没有声称提供现成系统。

1.0.1 流程更新优先使用已连接的 GitHub 插件与官方 GitHub CLI，在后台创建仓库、更新源码和上传发行附件，并涵盖账号/凭据存储检查、草稿上传、远端校验及中断恢复。网页自动操作作为后备，账号授权仍由用户确认；项目选择 GitHub 作为发布渠道时再使用这部分流程。

## 安装和调用

将 **`skills/macos-utility-launch` 这一层目录**复制到 Codex 用户技能目录，通常为 `~/.codex/skills/`；如配置了 `CODEX_HOME`，则使用其下的 `skills`。不要把整个仓库根目录当成 skill 安装；已有同名 skill 时先保留旧版本再更新。

新安装的 skill 可能需要新建会话或刷新技能后才被识别。调用示例：

```text
使用 $macos-utility-launch 完成这款 Mac 小工具的当前开发阶段，
包括实际验收、App 与菜单栏图标，以及中英文发布资料。
```

也可以只要求某一阶段，例如“修复登录项小图标”或“改名但保留旧配置”。采用正常的自动发现默认值；调用 skill 不会自动取得公开发布或额外系统权限的授权。

## 运行检查

```sh
python3 -m unittest discover -s tests -v
```

脚本需要 Python 3.9+ 标准库。图标与 App 打包依赖 macOS 的苹果系统工具；公开文件整理可跨平台执行。测试使用临时文件与专用签名样例，不启动应用、不更改登录项、不使用个人配置、不上传代码。

具体参数与适用边界见 [脚本说明](skills/macos-utility-launch/references/script-tools.md)。检查器覆盖有限模式，不代替安全审计；签名完整性不等于公证，单机通过不等于全面兼容。

验证快照（2026-11-01）：在 Apple Silicon、macOS 27.2 上，16 项检查通过，包含苹果图标编码器与原生 ZIP/签名的实际复验。受限执行环境可能需要为 `iconutil` 的系统图像服务提供必要访问。

仓库附带明确的公开文件清单 `public-files.json`，可以先执行只读检查，不上传或复制文件：

```sh
python3 skills/macos-utility-launch/scripts/prepare_public.py --source-root . --manifest public-files.json
```

## 许可证

[MIT](LICENSE)。图标生成流程参考 MIT 开源的 OtterMate，保留版权声明。包内不含苹果开发者凭据、个人输入法规则或专有图像资产。
