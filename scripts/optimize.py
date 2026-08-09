#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
把订阅转换得到的原始 Clash 配置，精简成"自建节点 + RULE-SET 规则"的优化版。

用法:
    python scripts/optimize.py 原始配置.yaml [输出路径]

做的事情:
- 只保留自建节点（server 属于 fq.146916.xyz / rn.146916.xyz）
- 去掉节点名里的流量后缀（|xxx）和多余空格（hysteria- Cloudcone -> hysteria-Cloudcone）
- 重建 15 个代理组（与 ACL4SSR_Online_optimized.ini 一致）
- 头部固定为：allow-lan false、控制端 10.0.0.1:9090、DNS(fake-ip) + sniffer + TUN
- 规则改为远程 rule-providers，附带 HuggingFace / PT 直连等自定义规则
"""

import re
import sys

import yaml

KEEP_SERVERS = {"fq.146916.xyz", "rn.146916.xyz"}


class _Dumper(yaml.SafeDumper):
    """让列表项带缩进（- name: 而不是顶格的 - name:），排版更贴近原文件。"""

    def increase_indent(self, flow=False, indentless=False):
        return super().increase_indent(flow, False)


HEADER = """\
port: 7890
socks-port: 7891
allow-lan: false
mode: Rule
log-level: info
external-controller: 10.0.0.1:9090
unified-delay: true
dns:
    enable: true
    ipv6: false
    enhanced-mode: fake-ip
    fake-ip-range: 198.18.0.1/16
    use-hosts: true
    respect-rules: true
    default-nameserver: [223.5.5.5, 119.29.29.29, 114.114.114.114]
    proxy-server-nameserver: [127.0.0.1:5353]
    nameserver: [223.5.5.5, 119.29.29.29, 114.114.114.114]
    nameserver-policy:
      'geosite:cn': [223.5.5.5, 119.29.29.29, 114.114.114.114]
      'geosite:private': [223.5.5.5, 119.29.29.29, 114.114.114.114]
    fallback: [tls://1.1.1.1:853, tls://8.8.8.8:853]
    fallback-filter: { geoip: true, geoip-code: CN, geosite: [gfw], ipcidr: [240.0.0.0/4], domain: [+.google.com, +.facebook.com, +.youtube.com] }
sniffer:
    enable: true
    sniff: { TLS: { ports: [443], override-destination: true }, HTTP: { ports: [80], override-destination: true } }
    skip-domain: ['Mijia Cloud', dlg.io.mi.com]
    parse-pure-ip: false
tun:
  enable: true   # TUN 模式已开启；不支持代理的 App 也会走规则
  stack: system
  dns-hijack:
    - 0.0.0.0:53
  auto-route: true
  auto-detect-interface: true

proxies:
"""

# 规则集（rule-providers），与 ACL4SSR_Online_optimized.ini 的 ruleset 一一对应
PROVIDERS = [
    ("acl4ssr-lan", "https://cdn.jsdelivr.net/gh/ACL4SSR/ACL4SSR@master/Clash/LocalAreaNetwork.list"),
    ("acl4ssr-unban", "https://cdn.jsdelivr.net/gh/ACL4SSR/ACL4SSR@master/Clash/UnBan.list"),
    ("acl4ssr-banad", "https://cdn.jsdelivr.net/gh/ACL4SSR/ACL4SSR@master/Clash/BanAD.list"),
    ("acl4ssr-banprogad", "https://cdn.jsdelivr.net/gh/ACL4SSR/ACL4SSR@master/Clash/BanProgramAD.list"),
    ("china-media", "https://cdn.jsdelivr.net/gh/blackmatrix7/ios_rule_script@master/rule/Clash/ChinaMedia/ChinaMedia.list"),
    ("google-fcm", "https://cdn.jsdelivr.net/gh/ACL4SSR/ACL4SSR@master/Clash/Ruleset/GoogleFCM.list"),
    ("ai-gemini", "https://cdn.jsdelivr.net/gh/blackmatrix7/ios_rule_script@master/rule/Clash/Gemini/Gemini.list"),
    ("ai-copilot", "https://cdn.jsdelivr.net/gh/VPSDance/ai-proxy-rules@main/rules/loon/copilot.list"),
    ("ai-openai", "https://cdn.jsdelivr.net/gh/blackmatrix7/ios_rule_script@master/rule/Clash/OpenAI/OpenAI.list"),
    ("ai-anthropic", "https://cdn.jsdelivr.net/gh/blackmatrix7/ios_rule_script@master/rule/Clash/Anthropic/Anthropic.list"),
    ("ai-perplexity", "https://cdn.jsdelivr.net/gh/VPSDance/ai-proxy-rules@main/rules/loon/perplexity.list"),
    ("ai-poe", "https://cdn.jsdelivr.net/gh/VPSDance/ai-proxy-rules@main/rules/loon/poe.list"),
    ("ai-cursor", "https://cdn.jsdelivr.net/gh/VPSDance/ai-proxy-rules@main/rules/loon/cursor.list"),
    ("ai-mistral", "https://cdn.jsdelivr.net/gh/VPSDance/ai-proxy-rules@main/rules/loon/mistral-ai.list"),
    ("ai-xai", "https://cdn.jsdelivr.net/gh/VPSDance/ai-proxy-rules@main/rules/loon/x-ai.list"),
    ("ai-google", "https://cdn.jsdelivr.net/gh/VPSDance/ai-proxy-rules@main/rules/loon/google-ai.list"),
    ("ai-meta", "https://cdn.jsdelivr.net/gh/VPSDance/ai-proxy-rules@main/rules/loon/meta-ai.list"),
    ("google-cn", "https://cdn.jsdelivr.net/gh/ACL4SSR/ACL4SSR@master/Clash/GoogleCN.list"),
    ("steam-cn", "https://cdn.jsdelivr.net/gh/ACL4SSR/ACL4SSR@master/Clash/Ruleset/SteamCN.list"),
    ("china-domain", "https://cdn.jsdelivr.net/gh/ACL4SSR/ACL4SSR@master/Clash/ChinaDomain.list"),
    ("china-company-ip", "https://cdn.jsdelivr.net/gh/ACL4SSR/ACL4SSR@master/Clash/ChinaCompanyIp.list"),
    ("microsoft", "https://cdn.jsdelivr.net/gh/ACL4SSR/ACL4SSR@master/Clash/Microsoft.list"),
    ("apple", "https://cdn.jsdelivr.net/gh/ACL4SSR/ACL4SSR@master/Clash/Apple.list"),
    ("telegram", "https://cdn.jsdelivr.net/gh/ACL4SSR/ACL4SSR@master/Clash/Telegram.list"),
    ("game-epic", "https://cdn.jsdelivr.net/gh/ACL4SSR/ACL4SSR@master/Clash/Ruleset/Epic.list"),
    ("game-origin", "https://cdn.jsdelivr.net/gh/ACL4SSR/ACL4SSR@master/Clash/Ruleset/Origin.list"),
    ("game-sony", "https://cdn.jsdelivr.net/gh/ACL4SSR/ACL4SSR@master/Clash/Ruleset/Sony.list"),
    ("game-steam", "https://cdn.jsdelivr.net/gh/ACL4SSR/ACL4SSR@master/Clash/Ruleset/Steam.list"),
    ("game-nintendo", "https://cdn.jsdelivr.net/gh/ACL4SSR/ACL4SSR@master/Clash/Ruleset/Nintendo.list"),
    ("game-blizzard", "https://cdn.jsdelivr.net/gh/blackmatrix7/ios_rule_script@master/rule/Clash/Blizzard/Blizzard.list"),
    ("game-riot", "https://cdn.jsdelivr.net/gh/blackmatrix7/ios_rule_script@master/rule/Clash/Riot/Riot.list"),
    ("media-proxymedia", "https://cdn.jsdelivr.net/gh/ACL4SSR/ACL4SSR@master/Clash/ProxyMedia.list"),
    ("media-netflix", "https://cdn.jsdelivr.net/gh/blackmatrix7/ios_rule_script@master/rule/Clash/Netflix/Netflix.list"),
    ("media-spotify", "https://cdn.jsdelivr.net/gh/blackmatrix7/ios_rule_script@master/rule/Clash/Spotify/Spotify.list"),
    ("media-discord", "https://cdn.jsdelivr.net/gh/blackmatrix7/ios_rule_script@master/rule/Clash/Discord/Discord.list"),
    ("media-youtube", "https://cdn.jsdelivr.net/gh/blackmatrix7/ios_rule_script@master/rule/Clash/YouTube/YouTube.list"),
    ("media-google", "https://cdn.jsdelivr.net/gh/blackmatrix7/ios_rule_script@master/rule/Clash/Google/Google.list"),
    ("media-facebook", "https://cdn.jsdelivr.net/gh/blackmatrix7/ios_rule_script@master/rule/Clash/Facebook/Facebook.list"),
    ("media-instagram", "https://cdn.jsdelivr.net/gh/blackmatrix7/ios_rule_script@master/rule/Clash/Instagram/Instagram.list"),
    ("media-tiktok", "https://cdn.jsdelivr.net/gh/blackmatrix7/ios_rule_script@master/rule/Clash/TikTok/TikTok.list"),
    ("media-twitch", "https://cdn.jsdelivr.net/gh/blackmatrix7/ios_rule_script@master/rule/Clash/Twitch/Twitch.list"),
    ("proxylite", "https://cdn.jsdelivr.net/gh/ACL4SSR/ACL4SSR@master/Clash/ProxyLite.list"),
    ("dev-github", "https://cdn.jsdelivr.net/gh/blackmatrix7/ios_rule_script@master/rule/Clash/GitHub/GitHub.list"),
    ("dev-gitlab", "https://cdn.jsdelivr.net/gh/blackmatrix7/ios_rule_script@master/rule/Clash/GitLab/GitLab.list"),
    ("dev-docker", "https://cdn.jsdelivr.net/gh/blackmatrix7/ios_rule_script@master/rule/Clash/Docker/Docker.list"),
    ("gfwlist", "https://cdn.jsdelivr.net/gh/ACL4SSR/ACL4SSR@master/Clash/ProxyGFWlist.list"),
]

# 规则（顶部为自定义直连，其余走 RULE-SET）
RULES = [
    "# 自定义直连（HuggingFace / PT）",
    "- DOMAIN-SUFFIX,us.aws.cdn.hf.co,DIRECT",
    "- DOMAIN-SUFFIX,cdn-lfs.huggingface.co,DIRECT",
    "- DOMAIN-SUFFIX,cas-bridge.xethub.hf.co,DIRECT",
    "- DOMAIN-KEYWORD,m-team,DIRECT",
    "- DOMAIN-KEYWORD,pthome,DIRECT",
    "- DOMAIN-KEYWORD,pttime,DIRECT",
    "- DOMAIN-KEYWORD,hdfans,DIRECT",
    "# 基础分流",
    "- RULE-SET,acl4ssr-lan,🎯 全球直连",
    "- RULE-SET,acl4ssr-unban,🎯 全球直连",
    "- RULE-SET,acl4ssr-banad,🛑 全球拦截",
    "- RULE-SET,acl4ssr-banprogad,🍃 应用净化",
    "- RULE-SET,china-media,🎞️ 国内媒体",
    "- RULE-SET,google-fcm,📢 谷歌FCM",
    "# AI 分流（走代理）",
    "- RULE-SET,ai-gemini,🤖 AI",
    "- RULE-SET,ai-copilot,🤖 AI",
    "- RULE-SET,ai-openai,🤖 AI",
    "- RULE-SET,ai-anthropic,🤖 AI",
    "- RULE-SET,ai-perplexity,🤖 AI",
    "- RULE-SET,ai-poe,🤖 AI",
    "- RULE-SET,ai-cursor,🤖 AI",
    "- RULE-SET,ai-mistral,🤖 AI",
    "- RULE-SET,ai-xai,🤖 AI",
    "- RULE-SET,ai-google,🤖 AI",
    "- RULE-SET,ai-meta,🤖 AI",
    "# 国内直连（Play 商店：页面走代理，APK 下载 CDN 走国内直连）",
    "- DOMAIN-SUFFIX,googleusercontent.com,🚀 节点选择",
    "- DOMAIN,android.clients.google.com,🚀 节点选择",
    "- DOMAIN-SUFFIX,play.google.com,🚀 节点选择",
    "- DOMAIN-SUFFIX,dl.google.com,🎯 全球直连",
    "- DOMAIN-SUFFIX,xn--ngstr-lra8j.com,🎯 全球直连",
    "- DOMAIN-SUFFIX,gvt1.com,🚀 节点选择",
    "- DOMAIN-SUFFIX,gvt2.com,🚀 节点选择",
    "- DOMAIN-SUFFIX,gstatic.com,🚀 节点选择",
    "- RULE-SET,google-cn,🎯 全球直连",
    "- RULE-SET,steam-cn,🎯 全球直连",
    "- RULE-SET,china-domain,🎯 全球直连",
    "- RULE-SET,china-company-ip,🎯 全球直连",
    "# 海外服务",
    "- RULE-SET,microsoft,Ⓜ️ 微软服务",
    "- RULE-SET,apple,🍎 苹果服务",
    "- RULE-SET,telegram,📲 电报信息",
    "- RULE-SET,game-epic,🎮 游戏平台",
    "- RULE-SET,game-origin,🎮 游戏平台",
    "- RULE-SET,game-sony,🎮 游戏平台",
    "- RULE-SET,game-steam,🎮 游戏平台",
    "- RULE-SET,game-nintendo,🎮 游戏平台",
    "- RULE-SET,game-blizzard,🎮 游戏平台",
    "- RULE-SET,game-riot,🎮 游戏平台",
    "- RULE-SET,media-proxymedia,🌍 国外媒体",
    "- RULE-SET,media-netflix,🌍 国外媒体",
    "- RULE-SET,media-spotify,🌍 国外媒体",
    "- RULE-SET,media-discord,🌍 国外媒体",
    "- RULE-SET,media-youtube,🌍 国外媒体",
    "- RULE-SET,media-google,🌍 国外媒体",
    "- RULE-SET,media-facebook,🌍 国外媒体",
    "- RULE-SET,media-instagram,🌍 国外媒体",
    "- RULE-SET,media-tiktok,🌍 国外媒体",
    "- RULE-SET,media-twitch,🌍 国外媒体",
    "- RULE-SET,proxylite,🚀 节点选择",
    "# 开发工具",
    "- RULE-SET,dev-github,🐙 开发工具",
    "- RULE-SET,dev-gitlab,🐙 开发工具",
    "- RULE-SET,dev-docker,🐙 开发工具",
    "# GFW 列表（被墙站点走代理）",
    "- RULE-SET,gfwlist,🚀 节点选择",
    "# IP 段兜底（国内直连）",
    "- GEOIP,PRIVATE,🎯 全球直连",
    "- GEOIP,CN,🎯 全球直连",
    "# 兜底",
    "- MATCH,🐟 漏网之鱼",
]


def normalize_name(name):
    """去掉流量后缀（|xxx）和空格。"""
    name = str(name).split("|", 1)[0]
    return re.sub(r"\s+", "", name)


def build_groups(nodes):
    """按固定结构重建 15 个代理组，节点列表取自当前订阅。"""
    return [
        {"name": "🚀 节点选择", "type": "select", "proxies": ["♻️ 自动选择", "DIRECT"] + nodes},
        {"name": "♻️ 自动选择", "type": "url-test", "url": "http://www.gstatic.com/generate_204", "interval": 300, "tolerance": 50, "proxies": nodes},
        {"name": "🎞️ 国内媒体", "type": "select", "proxies": ["DIRECT", "🚀 节点选择", "♻️ 自动选择"]},
        {"name": "🌍 国外媒体", "type": "select", "proxies": ["🚀 节点选择", "♻️ 自动选择", "🎯 全球直连"] + nodes},
        {"name": "📲 电报信息", "type": "select", "proxies": ["🚀 节点选择", "🎯 全球直连"] + nodes},
        {"name": "Ⓜ️ 微软服务", "type": "select", "proxies": ["🎯 全球直连", "🚀 节点选择"] + nodes},
        {"name": "🍎 苹果服务", "type": "select", "proxies": ["🚀 节点选择", "🎯 全球直连"] + nodes},
        {"name": "📢 谷歌FCM", "type": "select", "proxies": ["🚀 节点选择", "🎯 全球直连", "♻️ 自动选择"] + nodes},
        {"name": "🤖 AI", "type": "select", "proxies": ["🚀 节点选择", "🎯 全球直连", "♻️ 自动选择"] + nodes},
        {"name": "🎮 游戏平台", "type": "select", "proxies": ["🚀 节点选择", "🎯 全球直连", "♻️ 自动选择"] + nodes},
        {"name": "🐙 开发工具", "type": "select", "proxies": ["🚀 节点选择", "♻️ 自动选择", "🎯 全球直连"] + nodes},
        {"name": "🎯 全球直连", "type": "select", "proxies": ["DIRECT", "🚀 节点选择", "♻️ 自动选择"]},
        {"name": "🛑 全球拦截", "type": "select", "proxies": ["REJECT", "DIRECT"]},
        {"name": "🍃 应用净化", "type": "select", "proxies": ["REJECT", "DIRECT"]},
        {"name": "🐟 漏网之鱼", "type": "select", "proxies": ["🚀 节点选择", "🎯 全球直连", "♻️ 自动选择"] + nodes},
    ]


def main():
    if len(sys.argv) < 2:
        raise SystemExit("用法: python scripts/optimize.py 原始配置.yaml [输出路径]")
    src = sys.argv[1]
    dst = sys.argv[2] if len(sys.argv) > 2 else "节点.yaml"

    with open(src, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        raise SystemExit("原始配置解析失败")

    # 只保留自建节点
    proxies, seen = [], set()
    for p in data.get("proxies") or []:
        if p.get("server") not in KEEP_SERVERS:
            continue
        p = dict(p)
        p["name"] = normalize_name(p.get("name", ""))
        if not p["name"] or p["name"] in seen:
            continue
        seen.add(p["name"])
        proxies.append(p)
    if not proxies:
        raise SystemExit("没有找到自建节点（server 需属于 fq.146916.xyz / rn.146916.xyz）")

    nodes = [p["name"] for p in proxies]
    lines = [HEADER.rstrip("\n")]
    for p in proxies:
        flow = yaml.safe_dump(
            p,
            allow_unicode=True,
            sort_keys=False,
            default_flow_style=True,
            width=4096,
        ).strip()
        lines.append("  - " + flow)
    lines.append("")
    lines.append(
        yaml.dump(
            {"proxy-groups": build_groups(nodes)},
            Dumper=_Dumper,
            allow_unicode=True,
            sort_keys=False,
            width=4096,
        ).rstrip()
    )
    lines.append("")
    lines.append("rule-providers:")
    for name, url in PROVIDERS:
        lines.append(f'  {name}: {{ type: http, behavior: classical, format: text, url: "{url}" }}')
    lines.append("")
    lines.append("rules:")
    lines.extend("  " + r for r in RULES)
    lines.append("")

    with open(dst, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines))
    print(f"完成：保留 {len(proxies)} 个自建节点，已写出 {dst}")


if __name__ == "__main__":
    main()
