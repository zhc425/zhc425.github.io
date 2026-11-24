# 账号星图 Atlas · 官方网站

<p>
  <a href="https://zhc425.github.io/"><b>https://zhc425.github.io</b></a>
</p>

这是开源项目 [账号星图 Atlas](https://github.com/Ckxkx/account-atlas) 的官方站点源码。Atlas 帮你记清每个邮箱、手机号注册 / 绑定了哪些网站和 App，网页、iOS、安卓三端可用，永久免费。

## 站点页面

| 页面 | 地址 | 内容 |
|---|---|---|
| 首页 | [/](https://zhc425.github.io/) | 项目介绍、三端下载、功能演示 |
| 安装指南 | [/guide/](https://zhc425.github.io/guide/) | 安卓 APK 与 iPhone（网页版 / IPA 自签）图解安装 |
| SideStore 续签 | [/sidestore/](https://zhc425.github.io/sidestore/) | 用 SideStore 安装 IPA 并在手机上自动续签 |
| 常见问题 | [/faq/](https://zhc425.github.io/faq/) | 安装、签名、续签、数据备份 |

## 下载

<!-- downloads:start -->
- 蓝奏云网盘（v2.3.1）：安卓 <https://wwbsj.lanzoup.com/iFq7G4h6uxxe> · iPhone <https://wwbsj.lanzoup.com/iHNrU4h6uy2j> · 密码 **0874**
- GitHub Releases：<https://github.com/Ckxkx/account-atlas/releases/latest>
<!-- downloads:end -->
- 网页版：<https://huichen.dev/account-atlas/>

官方安装包只从 GitHub Releases 和 huichen.dev 发布，App 永久免费，任何收费渠道都不是官方的。

## 目录结构

```
index.html            首页
guide/index.html      安装指南
sidestore/index.html  SideStore 续签教程
faq/index.html        常见问题
assets/site-atlas.css 全站样式
assets/atlas/         图标、截图、功能演示
.github/scripts/       发版同步脚本（GitHub 新 Release → 蓝奏云 → 站点链接）
```

纯静态 HTML，推送到 `main` 后由 GitHub Actions 自动部署到 GitHub Pages。

## 发版自动同步

`.github/workflows/sync-release.yml` 每 15 分钟检查一次 [Ckxkx/account-atlas](https://github.com/Ckxkx/account-atlas) 的最新 Release，发现新版本时：

1. 下载 Release 里的 `Atlas.apk` 和 `Atlas.ipa`；
2. 删掉蓝奏云「Atlas」文件夹里的旧安装包，上传新包，取得分享链接；
3. 更新站点上的版本号、安装包大小和蓝奏云链接，提交并重新部署。

需要的仓库 Secrets：`LANZOU_YLOGIN`、`LANZOU_PHPDISK_INFO`（蓝奏云登录 Cookie）。可选 Variable：`LANZOU_FOLDER_ID`（不填则自动使用 / 创建名为 Atlas 的文件夹）。在 Actions 页手动运行并勾选 force 可强制重新同步。

## 反馈

问题和建议请提到 Atlas 仓库的 [Issues](https://github.com/Ckxkx/account-atlas/issues)，或加入 QQ 交流群：1063129927。

© 2026 Ckxkx（阿chen）
