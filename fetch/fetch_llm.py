#!/usr/bin/env python3
"""Refresh LLM API prices in data/llm.json from OpenRouter's public model API.

OpenRouter (https://openrouter.ai/api/v1/models) lists ~hundreds of models with
current prompt/completion prices in one JSON call, no API key -- the ideal
single source for keeping api_models fresh, Chinese providers included.

Run: python fetch/fetch_llm.py   (stdlib only; safe to run in CI)
It never wipes data on failure: if a model isn't found, its seed price is kept.
"""
import datetime
import json
import os
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LLM = os.path.join(ROOT, "data", "llm.json")
API = "https://openrouter.ai/api/v1/models"

# our display model  ->  OpenRouter id (or unique id-substring to match)
CURATED = {
    "GPT-5.5": "openai/gpt-5.5",
    "GPT-5.4": "openai/gpt-5.4",
    "GPT-5.4 mini": "openai/gpt-5.4-mini",
    "GPT-5.4 nano": "openai/gpt-5.4-nano",
    "Claude Opus 4.8": "anthropic/claude-opus-4.8",
    "Claude Sonnet 4.6": "anthropic/claude-sonnet-4.6",
    "Claude Haiku 4.5": "anthropic/claude-haiku-4.5",
    "Gemini 3.1 Pro": "google/gemini-3.1-pro",
    "Gemini 3.5 Flash": "google/gemini-3.5-flash",
    "Gemini 2.5 Flash": "google/gemini-2.5-flash",
    "Gemini 3.1 Flash-Lite": "google/gemini-3.1-flash-lite",
    "Grok 4.3": "x-ai/grok-4.3",
    "DeepSeek-V4 Pro": "deepseek/deepseek-v4-pro",
    "DeepSeek-V4 Flash": "deepseek/deepseek-v4-flash",
    "Qwen3.7 Max": "qwen/qwen3.7-max",
    "Qwen3.7 Plus": "qwen/qwen3.7-plus",
    "GLM-5.2": "z-ai/glm-5.2",
    "Kimi K2.7": "moonshotai/kimi-k2.7",
}


def fetch_models():
    req = urllib.request.Request(API, headers={"accept": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r).get("data", [])


def index(models):
    by_id = {}
    for m in models:
        by_id[m.get("id", "")] = m
    return by_id


def find(by_id, target):
    if target in by_id:
        return by_id[target]
    # fallback: first id that starts with target (ignoring a leading ~)
    for mid, m in by_id.items():
        if mid.lstrip("~").startswith(target):
            return m
    return None


def main():
    with open(LLM, encoding="utf-8") as f:
        data = json.load(f)
    try:
        by_id = index(fetch_models())
    except Exception as e:  # network/CI hiccup -> keep existing data
        print("fetch failed, keeping existing prices:", e)
        return
    updated = 0
    for row in data["api_models"]:
        target = CURATED.get(row["model"])
        if not target:
            continue
        m = find(by_id, target)
        if not m:
            print("  not found on OpenRouter:", row["model"], "(kept seed)")
            continue
        p = m.get("pricing", {})
        try:
            in_ = round(float(p["prompt"]) * 1e6, 4)
            out = round(float(p["completion"]) * 1e6, 4)
        except (KeyError, ValueError, TypeError):
            continue
        if in_ > 0 and out > 0:
            row["in"], row["out"] = in_, out
            if m.get("context_length"):
                row["ctx"] = int(m["context_length"])
            updated += 1
    data["as_of"] = (
        datetime.date.today().isoformat()
        + " · 主流厂商 API 价经 OpenRouter 自动刷新；订阅plan与能力档为人工维护"
    )
    with open(LLM, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"updated {updated}/{len(CURATED)} models -> {LLM}")


if __name__ == "__main__":
    main()
