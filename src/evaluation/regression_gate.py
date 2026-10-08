"""Compatibility-checked quality regression gate for evaluation summaries."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

DEFAULT_THRESHOLDS = Path("configs/evaluation_regression_thresholds.json")
IDENTITY_FIELDS = (
    "dataset_sha256",
    "dataset_version",
    "evaluation_schema_version",
    "evaluator_version",
    "prompt_version",
    "retrieval_version",
    "retrieval_backend",
    "run_mode",
    "provider",
    "model",
    "examples_evaluated",
)
OPTIONAL_HUMAN_IDENTITY_FIELDS = (
    "annotation_dataset_version",
    "annotation_sample_sha256",
    "annotation_records_sha256",
    "adjudication_records_sha256",
    "ground_truth_source",
)


def _metric(report: dict[str, Any], dotted_path: str) -> float | None:
    value: Any = report
    for part in dotted_path.split("."):
        if not isinstance(value, dict) or part not in value:
            return None
        value = value[part]
    if isinstance(value, dict):
        value = value.get("value")
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value)


def _metric_denominator(report: dict[str, Any], dotted_path: str) -> int | None:
    value: Any = report
    for part in dotted_path.split("."):
        if not isinstance(value, dict) or part not in value:
            return None
        value = value[part]
    if not isinstance(value, dict):
        return None
    denominator = value.get("denominator")
    if isinstance(denominator, bool) or not isinstance(denominator, int):
        return None
    return denominator


def compare_reports(
    baseline: dict[str, Any],
    candidate: dict[str, Any],
    thresholds: dict[str, Any],
) -> dict[str, Any]:
    base_metadata = baseline.get("run_metadata", {})
    candidate_metadata = candidate.get("run_metadata", {})
    mismatches: dict[str, Any] = {
        field: {
            "baseline": base_metadata.get(field),
            "candidate": candidate_metadata.get(field),
        }
        for field in IDENTITY_FIELDS
        if field not in base_metadata
        or field not in candidate_metadata
        or base_metadata.get(field) != candidate_metadata.get(field)
        or (field != "model" and not base_metadata.get(field))
    }
    human_identity_present = any(
        field in base_metadata or field in candidate_metadata
        for field in OPTIONAL_HUMAN_IDENTITY_FIELDS
    )
    if human_identity_present:
        mismatches.update({
            field: {
                "baseline": base_metadata.get(field),
                "candidate": candidate_metadata.get(field),
            }
            for field in OPTIONAL_HUMAN_IDENTITY_FIELDS
            if field not in base_metadata
            or field not in candidate_metadata
            or base_metadata.get(field) != candidate_metadata.get(field)
            or not base_metadata.get(field)
        })
    baseline_config = base_metadata.get("configuration", {})
    candidate_config = candidate_metadata.get("configuration", {})
    if not isinstance(baseline_config, dict) or not isinstance(
        candidate_config, dict
    ):
        mismatches["configuration"] = {
            "status": "missing_or_invalid",
        }
    elif baseline_config != candidate_config:
        mismatches["configuration"] = {
            "different_keys": sorted(
                str(key)
                for key in set(baseline_config) | set(candidate_config)
                if baseline_config.get(key) != candidate_config.get(key)
            ),
        }
    if mismatches:
        return {
            "gate_version": "evaluation-regression-gate-v1",
            "compatible": False,
            "passed": False,
            "identity_mismatches": mismatches,
            "checks": [],
            "failure_reasons": ["runs are not comparable"],
        }

    checks: list[dict[str, Any]] = []
    failures: list[str] = []
    configured_metrics = thresholds.get("metrics")
    if not isinstance(configured_metrics, dict) or not configured_metrics:
        raise ValueError("threshold configuration must define a non-empty metrics mapping")
    for name, policy in configured_metrics.items():
        if not isinstance(policy, dict):
            raise ValueError(f"threshold for {name!r} must be an object")
        path = policy.get("path", name)
        direction = policy.get("direction")
        limit = policy.get("max_degradation")
        if not isinstance(path, str):
            raise ValueError(f"metric path for {name!r} must be a string")
        if direction not in {"higher_is_better", "lower_is_better"}:
            raise ValueError(f"invalid regression direction for {name!r}")
        if isinstance(limit, bool) or not isinstance(limit, (int, float)) or limit < 0:
            raise ValueError(f"max_degradation for {name!r} must be non-negative")
        base_value = _metric(baseline, path)
        candidate_value = _metric(candidate, path)
        minimum_denominator = policy.get("minimum_denominator")
        if minimum_denominator is not None and (
            isinstance(minimum_denominator, bool)
            or not isinstance(minimum_denominator, int)
            or minimum_denominator < 1
        ):
            raise ValueError(
                f"minimum_denominator for {name!r} must be a positive integer"
            )
        base_denominator = _metric_denominator(baseline, path)
        candidate_denominator = _metric_denominator(candidate, path)
        check: dict[str, Any] = {
            "metric": name,
            "path": path,
            "baseline": base_value,
            "candidate": candidate_value,
            "max_degradation": float(limit),
            "direction": direction,
        }
        if minimum_denominator is not None:
            check.update({
                "minimum_denominator": minimum_denominator,
                "baseline_denominator": base_denominator,
                "candidate_denominator": candidate_denominator,
            })
        if (
            base_value is None
            or candidate_value is None
            or (
                minimum_denominator is not None
                and (
                    base_denominator is None
                    or candidate_denominator is None
                    or base_denominator < minimum_denominator
                    or candidate_denominator < minimum_denominator
                )
            )
        ):
            check["passed"] = False
            check["status"] = (
                "insufficient_denominator"
                if base_value is not None
                and candidate_value is not None
                else "required_metric_missing"
            )
            failures.append(
                f"{name}: metric missing or denominator below minimum"
            )
        else:
            degradation = (
                base_value - candidate_value
                if direction == "higher_is_better"
                else candidate_value - base_value
            )
            check["degradation"] = degradation
            check["passed"] = degradation <= float(limit)
            check["status"] = "pass" if check["passed"] else "threshold_exceeded"
            if not check["passed"]:
                failures.append(f"{name}: degradation {degradation:.6f} exceeds {limit}")
        checks.append(check)
    identity = {field: base_metadata[field] for field in IDENTITY_FIELDS}
    if human_identity_present:
        identity.update({
            field: base_metadata[field]
            for field in OPTIONAL_HUMAN_IDENTITY_FIELDS
        })
    return {
        "gate_version": "evaluation-regression-gate-v1",
        "compatible": True,
        "passed": not failures,
        "identity": identity,
        "checks": checks,
        "failure_reasons": failures,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--thresholds", type=Path, default=DEFAULT_THRESHOLDS)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    baseline = json.loads(args.baseline.read_text(encoding="utf-8"))
    candidate = json.loads(args.candidate.read_text(encoding="utf-8"))
    thresholds = json.loads(args.thresholds.read_text(encoding="utf-8"))
    report = compare_reports(baseline, candidate, thresholds)
    rendered = json.dumps(report, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
