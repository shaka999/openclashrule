# openclashrule

OpenClash 订阅转换配置仓库（Clash Meta 内核优化版）

## 文件说明

| 文件 | 用途 |
|------|------|
| ACL4SSR_Online_optimized.ini | **主配置模板（推荐）**：ACL4SSR 在线版 + CDN 优化 |
| clash_base.yaml | 基础配置模板（端口/DNS/TUN/geodata） |
| hf_pt_direct.list / play_direct.list / play_proxy.list / dns_upstream.list | 辅助规则列表 |

## 使用方法（OpenClash 订阅转换）

1. **配置订阅** → 添加订阅
2. 填写：订阅地址（机场链接）、在线订阅转换=开启
3. 订阅转换后端：https://api.asailor.org/sub
4. 订阅转换模板：https://raw.githubusercontent.com/shaka999/openclashrule/main/ACL4SSR_Online_optimized.ini
5. 保存并「更新配置」

## 特性

- 规则集全部走 jsDelivr CDN（国内可访问，拉取稳定）
- AI 分流（Gemini/Copilot/OpenAI/Claude/Perplexity/Poe/Cursor/Mistral/xAI/Google/Meta）
- 游戏平台（Epic/Origin/Sony/Steam/Nintendo/Blizzard/Riot）
- 流媒体（Netflix/Spotify/Discord/YouTube/Google/Facebook/Instagram/TikTok/Twitch）
- 开发工具（GitHub/GitLab/Docker）
- Play 商店优化（页面走代理，APK CDN 直连）
- HuggingFace / PT 站点直连
- 去广告（BanAD + 应用净化）
- GEOIP no-resolve 防 DNS 泄漏
