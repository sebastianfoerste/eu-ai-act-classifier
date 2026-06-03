# Methodology — how the regulation is encoded

This document records the mapping between Regulation (EU) 2024/1689 (the AI Act,
"AIA") and the rules in `catalog.py` and `rules/`. It is the part a reviewing
lawyer audits.

## Division of labour

The engine subsumes characterised facts under rules. It does not characterise
facts. The judgment — *does this tool materially influence a hiring decision?*,
*is this a "narrow procedural task"?* — stays with the lawyer who fills in the
`SystemProfile`. This is the same division a `Gutachten` makes between the
abstract rule (Obersatz) and its application to facts (Untersatz). Encoding the
Obersatz is safe; the Untersatz is where the engine defers.

## The five gates

| Gate | Legal basis | Output |
| --- | --- | --- |
| Prohibited | Art. 5(1)(a)–(h) AIA | Hard stop; dominates every tier |
| High-risk | Art. 6(1) (Annex I route), Art. 6(2)+(3) (Annex III route) | High-risk tier; obligations attach by role |
| GPAI | Art. 51 (systemic threshold), Art. 53 (baseline), Art. 55 (systemic) | Chapter V duties, orthogonal to the system tier |
| Transparency | Art. 50(1)–(4) AIA | Limited-risk tier; stacks on any higher tier |
| Minimal | — | Default |

## Decisions worth recording

**Conservative default on Annex III.** An Annex III use case is treated as
high-risk unless a derogation is affirmatively established. An asserted but
unconfirmed Art. 6(3) derogation does not silently downgrade the system: the
tier stays high-risk and the disposition becomes `requires_review`. This tracks
Art. 6(3)/(4), which require a documented assessment (and registration) before a
system leaves the high-risk tier.

**Profiling forecloses the derogation.** Where the system performs profiling of
natural persons, the Art. 6(3) derogation is unavailable (Art. 6(3) subpara. 2),
so the engine resolves directly to high-risk with no review needed.

**GPAI is orthogonal.** A general-purpose model provider carries Chapter V duties
whatever tier the downstream system occupies. Systemic risk follows the 10^25
FLOP presumption (Art. 51(2)) or a Commission designation (Art. 51(1)(b)). Where
compute is undisclosed and there is no designation, systemic status is left open
rather than assumed away.

**FRIA.** A fundamental rights impact assessment (Art. 27) is attached
automatically for deployers of Annex III(5)(b) creditworthiness and (5)(c)
insurance systems. For other high-risk deployments the engine raises an open
question, because Art. 27 also turns on the deployer's status (a body governed by
public law, or a private operator providing a public service) — a fact the engine
does not hold.

## Citation policy

- Citations are pinpoint: `Art. 6(2) AIA`, `Annex III(5)(b) AIA`.
- The classifier operates at **Level 1** (the Regulation). **Level 2** delegated
  and implementing acts and **Level 3** guidance (Commission guidelines, the GPAI
  Code of Practice) are out of scope and noted where relevant.
- A citation that is not confirmed against the consolidated EUR-Lex text is
  flagged `noch zu verifizieren` in the output and carried in
  `report.unverified_citations`. Areas 6 (law enforcement) and 7 (migration)
  sub-points are verified. The only remaining flag is the residual `UNSURE`
  catch-all, used when an Annex III area is implicated but the specific point is
  unsettled. Nothing is invented.

## Out of scope

Conformity-assessment workflow, Level 2/3 instruments, sector-specific Annex I
harmonisation legislation, and any substitution for legal judgment. This is a
screening tool a practising lawyer supervises.
