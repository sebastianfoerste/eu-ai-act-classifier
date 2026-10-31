# Regulation (EU) 2026/1744 (Digital Omnibus on AI): point-by-point coverage

What this classifier does with each amending point of Art. 1 of Regulation (EU)
2026/1744 and with its Arts. 2 to 4. The README says the classifier encodes
the amending regulation "in part"; this table says which part. It was drawn up
on 31 October 2026 from the Publications Office snapshot of the OJ text on the
`feat/source-snapshots` branch (`sources/oj/32026R1744.en.xhtml`), read point
by point, and cross-checked against the AI Act Service Desk article pages
(consolidated text as at 27 July 2026). EUR-Lex itself was not read (bot
challenge). `tests/test_omnibus_coverage.py` checks that every point has
exactly one row. Legal mapping drafted with AI assistance; not adopted until
the owner reviews it.

Status values:

- **encoded**: the classifier applies the amended rule; the last column names
  the code (file and symbol) and the ledger row.
- **flagged for review**: the classifier states the amended rule in a finding,
  note or source entry but does not apply it to the result.
- **outside the classifier's scope**: governance, notified bodies, sandboxes,
  enforcement, delegated-act powers and other provisions that do not change a
  tier, an obligation or a date for the operator of a system.
- **not encoded (gap)**: the amendment changes or conditions an operator's
  duty and the classifier does not reflect it.

Ledger references are to the claim text in
[docs/REGULATORY_CLAIM_LEDGER.md](REGULATORY_CLAIM_LEDGER.md).

| Point | Provision amended | Effect (one line) | Status in this classifier | Where |
| --- | --- | --- | --- | --- |
| (1) | Art. 1(2)(g) | Subject matter: innovation support names SMCs next to SMEs. | outside the classifier's scope | Subject-matter clause; no operator duty. |
| (2) | Art. 2(2), Art. 2(7) | (2): for an Art. 6(1) system of an Annex I, Section B product only Art. 6(1), Art. 60a and Arts. 102 to 112 apply (Arts. 57 to 59 in so far as integrated). (7): data protection law applies without prejudice to Arts. 4a and 59. | encoded (Art. 2(2)); outside the classifier's scope (Art. 2(7)) | `catalog.py`: `SECTION_B_PROVISIONS`, `section_b_obligations`; `engine.py`: `section_b_only` branch; `transitions.py`: `section_b_product`; ledger rows "For an AI system classified high-risk under Art. 6(1) for a product covered by ... Section B", "Whether Art. 2(2) also displaces the Annex III duties", "Whether Art. 5 and Art. 50 apply to ... a Section B product", "Whether Art. 4 applies to ... a Section B product". |
| (3) | Art. 2(13) (new) | Delegated acts, due by 2 August 2027, may limit Arts. 9 to 15 and 17 to 25 for Section A products with equivalent sectoral protection. | flagged for review | `rules/high_risk.py`: `_ANNEX_I_SECTION_NOTE[SECTION_A]` (the Art. 6(1) finding states it; no Section A duty is limited); ledger row "The classifier encodes Regulation (EU) 2026/1744 only in part". |
| (4) | Art. 3(14), (14a), (14b) | (14): "safety component" redefined (a safety function prevents or mitigates risks to health and safety of persons or property). (14a), (14b): SME and SMC defined. | not encoded (gap) | `annex_i_safety_component` is a characterised fact; the field guide does not state the amended definition. No enterprise-size field for SME or SMC. |
| (5) | Art. 4 | AI literacy: providers and deployers take measures to support the AI literacy of staff and persons operating or using the system on their behalf; no specific level has to be guaranteed. | encoded | `catalog.py`: `AI_LITERACY_REQUIREMENT`, `ai_literacy_obligations`; `engine.py`: `ai_literacy_applies`; `obligation_graph.py`: `_ai_literacy_items`; ledger rows "Providers and deployers of AI systems take measures to support the development of AI literacy", "Whether Art. 4 applies to ... a Section B product". |
| (6) | Art. 4a (new) | Providers of high-risk systems may process special categories of personal data for bias detection and correction under the listed conditions; no obligation to do so. | not encoded (gap) | A permission with conditions attached to Art. 10(2)(f) and (g); the Art. 10 item (`catalog.py`: `high_risk_provider_obligations`) does not mention it. |
| (7) | Art. 5(1), first subparagraph, points (ba), (bb); Art. 5(1a), (1b) | New prohibitions on non-consensual intimate material and child sexual abuse material, limited by the Art. 5(1a) conditions and the Art. 5(1b) exclusion; apply from 2 December 2026. | encoded (the prohibitions and their date); flagged for review (Art. 5(1a), (1b): no input field, the finding quotes them) | `catalog.py`: `PROHIBITED`, `LATER_PROHIBITIONS`, `ART_5_1A`, `ART_5_1B`; `rules/prohibited.py`; `citations.py`: `POINT_A_EXCEPTION_DATE`; ledger rows "Art. 5(1), first subparagraph, points (ba) and (bb) ... apply from 2 December 2026", "The classifier encodes Regulation (EU) 2026/1744 only in part". |
| (8) | Art. 6(1a), (1b), (1c) (new) | (1a): systems used solely for non-safety aspects are not safety components; (1b): unless their failure endangers health and safety; (1c): a third-party assessment required solely for non-health-and-safety risks does not meet Art. 6(1)(b). | flagged for review (Art. 6(1c)); not encoded (gap) (Art. 6(1a), (1b)) | `rules/high_risk.py`: `_ART_6_1C` in the Art. 6(1) finding; no field records whether the system is a safety component only for non-safety aspects; ledger row "The classifier encodes Regulation (EU) 2026/1744 only in part". |
| (9) | Art. 10(1), (5), (6) | Data governance criteria extended to Art. 4a(1); former Art. 10(5) (special-category data) deleted and moved to Art. 4a; Art. 10(6) adjusted. | not encoded (gap) | The Art. 10 obligation (`catalog.py`: `high_risk_provider_obligations`) is generic ("Apply data governance ...") and stays correct, but names neither Art. 4a nor the deleted paragraph. |
| (10) | Art. 11(1), second subparagraph | SMEs, including start-ups, and SMCs may provide the Annex IV documentation in a simplified form the Commission establishes. | not encoded (gap) | No enterprise-size field; the Art. 11 item and the Annex IV checklist (`artifacts.py`) do not mention the simplified form. |
| (11) | Art. 17(2) | Quality management system proportionate to the provider's size, in particular for SMEs and SMCs. | not encoded (gap) | No enterprise-size field; the Art. 17 item is generic. |
| (12) | Art. 25(2), (4) | (2): the initial provider cooperates with the new provider (documentation, known limitations, technical access), unless it excluded a high-risk change; (4): third-party cooperation duty, with the free and open-source exception. | not encoded (gap) | The Art. 25 item (`catalog.py`: `high_risk_value_chain_obligations`; `obligation_graph.py`: `high-risk.value-chain.25`) asks only whether provider duties shift; the cooperation duties and the open-source exception are not stated. |
| (13) | Art. 27(4), (5) | (4): a FRIA may cross-reference or include parts of a data protection impact assessment; (5): the AI Office develops a questionnaire template, including an automated tool. | not encoded (gap) | The Art. 27 item (`catalog.py`: `high_risk_deployer_obligations`) and the FRIA artifact (`artifacts.py`, checklist "Record whether a DPIA covers any overlapping obligation") do not state the cross-reference rule or the template. |
| (14) | Art. 28(8), (9) (new) | Single application and unified assessment for conformity assessment bodies under Section A legislation. | outside the classifier's scope | Notified bodies. |
| (15) | Art. 29(4) | Documents from other designations support a notified body's designation; single application under Art. 28(8). | outside the classifier's scope | Notified bodies. |
| (16) | Art. 30(2) | Notification by codes, categories and types of AI systems in Annex XIV; delegated acts amend Annex XIV. | outside the classifier's scope | Notified bodies. |
| (17) | Art. 40(2), new subparagraph | The Commission requests standardisation deliverables for joint compliance with Chapter III, Sections 2 and 3 and Annex I legislation. | outside the classifier's scope (a Commission request) | The Art. 40 graph item (`obligation_graph.py`: `high-risk.provider.40`) asks the provider to track harmonised standards. Harmonised-standards logic for EN 18286:2026 and Implementing Decision (EU) 2026/2274 is proposed in open PR #34 and is not changed here. |
| (18) | Art. 42(3) (new) | High-risk systems in the scope of Regulation (EU) 2024/2847 (Cyber Resilience Act) meeting its Art. 12(1) conditions are deemed to comply with Art. 15 cybersecurity. | not encoded (gap) | The Art. 15 item and the Art. 42 graph item (`obligation_graph.py`: `high-risk.provider.42`) do not state the presumption; no field records CRA scope. |
| (19) | Art. 43(3) | For Section A products the provider follows the sectoral conformity assessment procedure, with the Section 2 requirements and the Art. 17 assessment folded in; notified bodies under that legislation may assess them. | not encoded (gap) | The Art. 43 item (`catalog.py`, `obligation_graph.py`: `high-risk.provider.43`) says "Undergo the applicable conformity assessment" without the Section A route. The Art. 43(2) versus Art. 44 question for Annex III points 2 to 8 is closed PR #14's, not touched. |
| (20) | Art. 50(7) | Codes of practice for marking and labelling; the Commission assesses their adequacy for Art. 50(2) and (4) and may adopt common rules by implementing act. | outside the classifier's scope (a Commission task); the Code it provides for is a nonbinding source | `citations.py`: `AI_CONTENT_CODE_URL`, manifest entry `ai-content-code-of-practice`; `advisory.py`: `guidance.ai-content-code`; ledger row "The Commission guidelines on the transparency obligations under Art. 50 and the Code of Practice ... are final". |
| (21) | Art. 56(6) | The Commission and the Board monitor the GPAI codes of practice and publish an adequacy assessment. | outside the classifier's scope | The Art. 56 graph item (`obligation_graph.py`: `gpai.provider.56`) is generic. |
| (22) | Art. 57(1), (3), (3a), ... | AI regulatory sandboxes: one per Member State by 2 August 2027, EDPS sandbox, an AI Office sandbox for Art. 75(1) systems. | outside the classifier's scope | Named only in the Art. 2(2) text for Section B products (`catalog.py`: `SECTION_B_PROVISIONS`, "Arts. 57, 58 and 59 ... in so far as integrated"). |
| (23) | Art. 58(1) | Implementing acts on sandbox arrangements, including governance and data protection supervision. | outside the classifier's scope | As for point (22). |
| (24) | Art. 60(1), (2) | Real-world testing outside sandboxes for Annex III and Section A systems. | outside the classifier's scope | Testing, not classification. |
| (25) | Art. 60a (new) | Member States may allow real-world testing of Section B product systems under national frameworks. | outside the classifier's scope; named in the Art. 2(2) item | `catalog.py`: `SECTION_B_PROVISIONS`; `obligation_graph.py`: `_section_b_items` (dates Art. 60a from 2 August 2026). |
| (26) | Art. 63(1) | SMEs without partner or linked enterprises may meet elements of the quality management system in a simplified manner. | not encoded (gap) | No enterprise-size field. |
| (27) | Art. 64(3) (new) | Resources for the AI Office. | outside the classifier's scope | Governance. |
| (28) | Art. 69(2) | Fees for expert advice. | outside the classifier's scope | Governance. |
| (29) | Art. 70(8) | National authorities' guidance, in particular to SMEs and SMCs, with consultation of other authorities. | outside the classifier's scope | Governance. |
| (30) | Art. 72(3) | The post-market monitoring plan is part of the Annex IV documentation; Commission guidance including a template by 2 September 2027. | encoded | `catalog.py`: `ART_72_REQUIREMENT`; `obligation_graph.py`: `high-risk.provider.72`; ledger row "The post-market monitoring plan is part of the Annex IV technical documentation". |
| (31) | Art. 75 (heading, (1), (1a) to (1e), ...) | The AI Office is exclusively competent for GPAI-based systems of the same provider (with exceptions) and VLOP/VLOSE systems; their providers report serious incidents to the AI Office (Art. 75(1a)); mutual assistance. | encoded (the Art. 75(1a) reporting route, stated next to Art. 73(1)); outside the classifier's scope (the rest) | `catalog.py`: `ART_73_REQUIREMENT`; `obligation_graph.py`: `high-risk.provider.73`; ledger row "Providers of high-risk AI systems report serious incidents to the market surveillance authorities". No field records the AI Office's competence, so both routes are stated. |
| (32) | Arts. 75a, 75b, 75c (new) | Supervisory and enforcement powers of the AI Office, fines and publication of decisions. | outside the classifier's scope | Enforcement. |
| (33) | Art. 76(1), new subparagraph | Real-world testing under Art. 60a: references to market surveillance authorities read as the sectoral authorities. | outside the classifier's scope | Testing. |
| (34) | Art. 77 (heading, (1), (1a), (1b), ...) | Access of fundamental-rights authorities to information held by market surveillance authorities; cooperation. | outside the classifier's scope | Enforcement. |
| (35) | Art. 95(4) | Codes of conduct: interests of SMEs and SMCs. | outside the classifier's scope | Voluntary codes. |
| (36) | Art. 96(1)(a), (g); second subparagraph | Commission guidelines, including on Arts. 25 and 26 and on complementarity with Section A legislation by 1 August 2027. | outside the classifier's scope | Guidelines enter the manifest as nonbinding sources when published (`citations.py`: `source_manifest`). |
| (37) | Art. 97(2), (3), ... | Delegated-act powers extended to Art. 2(13) and Art. 30(2), five years from 27 July 2026. | outside the classifier's scope | Delegated-act powers. |
| (38) | Art. 99(1), (4)(da) (new), (6a) (new) | Penalties: Member States consider SMEs and SMCs; fines for breaches of Art. 25(2) and (4); SMC fines capped at the lower amount. | outside the classifier's scope (penalties); not encoded (gap) for Art. 99(4)(da) and (6a) | Follows the Art. 25(2), (4) gap (point (12)) and the missing enterprise-size field. |
| (39) | Art. 111(2) (replaced), Art. 111(4) (new) | (2): the Regulation applies to operators of legacy high-risk systems only after a significant change in design; public-authority systems comply by 2 August 2030. (4): generative systems already on the market comply with Art. 50(2) by 2 December 2026. | encoded | `transitions.py`: `chapter_iii_date`, `legacy_dates`, `cut_off_flag`; `obligation_graph.py`: `_art_111_2_items`, `_with_legacy_notes`, `_art_111_dating`; `citations.py`: `ART_111_2_PUBLIC_AUTHORITY_DEADLINE`, `ART_111_4_DEADLINE`; ledger rows "A high-risk system placed on the market or put into service before the date of application of Chapter III", "Which date ... in Art. 111(2) means" (PENDING), "Whether Art. 50 applies to a high-risk system placed on the market ... before its Chapter III date" (PENDING), "Providers of AI systems generating synthetic audio, image, video or text content placed on the market before 2 August 2026", "For the Art. 111(2) grace period the decisive date is ... the first unit" (recital 39). |
| (40) | Art. 113, third paragraph, points (a), (c), (d) | (a): Art. 5(1)(ba), (bb), (1a), (1b) from 2 December 2026; (c): Chapter III, Sections 1 to 3 from 2 December 2027 (Annex III) and 2 August 2028 (Annex I); (d): Arts. 102 to 110 from 27 July 2026. | encoded | `citations.py`: `POINT_A_EXCEPTION_DATE`, `POINT_C_ANNEX_III`, `POINT_C_ANNEX_I`, `POINT_D_DATE`, `AMENDING_APPLICATION_DATES`; ledger rows "The 2 December 2027 date recorded by the classifier", "The 2 August 2028 date recorded by the classifier", "The classifier dates the Chapter III, Section 5 items", "Arts. 102 to 110 apply from 27 July 2026". |
| (41) | Annex I, Section A point 1 (deleted), Section B point 21 (new) | Machinery (Regulation (EU) 2023/1230) moves from Section A to Section B. | encoded | `models.py`: `AnnexISection`; `rules/high_risk.py`: `_ANNEX_I_SECTION_NOTE`; ledger row "Machinery is a Section B product". |
| (42) | Annex VIII, Section B, points 7 and 9 (deleted) | Two items drop from the information a public-authority deployer registers under Art. 49(3). | outside the classifier's scope | Registration form content; the Art. 49(3) and (4) items (`catalog.py`: `_SECURE_SECTION`) name Annex VIII without listing its points. |
| (43) | Annex XIV (new) | Codes, categories and types of AI systems for the designation of notified bodies. | outside the classifier's scope | Notified bodies. |
| Art. 2 | Regulation (EU) 2018/1139 (civil aviation), Arts. 27, 31, 32, 36, 39, 50, 53 | Sectoral implementing and delegated acts take the Chapter III, Section 2 requirements into account for AI safety components. | outside the classifier's scope | Sectoral legislation; reached only through the Art. 2(2) item for a Section B product. |
| Art. 3 | Regulation (EU) 2023/1230 (machinery), Arts. 8, 20, 47 | Delegated acts add health and safety requirements for high-risk AI machinery, applying by 2 August 2028; interim presumption of conformity via Arts. 40 and 41 standards. | flagged for review | `catalog.py`: `SECTION_B_ROUTE` (cites Art. 3, point (1) and the 2 August 2028 date); `obligation_graph.py`: `_section_b_items`. |
| Art. 4 | Entry into force | Third day after publication: 27 July 2026. | encoded | `citations.py`: timeline comment and `POINT_D_DATE`; ledger row "The current consolidated AI Act text is dated 27 July 2026". |

## Gaps in one place

- SME and SMC simplifications: Arts. 3(14a), (14b), 11(1), 17(2), 63(1) and 99(6a). The profile has no enterprise-size field, so none of them changes a result. Adding one is an owner decision.
- Art. 6(1a) and (1b): no input records whether a safety component serves only non-safety aspects.
- Art. 25(2) and (4) and Art. 99(4)(da): the value-chain item does not state the initial provider's cooperation duties or the open-source exception.
- Art. 27(4) and (5): the FRIA item does not state the DPIA cross-reference rule or the AI Office template.
- Art. 42(3) and Art. 43(3): no CRA presumption and no Section A conformity route in the items.
- Art. 4a and Art. 10: the Art. 10 item does not name Art. 4a.
- EN 18286:2026 and Implementing Decision (EU) 2026/2274 (Art. 40): open PR #34.

## Corrigendum

A corrigendum to Regulation (EU) 2026/1744 exists: CELEX 32026R1744R(01),
OJ L 2026/90810, 29.9.2026, ELI
http://data.europa.eu/eli/reg/2026/1744/corrigendum/2026-09-29/oj. The
Publications Office metadata lists the German language version only. Its
content was not read (EUR-Lex and the Publications Office portal refused
automated access on 31 October 2026), so the English text relied on above is
treated as unaffected as far as known. The ledger carries a PENDING row.
