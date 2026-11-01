# 脚本使用与边界

以下命令在 skill 目录执行；在其他目录调用时，将脚本路径替换为实际路径。参数中的示例路径是占位示例，执行前使用本次项目位置。所有脚本使用 Python 3.9+ 标准库。

## 1. 生成完整 ICNS

```sh
python3 scripts/make_icons.py /path/to/AppIcon-1024.png /path/to/AppIcon.icns
```

需要 macOS 的 `/usr/bin/sips`、`/usr/bin/iconutil`，不需要额外 Python 包。输入为实际 1024×1024 PNG；输出已存在时默认拒绝，可在有意替换项目资源时使用 `--replace`。不修改源图，不签名或重启任何应用。

先生成十个标准/Retina 文件，再编码、解包核对尺寸。此检查不评判设计美观，也不保证系统列表已经更新。某些受限执行环境可能不能调用图像服务；遇到该情况按工具机制申请必要执行权限，不要把服务权限错误当成图标素材损坏。

## 2. 打包并解包复验 App

```sh
python3 scripts/package_app.py /path/to/ExampleMate.app \
  --output-dir /path/to/new-release \
  --archive-name ExampleMate-macOS-arm64.zip
```

需要 macOS 的 `codesign`、`ditto`、`lipo`；已有完整 App 和有效签名。可使用 ad-hoc 或证书签名，但工具不提供签名、升级安装或公证服务。不会启动 App 或修改源应用。

输出目录必须不存在。工具会验证原包、临时副本与解包副本，比较普通文件内容、权限和符号链接；不把外部扩展属性或资源叉列为受支持的发布内容，若复制后签名失效会停止。外指或循环符号链接、特殊设备文件会拒绝。复杂安装器、PKG、DMG 和需要额外分发处理的应用不由此工具覆盖。

输出：

- 指定名称的 ZIP；
- `SHA256SUMS`，可用 `shasum -a 256 -c SHA256SUMS` 核对；
- `package-report.json`，包含架构、声明的最低系统、版本、签名类别与检查范围，不包含原应用绝对路径。

最低系统取自 Info.plist，不能替代检查 Mach-O 的实际部署目标。`notarization: not-checked` 是默认状态，不能据此判断已公证或未公证。

如果需要验证应用已经附带的公证票据，显式增加 `--validate-stapled-ticket`；原包与副本都要通过 `xcrun stapler validate`。不要对尚未附票的 App 使用该选项，也不要把通过票据验证写成全面安全审计。

原签名或架构检查失败时先排查原应用。工具不提供跳过校验、递归重签或移除隔离属性的开关。

## 3. 整理公开源码

根据实际项目建立 JSON 清单，格式见 `../assets/public-files.example.json`。`files` 只接受明确的相对文件名，不展开目录或通配符，拒绝链接、路径越界、重复/大小写冲突，以及常见构建目录、密钥和私人规则文件。

先检查，不复制：

```sh
python3 scripts/prepare_public.py \
  --source-root /path/to/project \
  --manifest /path/to/public-files.json
```

核对报告后整理到一个新目录：

```sh
python3 scripts/prepare_public.py \
  --source-root /path/to/project \
  --manifest /path/to/public-files.json \
  --output-dir /path/to/new-public-source
```

检查规则为有限的启发式：部分令牌、私钥标记与凭据赋值属于 `error`；个人主目录路径、普通邮箱、不能扫描内容的二进制或大文件属于 `review`。报告只给位置/类别，不打印命中正文。GitHub 隐私邮箱不作为普通邮箱告警。

`review` 经人工核对确实适合公开后，可以加 `--allow-reviewed-findings`；这不会绕过 `error`。需要公开的图片与二进制资源一般会有 review 提示。不要通过该参数批量放行尚未检查的内容。

退出码：`0` 表示所请求检查/整理完成；`2` 表示发现未处理问题、未整理；`1` 表示参数、路径、文件格式或系统错误。失败时不改源文件；检查阻止时不创建公开目录。

它不是安全审计工具，可能漏报或误报。不读取二进制内部、图片上的信息、Git 历史或账号设置；也不检查商标/许可证是否合法。不会运行所选文件、调用网络或自动发布。
