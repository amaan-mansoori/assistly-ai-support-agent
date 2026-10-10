"""Frozen evaluation-dataset identity and validation."""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
import re
from typing import Any

DEFAULT_MANIFEST = Path("reports/evaluation/evaluation_dataset_manifest.json")
FROZEN_DATASET = Path("data/golden/golden_set.csv")
FROZEN_DATASET_SHA256 = (
    "2a80bd3cafee26ef8a4cc665b9212a33eae4d08e12a808f9e0cfdce00b523b81"
)
FROZEN_MANIFEST_SHA256 = (
    "3b0f6fa241cb686832536471d0982ae8434870b83ffa45e6cb23a07d20c4ed77"
)
EXPECTED_COLUMNS = (
    "example_id",
    "customer_tweet_id",
    "customer_author_id",
    "customer_text",
    "conversation_context",
    "amazonhelp_response",
    "candidate_stratum",
    "human_intent",
    "annotation_notes",
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_manifest(path: Path = DEFAULT_MANIFEST) -> dict[str, Any]:
    manifest = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(manifest, dict):
        raise ValueError("evaluation dataset manifest must be a JSON object")
    return manifest


def verify_dataset(
    dataset_path: Path,
    manifest_path: Path = DEFAULT_MANIFEST,
) -> tuple[dict[str, Any], list[dict[str, str]]]:
    """Verify the frozen file hash, schema, row count, and stable IDs."""
    manifest = load_manifest(manifest_path)
    if manifest.get("schema_version") != "1":
        raise ValueError("unsupported evaluation dataset schema version")
    if tuple(manifest.get("columns", ())) != EXPECTED_COLUMNS:
        raise ValueError("manifest columns do not match the supported frozen schema")
    expected_hash = manifest.get("sha256")
    if not isinstance(expected_hash, str) or not re.fullmatch(
        r"[0-9a-f]{64}", expected_hash
    ):
        raise ValueError("manifest SHA-256 must be 64 lowercase hexadecimal characters")
    expected_path = Path(manifest["dataset_path"])
    if dataset_path.as_posix() != expected_path.as_posix():
        raise ValueError(
            f"dataset path mismatch: expected {expected_path}, got {dataset_path}"
        )
    actual_hash = sha256_file(dataset_path)
    if (
        dataset_path.resolve() == FROZEN_DATASET.resolve()
        and actual_hash != FROZEN_DATASET_SHA256
    ):
        raise ValueError(
            "frozen evaluation dataset does not match its pinned SHA-256"
        )
    if (
        manifest_path.resolve() == DEFAULT_MANIFEST.resolve()
        and sha256_file(manifest_path) != FROZEN_MANIFEST_SHA256
    ):
        raise ValueError(
            "evaluation dataset manifest does not match its pinned SHA-256"
        )
    if actual_hash != expected_hash:
        raise ValueError(
            "evaluation dataset SHA-256 mismatch; refusing to evaluate changed data"
        )
    with dataset_path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if tuple(reader.fieldnames or ()) != tuple(manifest["columns"]):
            raise ValueError("evaluation dataset schema does not match its manifest")
        rows = list(reader)
    if len(rows) != manifest.get("row_count"):
        raise ValueError("evaluation dataset row count does not match its manifest")
    ids = [row.get("example_id", "").strip() for row in rows]
    if any(not item for item in ids) or len(ids) != len(set(ids)):
        raise ValueError("evaluation dataset example IDs must be non-empty and unique")
    if any(not row.get("customer_text", "").strip() for row in rows):
        raise ValueError("evaluation dataset contains an empty customer_text")
    if any(not row.get("human_intent", "").strip() for row in rows):
        raise ValueError(
            "evaluation dataset contains a missing provisional reference label"
        )
    if manifest.get("provenance_status") != "unresolved_provisional":
        raise ValueError("manifest provenance status must preserve the unresolved caveat")
    return manifest, rows
