# Integration records

`eu-ai-act-classifier.adapter.v1.json` is the adapter manifest through which the former EU Regulatory Data Toolkit consumed this classifier for its MCP release. The toolkit was retired on 25 September 2026 and the manifest moved here on 12 October 2026, so the record survives the toolkit's archival.

The manifest pins commit `65d2b12`, which is not on `main`. The tag `archive/eu-reg-adapter-pin-65d2b12` keeps it reachable. No current consumer reads this manifest. The matching PENDING row on AI Act classification through the MCP release is in [the claim ledger](../REGULATORY_CLAIM_LEDGER.md), next to the PENDING row on how far the classifier encodes Regulation (EU) 2026/1744.

The manifest's `sourceCurrencyDate` (2026-10-18) is not a date of the pinned commit. It records when this repository last read the binding sources: `tests/test_integration_records.py` requires it to equal the `sourceCurrencyDate` of `contracts/eu-ai-act-classifier.proof.v1.json`, which in turn equals `BINDING_SOURCE_RETRIEVED_ON` in `src/eu_ai_act_classifier/citations.py`. At `65d2b12` the proof contract and the constant read 2026-08-26, and so did the manifest when it moved here. #26 read the sources again and moved the proof contract and the constant to 2026-10-18, and #30 moved the manifest's date with them; the pinned commit did not change.
