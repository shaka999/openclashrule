# openclashrule

OpenClash 订阅转换配置 + 自建节点优化流水线。

## 仓库内容

- `ACL4SSR_Online_optimized.ini` — 订阅转换模板（分组与规则定义）
- `scripts/optimize.py` — 把原始订阅配置精简为自建节点 + RULE-SET 规则
- `节点.yaml` — 生成好的精简配置，可直接给 OpenClash 使用
- `.github/workflows/update.yml` — 定时自动重新生成配置

## 使用

直接下载生成好的配置：

`https://raw.githubusercontent.com/shaka999/openclashrule/main/节点.yaml`

## 自动更新

1. 在仓库 `Settings -> Secrets and variables -> Actions` 添加 Secret：
   - Name：`SUB_URL`
   - Value：你的机场订阅地址
2. 之后每天 10:00（北京时间）自动更新一次；也可以到 Actions 页面手动运行，
   临时填写订阅地址。
3. 手动生成：

   ```bash
   python scripts/optimize.py 原始配置.yaml 节点.yaml
   ```

> 注意：`节点.yaml` 包含自建节点的连接凭据。当前仓库为公开仓库，
> 如需保密请把仓库设为 Private。
