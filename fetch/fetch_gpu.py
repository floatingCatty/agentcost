#!/usr/bin/env python3
"""Validate / bump data/compute.json (GPU rental prices).

Unlike LLM prices (OpenRouter gives one clean JSON), GPU marketplaces have no
single free API, so prices here are maintained by hand or by a per-source
scraper you add below. This script: (1) sanity-checks the schema, (2) optionally
plugs in scrapers, (3) bumps as_of so the page shows when it was last reviewed.

Add a real scraper by appending to SCRAPERS (each returns
[{"provider","gpu","vram_gb","usd_hr","type"}, ...]).
"""
import datetime
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COMPUTE = os.path.join(ROOT, "data", "compute.json")

SCRAPERS = []  # e.g. [scrape_getdeploying, scrape_vast] -- add your own


def validate(data):
    for g in data["gpus"]:
        assert {"gpu", "vram_gb", "cloud_hr", "buy_usd", "power_w", "perf"} <= set(g), f"bad gpu row: {g}"
        assert g["cloud_hr"] > 0 and g["buy_usd"] > 0, f"bad price: {g}"
    for m in data["selfhost_models"]:
        assert {"name", "ref_gpu", "ref_n", "tok_s_ref", "quants"} <= set(m), f"bad model: {m}"
        for q in m["quants"]:
            assert {"q", "vram_gb"} <= set(q), f"bad quant: {q}"
    return True


def main():
    with open(COMPUTE, encoding="utf-8") as f:
        data = json.load(f)
    validate(data)
    rows = []
    for s in SCRAPERS:
        try:
            rows += s()
        except Exception as e:
            print(f"  scraper {getattr(s,'__name__',s)} failed: {e}")
    if rows:
        data["gpus"] = rows
        print(f"replaced gpus with {len(rows)} scraped rows")
    else:
        print("no scrapers configured -> GPU prices kept (manual maintenance).")
    today = datetime.date.today().isoformat()
    data["as_of"] = today + " · GPU 价为人工/脚本维护的 on-demand 最低档；吞吐为估计"
    with open(COMPUTE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print("validated & bumped ->", COMPUTE)


if __name__ == "__main__":
    main()
