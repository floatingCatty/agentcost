#!/usr/bin/env python3
"""Build the self-contained static page from data/*.json.

Auto-update story: a scheduled job refreshes data/*.json (see fetch/), then runs
this to regenerate site/index.html, then redeploys (GitHub Pages / Vercel).
"""
import json
import os

ROOT = os.path.dirname(os.path.abspath(__file__))


def load(name):
    with open(os.path.join(ROOT, "data", name), encoding="utf-8") as f:
        return json.load(f)


def main():
    llm = load("llm.json")
    compute = load("compute.json")
    data = {
        "as_of": llm.get("as_of"),
        "fx_usd_cny": llm.get("fx_usd_cny", 7.2),
        "consumer_plans": llm["consumer_plans"],
        "api_models": llm["api_models"],
        "gpus": compute["gpus"],
        "selfhost_models": compute["selfhost_models"],
        "defaults": compute.get("defaults", {}),
    }
    with open(os.path.join(ROOT, "templates", "app.html"), encoding="utf-8") as f:
        app = f.read()
    app = app.replace("__DATA__", json.dumps(data, ensure_ascii=False))

    html = (
        "<!doctype html>\n<html lang=\"zh\">\n<head>\n<meta charset=\"utf-8\">\n"
        "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">\n"
        "<title>AI 用多少钱？· Agent 成本对比 | AgentCost</title>\n"
        "<meta name=\"description\" content=\"把订阅、API、自部署租卡全部折算成元/万token一个口径，并算出自部署vs API的盈亏平衡点。\">\n"
        "<style>body{margin:0;background:#FBF6EA}</style>\n</head>\n<body>\n"
        + app + "\n</body>\n</html>\n"
    )
    out = os.path.join(ROOT, "site")
    os.makedirs(out, exist_ok=True)
    with open(os.path.join(out, "index.html"), "w", encoding="utf-8") as f:
        f.write(html)
    print("built ->", os.path.join(out, "index.html"), f"({len(html)} bytes)")


if __name__ == "__main__":
    main()
