# AgentCost · 跑 Agent 的成本对比 & 部署方案

把**订阅 plan、各家 API、租 GPU 自部署**全部折算成同一口径 **元/万 token**，并算出
**自部署 vs API 的盈亏平衡点**。面向两类人，渐进式披露：

- **L1（小白）**：我想用 AI，按用途+预算推荐订阅/模型。
- **L2（进阶）**：API 元/万 token 归一对比（含国产，可排序、切币种/语言、调输入输出比）。
- **L3（技术）**：自部署成本计算器 + 盈亏平衡点 + 部署方案。

## 结构
```
data/llm.json        # 订阅plan + API价格 + 能力档（API价由 OpenRouter 自动刷新）
data/compute.json    # GPU时租 + 模型吞吐（人工/脚本维护）
templates/app.html   # 三层 UI + 成本引擎（纯前端，零后端）
build.py             # data + 模板 -> 自包含 site/index.html
fetch/fetch_llm.py   # 经 OpenRouter 公共API刷新 LLM 价（stdlib，无依赖）
fetch/fetch_gpu.py   # 校验/维护 GPU 价（可挂自定义 scraper）
.github/workflows/update.yml  # 每周定时刷新+构建+部署到 GitHub Pages
```

## 本地运行
```bash
python fetch/fetch_llm.py   # 可选：刷新最新 LLM 价
python build.py             # 生成 site/index.html
# 浏览器打开 site/index.html 即可（纯静态，无需服务器）
```

## 部署（任选其一，都免费）
- **GitHub Pages**：把本目录推到 GitHub，在仓库 Settings → Pages 选 “GitHub Actions”。
  自带的 workflow 会每周一自动刷新价格、重建、部署。
- **Vercel / Netlify / Cloudflare Pages**：把 `site/` 作为静态目录部署即可。

## 数据准确性
- **LLM API 价**：由 OpenRouter 实时刷新，较可靠。
- **GPU 时租**：on-demand 最低档（含 spot/市场，稳定性各异），需人工或自建 scraper 维护。
- **模型吞吐 tok/s**：公开 benchmark 量级估计，强依赖并发/量化/序列长度——**建议按你自己的实测校正 `data/compute.json`，这正是这个工具的护城河。**

## 成本模型（L3）
```
API:    月费 = 日token × 30 × blended / 1e6      （blended = 输入价×占比 + 输出价×(1−占比)）
自部署: 需卡数 = ceil(日token / (吞吐 × 86400))
        月费   = 需卡数 × 卡时租 × 24 × 30
        盈亏平衡日token ≈ 卡时租 × 24 × 1e6 / blended
```
简化假设：自部署按满吞吐租卡、全天计费；忽略冷启动/运维/网络成本。
