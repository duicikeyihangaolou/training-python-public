#!/usr/bin/env python3
"""
AIOps 最小 loop：
  observe → LLM(GLM/OpenAI 兼容) → 结构化建议 → confirm → act

环境变量（勿提交 git）：
  GLM_API_KEY / ZHIPUAI_API_KEY / OPENAI_API_KEY
  GLM_BASE_URL 默认 https://open.bigmodel.cn/api/paas/v4/
  GLM_MODEL    默认 glm-4-flash
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

from aiops_actions import (
    fetch_prometheus_alerts,
    get_deploy_status,
    query_prom,
    rollback_chaos,
    scale_deployment,
)

ALERTS_JSONL = Path(os.environ.get("SRE_AIOPS_ALERTS_JSONL", "/tmp/sre-aiops-alerts.jsonl"))


def load_recent_webhooks(limit: int = 5) -> list[dict]:
    if not ALERTS_JSONL.exists():
        return []
    lines = ALERTS_JSONL.read_text(encoding="utf-8", errors="replace").strip().splitlines()
    out: list[dict] = []
    for line in lines[-limit:]:
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return out


def observe(prom: str, api: str) -> dict[str, Any]:
    alerts = fetch_prometheus_alerts(prom)
    firing = [a for a in alerts if a.get("state") == "firing"]
    err = query_prom(
        prom,
        'sum(rate(http_requests_total{job="api",status=~"5.."}[1m]))'
        ' / clamp_min(sum(rate(http_requests_total{job="api"}[1m])), 0.001)',
    )
    qps = query_prom(prom, 'sum(rate(http_requests_total{job="api"}[1m]))')
    cpu = query_prom(
        prom,
        '100 - (avg(rate(node_cpu_seconds_total{mode="idle"}[2m])) * 100)',
    )

    def first_value(payload: dict) -> str | None:
        try:
            return payload["data"]["result"][0]["value"][1]
        except (KeyError, IndexError, TypeError):
            return None

    return {
        "firing_alerts": [
            {
                "alertname": a.get("labels", {}).get("alertname"),
                "severity": a.get("labels", {}).get("severity"),
                "summary": a.get("annotations", {}).get("summary"),
                "description": a.get("annotations", {}).get("description"),
            }
            for a in firing
        ],
        "error_rate": first_value(err),
        "qps": first_value(qps),
        "cpu_pct": first_value(cpu),
        "api_base": api,
        "recent_webhooks_count": len(load_recent_webhooks(20)),
    }


SYSTEM = """你是资深 SRE。根据观测数据给出处置建议。
只输出一个 JSON 对象，不要 markdown，不要复述字段说明。
字段要求：
- summary: 用中文描述当前现象（结合 error_rate、qps、firing_alerts）
- root_cause_hypothesis: 在「应用故障」「容量不足」「依赖故障」「未知」中选一并写理由
- runbook: 3-5 条可执行排查/恢复步骤（中文短句）
- recommended_action: 只能是 rollback_chaos | scale_out | scale_in | none
- scale_replicas: 整数，默认 3
- confidence: 0 到 1 的小数
决策：若 firing 含 HighErrorRate 或 error_rate>0.05 且 cpu 不高 → rollback_chaos；
若 HighRequestRate 或 qps 很高且错误率低 → scale_out；否则 none。
"""


def call_llm(observation: dict) -> dict:
    try:
        from openai import OpenAI
    except ImportError as e:
        raise SystemExit("请先: pip install openai") from e

    api_key = (
        os.environ.get("GLM_API_KEY")
        or os.environ.get("ZHIPUAI_API_KEY")
        or os.environ.get("OPENAI_API_KEY")
    )
    if not api_key:
        raise SystemExit("未设置 GLM_API_KEY / ZHIPUAI_API_KEY / OPENAI_API_KEY")

    base_url = os.environ.get("GLM_BASE_URL", "https://open.bigmodel.cn/api/paas/v4/")
    model = os.environ.get("GLM_MODEL", "glm-4-flash")
    client = OpenAI(api_key=api_key, base_url=base_url)
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM},
            {
                "role": "user",
                "content": "观测数据：\n"
                + json.dumps(observation, ensure_ascii=False, indent=2)
                + "\n请直接输出 JSON。",
            },
        ],
        temperature=0.2,
        response_format={"type": "json_object"},
    )
    text = (resp.choices[0].message.content or "{}").strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.startswith("json"):
            text = text[4:].strip()
    return json.loads(text)


def rules_fallback(observation: dict) -> dict:
    names = {a["alertname"] for a in observation.get("firing_alerts", [])}
    try:
        err = float(observation.get("error_rate") or 0)
    except ValueError:
        err = 0.0
    if "HighErrorRate" in names or err > 0.05:
        return {
            "summary": "API 错误率超过阈值（规则引擎）",
            "root_cause_hypothesis": "应用故障：chaos/缺陷可能性高",
            "runbook": [
                "查看 Grafana Errors",
                "执行 rollback_chaos",
                "确认 HighErrorRate resolved",
            ],
            "recommended_action": "rollback_chaos",
            "scale_replicas": 3,
            "confidence": 0.7,
            "engine": "rules",
        }
    if "HighRequestRate" in names:
        return {
            "summary": "请求流量偏高（规则引擎）",
            "root_cause_hypothesis": "容量不足：建议扩容 sre-load",
            "runbook": ["确认 QPS", "kubectl scale sre-load", "观察 Pod"],
            "recommended_action": "scale_out",
            "scale_replicas": 3,
            "confidence": 0.65,
            "engine": "rules",
        }
    return {
        "summary": "无明确 firing 告警",
        "root_cause_hypothesis": "未知",
        "runbook": ["复查 Prometheus Alerts"],
        "recommended_action": "none",
        "scale_replicas": 1,
        "confidence": 0.3,
        "engine": "rules",
    }


def execute_action(advice: dict, api: str, deploy: str, ns: str, force: str | None) -> Any:
    action = force or advice.get("recommended_action")
    if action == "rollback_chaos":
        return {"action": action, "result": rollback_chaos(api)}
    if action == "scale_out":
        replicas = int(advice.get("scale_replicas") or 3)
        before = get_deploy_status(deploy, ns)
        scale_deployment(deploy, replicas, ns)
        after = get_deploy_status(deploy, ns)
        return {"action": action, "replicas": replicas, "before": before, "after": after}
    if action == "scale_in":
        before = get_deploy_status(deploy, ns)
        scale_deployment(deploy, 1, ns)
        after = get_deploy_status(deploy, ns)
        return {"action": action, "replicas": 1, "before": before, "after": after}
    return {"action": action, "result": "noop"}


def main() -> None:
    parser = argparse.ArgumentParser(description="SRE AIOps minimal loop")
    parser.add_argument("--prom", default="http://127.0.0.1:9090")
    parser.add_argument("--api", default="http://127.0.0.1:8088")
    parser.add_argument("--deploy", default="sre-load")
    parser.add_argument("--namespace", default="default")
    parser.add_argument("--mode", choices=["advise", "execute"], default="advise")
    parser.add_argument("--confirm", action="store_true")
    parser.add_argument("--auto-execute", action="store_true")
    parser.add_argument("--rules-only", action="store_true")
    parser.add_argument(
        "--force-action",
        choices=["rollback_chaos", "scale_out", "scale_in", "none"],
        default=None,
        help="跳过建议中的动作，强制执行指定动作（课堂扩容演示）",
    )
    args = parser.parse_args()

    obs = observe(args.prom, args.api)
    print("=== OBSERVE ===", flush=True)
    print(json.dumps(obs, ensure_ascii=False, indent=2), flush=True)

    if args.rules_only:
        advice = rules_fallback(obs)
    else:
        try:
            advice = call_llm(obs)
            advice["engine"] = "llm"
        except Exception as e:
            print(f"[warn] LLM 失败，降级规则引擎: {e}", file=sys.stderr, flush=True)
            advice = rules_fallback(obs)

    print("=== ADVICE ===", flush=True)
    print(json.dumps(advice, ensure_ascii=False, indent=2), flush=True)

    if args.mode != "execute":
        return

    if not args.auto_execute:
        if not args.confirm:
            raise SystemExit("execute 需要 --confirm 或 --auto-execute")
        ans = input(
            f"确认执行 {args.force_action or advice.get('recommended_action')}? 输入 yes: "
        ).strip()
        if ans != "yes":
            print("已取消", flush=True)
            return

    result = execute_action(advice, args.api, args.deploy, args.namespace, args.force_action)
    print("=== EXECUTE ===", flush=True)
    print(json.dumps(result, ensure_ascii=False, indent=2), flush=True)


if __name__ == "__main__":
    main()
