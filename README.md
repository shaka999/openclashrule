# openclashrule

OpenClash 订阅转换配置仓库（Clash Meta 内核优化版）

## 📁 文件说明

| 文件 | 用途 |
|------|------|
| `openclash-optimized.ini` | **主配置（推荐）**：综合优化版订阅转换模板 |
| `clash_base.yaml` | 基础配置模板（端口/DNS/TUN/geodata），供 OpenClash 覆写或手动合并 |
| `ACL4SSR_Online_optimized.ini` | ~~旧版配置~~（已删除，请使用 `openclash-optimized.ini`） |

## 🚀 使用方法（OpenClash）

1. **OpenClash → 覆写设置 → 配置覆写**，勾选「启用自定义配置」
2. 在「订阅转换模板」处填写/选择 `openclash-optimized.ini` 的内容，或直接在配置覆写中粘贴
3. 将 `clash_base.yaml` 的内容粘贴到 OpenClash 的「DNS/基础配置」覆写中（注意端口避免与路由其他服务冲突）
4. 保存后重启 OpenClash，在面板中按需选择各应用策略组

> 提示：仓库为私有仓库，远程引用 raw 链接会 404，因此所有辅助规则已**内联**进主配置文件，无需额外引用 list 文件。

## ✨ 特性

- 🧹 **节点清洗**：自动剔除机场展示 / 流量提示 / 防失联 / TG 群等杂项节点
- 🗺️ **两层策略组**：五区 url-test 测速组（HK/TW/JP/SG/US）→ 各应用 select 组
- 🧊 **冷门节点池**：负向正则排除五大区，冷门节点单独成组可选
- 🔒 **防泄漏**：全链路 `no-resolve` + https 测速 + 私网直连保护
- 📡 **稳定规则源**：GEOSITE/GEOIP 本地库为主，Aethersailor 补丁走 jsdelivr CDN（国内可访问）
- 🚫 **广告拦截**：`category-ads-all` 本地库拦截
- 🖥️ **应用分流**：Notion / ChatGPT / AI / Telegram / YouTube / Netflix / TikTok / GitHub / Steam / 交易所 / Adobe（可一键 REJECT 禁止联网）等
- 🛒 **Play 商店优化**：页面走代理，APK 下载 CDN 走国内直连
- 🤗 **HuggingFace / PT 直连**：HF CDN 与 PT 站点直连加速
