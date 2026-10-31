# Methodology

This document records how Regulation (EU) 2024/1689 is encoded in the
classifier. It is the legal audit surface.

## Division Of Labour

The engine subsumes characterised facts under rules. It does not characterise
facts. The lawyer or reviewer decides whether the submitted system qualifies as
an AI system, what the intended purpose is, whether Annex I or Annex III is
triggered, and whether an asserted derogation is evidenced.

That division keeps the output deterministic. The `SystemProfile` states the
facts. The engine applies the rules and makes uncertainty visible.

## Gate Order

1. Scope and intake: Art. 2, Art. 3(1), intended purpose, EU nexus, exclusions
   and the Art. 111(2) transition: the placing-on-market and
   putting-into-service dates compared with the Chapter III date.
2. Prohibited practices: Art. 5(1)(a) to (h) AIA, including points (ba) and
   (bb), which apply from 2 December 2026. A hit is a hard stop.
3. High-risk classification: Art. 6(1), Art. 6(2), Art. 6(3), Annex I and
   Annex III.
4. GPAI: Art. 51 systemic threshold and Arts. 53, 55 and 56 obligations.
5. Transparency: Art. 50(1) to (4) AIA.
6. Resolution: highest tier, review disposition, source-backed obligations
   (the Art. 4 AI literacy duty of every provider and deployer first), timeline
   and open legal questions.

## Source Statuses

Binding Level 1 text drives classification and obligations. The current source
layer is Regulation (EU) 2024/1689 as consolidated on 27 July 2026 together
with Regulation (EU) 2026/1744. The latter was adopted on 8 July 2026 and
published in the Official Journal on 24 July 2026. Its amended application
dates are therefore binding source data rather than provisional context.

The source-status model retains a provisional category for future political
agreements. No provisional AI Omnibus source remains in the current manifest.

Nonbinding guidance appears only as advisory overlay or eval context. The
overlay can point reviewers to Commission materials, the AI Act Service Desk,
the GPAI Code of Practice, the draft high-risk guidelines, the Commission
guidelines on the transparency obligations under Art. 50 (published
20 July 2026) and the final Code of Practice on marking and labelling of
AI-generated content (published 10 June 2026; Art. 50(2) and (4)). It never
changes the binding classification. The Art. 50 sources carry their own
retrieval date, 31 October 2026; the other advisory sources keep theirs.

## AI Literacy (Art. 4)

Art. 4(1) AIA, as replaced by Regulation (EU) 2026/1744, Art. 1, point (5)
(in force 27 July 2026), binds providers and deployers of AI systems whatever
the risk tier: they "take measures to support the development of AI literacy
of their staff and other persons dealing with the operation and use of AI
systems on their behalf", taking into account their technical knowledge,
experience, education and training, the context of use and the persons the
system is used on; no specific level of AI literacy of any individual has to
be guaranteed. Chapter I applies from 2 February 2025 (Art. 113, third
paragraph, point (a)).

The report lists one Art. 4 obligation and one graph item (`literacy.provider.4`,
`literacy.deployer.4`, dated 2025-02-02, `determined`) per provider or deployer
role the profile holds, for every report whose scope is not outside the AI
Act, including a minimal-risk system and a system whose scope is under review.
Importers, distributors, authorised representatives and the provider of a
general-purpose AI model, as such, get none. A prohibited system gets none
either, as for the GPAI duties: a system that may not be placed on the market,
put into service or used (Art. 5) has no staff to operate it; the choice is
pinned in `tests/test_ai_literacy.py`.

Two positions are flagged "Literal reading, confirm with counsel" and sent to
review, as the same positions are for Art. 50: for a Section B product
Art. 2(2) does not list Art. 4 (the obligation text and the item carry the
flag), and for a legacy high-risk system Art. 111(2) applies the Regulation
only after a significant change in design (the item keeps its date and carries
the flag).

## High-Risk Logic

Annex I product-safety systems are high-risk where both the safety-component
route and third-party assessment route are asserted.

`annex_i_section` says which section of Annex I lists the product's Union
harmonisation legislation. For a Section B product, Art. 2(2) AIA, as replaced
by Regulation (EU) 2026/1744, Art. 1, point (2)(a), applies "only Article 6(1),
Article 60a and Articles 102 to 112"; Arts. 57, 58 and 59 apply only in so far
as the high-risk requirements have been integrated in that legislation. The
system stays high-risk under Art. 6(1), but the report lists no Chapter III
obligation: one Art. 2(2) obligation and graph item replace them. Regulation
(EU) 2026/1744, Art. 1, point (41) deleted Section A, point 1 and added
Regulation (EU) 2023/1230 on machinery as Section B, point 21, so AI-enabled
machinery is a Section B product. An unset section is treated as Section A
(the full Chapter III set), and the Art. 6(1) finding says that a Section B
product, machinery included, gets only the Art. 2(2) provisions.

On its wording, Art. 2(2) covers any AI system
"classified as high-risk AI systems in accordance with Article 6(1)" for a
Section B product, and it lists no Chapter III provision other than
Art. 6(1), in particular not Art. 6(2), so a
Section B product that also falls in an Annex III area would get only the
listed provisions. The report keeps the Annex III obligations as the
conservative reading, since the system is also classified high-risk under
Art. 6(2) and Annex III. The Art. 6(1) finding and the Art. 2(2) graph item,
which is `review_required`, state both after
"Literal reading, confirm with counsel". Where an Art. 6(3) derogation is
asserted, they add that only the Art. 2(2) provisions apply if it is
established. As for every Section B product, Art. 5 and Art. 50 are kept and
flagged (next paragraph).

Art. 2(2) lists neither Art. 5 nor Art. 50, so on its wording neither applies
to a Section B product. The report keeps the prohibition and the Art. 50
duties as the conservative reading for every Section B product, Annex III
area or not, and flags both with "Literal reading, confirm with counsel": the
Art. 5 finding and an open question, and the `TRANSPARENCY.50` finding and
each Art. 50 graph item, which is `review_required`.

Annex III systems are treated as high-risk unless an Art. 6(3) derogation is
asserted. An asserted derogation keeps the tier high-risk and changes the
disposition to `requires_review`, because Art. 6(4) requires documentation and
registration. Profiling of natural persons forecloses the derogation.

The residual `AnnexIII.UNSURE` value is conservative. It marks the system
high-risk and records an unverified citation for review.

## FRIA Logic

Art. 27 is automatic for deployers of Annex III point 5(b) creditworthiness and
point 5(c) life and health insurance.

Art. 27 is also attached where the submitted facts establish a public-law
deployer or a private entity providing public services.

Annex III point 2 critical infrastructure is excluded from the Art. 27 trigger.
The engine suppresses the generic FRIA open question for that case.

Where the deployment is high-risk and the deployer status is incomplete, the
engine raises a review question instead of asserting a FRIA conclusion.

## Obligation Graph

The legacy obligation lists remain for compatibility. The richer
`obligation_graph` is the product surface for review workflows.

Each graph item records:

1. Obligation ID.
2. Article.
3. Actor role.
4. Trigger.
5. Requirement.
6. Evidence artifact.
7. Source status.
8. Source URL.
9. Application date.
10. Review status.
11. Application date note, where the date rests on a contestable reading or a
    transitional rule.

The graph covers high-risk provider, deployer, importer, distributor,
authorised representative, value-chain, GPAI, transparency, post-market
monitoring and serious-incident duties.

## Application Dates

Dates follow Art. 113 AIA as amended by Regulation (EU) 2026/1744, checked on
18 October 2026 against the consolidated text of 27 July 2026.

Chapter III, Sections 1, 2 and 3 (Arts. 6 to 27, except Art. 6(5)) apply from
2 December 2027 for Annex III systems and from 2 August 2028 for Annex I
systems (Art. 113, third paragraph, point (c)). Graph items for Arts. 16 to 27
carry that date. A system that is an Annex I product and also falls in an
Annex III area is still "classified as high-risk pursuant to Article 6(2) and
Annex III", so point (c)(i) applies and its items carry 2 December 2027. Only
the Annex I route without an Annex III area gives 2 August 2028.

Point (c) does not defer Chapter III, Section 5 (Arts. 40 to 49) or Chapter IX
(Arts. 72 and 73). Read literally, those duties apply from the general date of
2 August 2026 (Art. 113, second paragraph). That reading is contested: the
duties bite only on systems classified high-risk under Art. 6, which is itself
deferred. Art. 16(f) to (i) also makes Arts. 43, 47, 48 and 49(1) provider
duties, and Art. 17(1)(h) and (i) builds Arts. 72 and 73 into the quality
management system; both sit in Section 3 and are deferred too. The graph
therefore gives these items 2026-08-02 with the note
"Literal reading, confirm with counsel", names the deferred date that applies
if they follow Sections 1 to 3, and marks them `review_required`. The engine
does not pick a side.

The Art. 49 registration duty appears only where Art. 49(1) reaches the system:
high-risk systems listed in Annex III, except point 2 (critical
infrastructure). An Annex I product without an Annex III area gets no Art. 49
obligation or graph item. A point 2 system gets an Art. 49(5) graph item
instead (registration at national level, not in the EU database), marked
`review_required`. An unsettled Annex III point (`III.unsure`) keeps the
Art. 49 item for review. Where the profile asserts an Art. 6(3) derogation
condition for any Annex III area, point 2 included, and no profiling, the graph
also has an Art. 49(2) item: a provider that relies on the derogation registers
itself and the system in the EU database (Art. 6(4)), and Art. 49(2) has no
point 2 exception. It is marked `review_required` and is the item the Art. 6(4)
assessment artifact lists. Because registration reaches a system only through
Annex III, the deferred alternative named on these items is always
2 December 2027 (point (c)(i)), also for a system that is an Annex I product
too.

Art. 49(3) adds a deployer item, `high-risk.deployer.49.3`, where the profile
has the deployer role, the Annex III area is not point 2 (`III.unsure` keeps
it, as for Art. 49(1)) and the deployer is a public authority. Deployers that
are public authorities, Union institutions, bodies, offices or agencies, or
persons acting on their behalf, register themselves, select the system and
register its use in the EU database before putting it into service or using
it. Selecting the system presupposes that it is registered there, so the item
also says not to use a system that is not.
The test is the deployer's own status, `deployer_public_authority`, not the
system's intended use. Where that field is not given, the item is inferred
for review where `public_authority_use` is true or the Annex III point is
5(a), 6 or 7, whose wording describes use by or on behalf of public
authorities (points 6 and 7 also by Union institutions, bodies, offices or
agencies). Its trigger names the reason and asks the reviewer to confirm the
deployer's status, and an open question asks for `deployer_public_authority`.
Point 8(a) also covers use
"in a similar way in alternative dispute resolution", which may be private,
so it raises only that open question. Otherwise a deployer given as a body
governed by public law (`deployer_public_law_body`, the Art. 27 fact) raises
it too. For points 6 and 7 the item adds the Art. 49(4) secure non-public
section, and for point 1 it adds it where the system is used in law
enforcement, migration, asylum or border control management. It also says
that the registration there includes only the Annex VIII and Annex IX
information Art. 49(4) lists, and that only the Commission and the national
authorities referred to in Art. 74(8) have access to it. As Section 5 duties,
the item carries 2026-08-02, the counsel flag and the 2 December 2027
alternative, and is `review_required`. It also appears in the deployer
obligations.

The Art. 26(8) check goes with the Art. 26 item, not the Art. 49(3) item.
Wherever the Art. 49(3) item appears, the Art. 26 requirement adds that a
deployer that is itself a public authority or Union institution, body, office
or agency and finds the system unregistered does not use it and informs the
provider or the distributor. Art. 26(8) binds those deployers themselves, not
persons acting on their behalf, and as a Chapter III, Section 3 duty it
carries the Art. 26 date. A deployer of a point 2 system that is a public
authority (or, with its status not given, of a system intended to be used by
public authorities) gets a `review_required` Art. 49(5) item,
`high-risk.deployer.49.5`, instead: Art. 49(3) excepts point 2, the system is
registered at national level, and the reviewer confirms what the national
procedure asks of the deployer. It is dated like the other Section 5 items.

Art. 111(2), as replaced by Regulation (EU) 2026/1744, Art. 1, point (39)(a),
applies the Regulation to operators of a high-risk system placed on the market
or put into service before "the date of application of Chapter III referred
to in Article 113" only if, "as from that date", its design changes
significantly. In any case, providers and deployers of high-risk systems
intended to be used by public authorities take the necessary steps to comply
by 2 August 2030. The engine
compares `placing_on_market_date` and `putting_into_service_date` with the
point (c) date for the system's route (2 December 2027, or 2 August 2028 for
an Annex I product without an Annex III area). If either date is before it,
the graph gets a `review_required` Art. 111(2) item for each operator role
the profile holds, once per role, because Art. 111(2) applies to "operators"
(a GPAI model provider is an operator under Art. 3(8), but not, as such, an
operator of the high-risk system). The item's
requirement follows `significant_change_after_application_date`; an asserted
change is not dated, the item asks for the date of the change in the
design-change log, and the flag says that on the date used here the change
counts only if it was made on or after that date. Only the provider and deployer items carry the
2 August 2030 sentence. With `public_authority_use` they also carry
2030-08-02, unless a significant change is asserted; with only a
public-authority deployer they ask the reviewer to confirm the intended use.

Art. 113 gives Chapter III no single date. Point (b) applies Section 4 from
2 August 2025, but Section 4 ("Notifying authorities and notified bodies")
concerns notifying authorities and notified bodies, not the operators
Art. 111(2) addresses, so the engine sets that date aside. That leaves the
point (c) date for Sections 1 to 3 and, on the literal reading above,
2 August 2026 for Section 5. Art. 111(2) uses the contested date twice: the
system must have been placed on the market or put into service "before" it,
and a significant change counts "as from that date". Every legacy result and
every undated Art. 111(2) check therefore carries
"Literal reading, confirm with counsel": the Art. 111(2) item, the scope text,
the open question asked while the change is not given and, unless a change is
asserted, the legacy note on each high-risk item, which goes to
`review_required`. For a system placed on the market or put into service
before 2 August 2026, the flag says that if the general date of
2 August 2026 is meant, a significant change in design made on or after that
date already counts: the change window would open on 2 August 2026, not on
the point (c) date. For a system whose earliest date falls on or after
2 August 2026 but before the point (c) date, it says that on the general-date
reading the system is not a legacy system and the condition does not apply.
An undated check states both. The item's note also
states the Art. 111(1) carve-out for the Annex X large-scale IT systems, and
that the first unit of the type and model decides (recital (39) of
Regulation (EU) 2026/1744).

Where an Art. 6(3) derogation is asserted for an Annex I product (not
Section B) that also falls in an Annex III area, the scope text and the item
note add that, if the derogation is established, only Art. 6(1) and Annex I
classify the system, so its Chapter III date is 2 August 2028 (point
(c)(ii)). A system that is a legacy system only on that date gets no item but
that statement in the scope text and an open question asking to confirm the
derogation, both flagged "Literal reading, confirm with counsel": on the
general date of 2 August 2026 it is no legacy system on either route. A Section B product without an Annex III area gets no
Art. 111(2) item, since none of its Chapter III duties apply.

The scope gate's transitional status states the same comparison in words:
which dates were given, the Chapter III date and its point, whether the system
predates it, the significant-change position, for a legacy system the
Art. 111(1) carve-out, and the 2030 deadline for public-authority use. Where
the profile gives no date but `public_authority_use` or
`deployer_public_authority`, it names the date to compare with; where it
gives a date but no high-risk route, it says there is no Chapter III date to
compare with. A `significant_change_after_application_date` answer counts
only for a high-risk system, with no prohibited practice screened, placed on
the market or put into service before its Chapter III date; elsewhere the
check states that the answer is not used. It also states the Art. 111(3)
check for a general-purpose AI model and the Art. 111(4) check for a system
generating synthetic content where the profile gives the date they turn on.

Art. 50 items (Chapter IV) carry 2 August 2026, subject to the Art. 50(2) rule
that follows. Under Art. 111(4), providers of generative systems placed on the
market before that date take the necessary steps to comply with Art. 50(2) by
2 December 2026.
If the profile's placing-on-market date is before 2 August 2026, the
Art. 50(2) item carries 2026-12-02 and the Art. 111(4) note. If it is on or
after that date, the item carries 2026-08-02 and no note. If the profile gives
no date, the item carries 2026-08-02 with the transition as its note.

Art. 111(2) applies "this Regulation", not only Chapter III, to a legacy
high-risk system only if its design changes significantly, so on its wording
Art. 50 too would apply to such a system only then. The report keeps the
Art. 50 dating above as the conservative reading. For a high-risk system with
a given date before its Chapter III date and no asserted significant change
(other than a Section B product without an Annex III area), the
`TRANSPARENCY.50` finding and each Art. 50 graph item carry
"Literal reading, confirm with counsel" with that reading, and the items are
`review_required`. The flag adds that which date Art. 111(2) means is itself
contested.

GPAI items (Chapter V) carry 2 August 2025, subject to the same kind of rule.
Under Art. 111(3), providers of general-purpose AI models placed on the market
before that date take the necessary steps to comply with the obligations
laid down in the Regulation by 2 August 2027. The model is dated by its
own date, `gpai_model_placing_on_market_date`. If it is before
2 August 2025, every GPAI item (Arts. 53, 55 and 56) carries 2027-08-02 and
the Art. 111(3) note. If it is on or after that date, the items carry
2025-08-02 and no note. If the profile gives no date, they carry 2025-08-02
with the transition as their note.

Art. 111(3) dates the model, Art. 111(4) the system, so the profile has two
fields. `gpai_model_placing_on_market_date` is the model's date and drives
Art. 111(3); `placing_on_market_date` stays the AI system's date and drives
Art. 111(4) (and Art. 111(2)). For backwards compatibility, a GPAI profile
that gives only `placing_on_market_date` is dated by it as before. That date
is not the model's own, so every GPAI item's note says so, the items are
`review_required` and an open question asks for
`gpai_model_placing_on_market_date`. Where the model's date is later than the
system's `placing_on_market_date`, an open question asks the reviewer to
confirm both dates.

Both transitions apply to systems (Art. 111(4)) and models (Art. 111(3))
placed on the market "before" the cut-off date, so one placed on the cut-off
date itself does not qualify. Only placing on the market counts; a
putting-into-service date alone does not drop the note. Because the engine
compares dates, `placing_on_market_date`, `putting_into_service_date` and
`gpai_model_placing_on_market_date` must be ISO dates (YYYY-MM-DD); a profile
with any other format is rejected.

The prohibited-practice codes `5.1.ba` and `5.1.bb` cover Art. 5(1), first
subparagraph, points (ba) and (bb), inserted by Regulation (EU) 2026/1744,
Art. 1, point (7). Their findings quote the point and the Art. 5(1a)
conditions (and, for point (ba), Art. 5(1b)) and say that the ban applies
from 2 December 2026 (Art. 113, third paragraph, point (a)). The sentence
does not depend on the date of the run, so the output stays deterministic.

The binding timeline also lists the point (a) exception (Art. 5(1), first
subparagraph, points (ba) and (bb), and Art. 5(1a) and (1b), from
2 December 2026), the full point (b) list (Chapter III Section 4, Chapters V,
VII and XII except Art. 101, and Art. 78, from 2 August 2025), point (d)
(Arts. 102 to 110, from 27 July 2026), the Art. 111(3) deadline of
2 August 2027 for general-purpose AI models already on the market before
2 August 2025, and the Art. 111(2) deadline of 2 August 2030 for high-risk
systems intended to be used by public authorities.

## Draft Work Products

Artifact generation is draft-only. Generated files include a source manifest,
open questions and a review status. They do not claim to be legal advice,
conformity assessments or final regulatory filings.

The artifacts are:

1. Art. 6(4) non-high-risk assessment.
2. Art. 27 FRIA.
3. Annex IV technical documentation checklist.
4. Post-market monitoring plan.
5. Serious-incident register.
6. GPAI model documentation checklist.
7. Training-content summary checklist.

## Citation Policy

Citations are pinpoint, for example `Art. 6(2) AIA` and `Annex III(5)(b) AIA`.

Unconfirmed pinpoints are flagged `noch zu verifizieren` and carried in
`report.unverified_citations`. Nothing is invented.

## Boundaries

The classifier is a triage and review tool. It does not replace legal judgment,
conformity assessment work, notified-body processes, regulator filings or
organisation-specific advice.
