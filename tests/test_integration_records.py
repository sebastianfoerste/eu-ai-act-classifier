"""The integration records state when the binding sources were last read."""

from __future__ import annotations

import json
from pathlib import Path

from eu_ai_act_classifier.citations import BINDING_SOURCE_RETRIEVED_ON

ROOT = Path(__file__).resolve().parent.parent
ADAPTER = ROOT / "docs" / "integrations" / "eu-ai-act-classifier.adapter.v1.json"
PROOF = ROOT / "contracts" / "eu-ai-act-classifier.proof.v1.json"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_adapter_and_proof_contract_share_the_source_currency_date() -> None:
    adapter, proof = _load(ADAPTER), _load(PROOF)

    assert adapter["proofContract"] == PROOF.relative_to(ROOT).as_posix()
    assert adapter["requiredProofSchema"] == proof["schema"]
    assert adapter["sourceCurrencyDate"] == proof["sourceCurrencyDate"]


def test_source_currency_date_is_the_binding_source_retrieval_date() -> None:
    assert _load(PROOF)["sourceCurrencyDate"] == BINDING_SOURCE_RETRIEVED_ON
