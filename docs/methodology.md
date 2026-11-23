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
4. GPAI: Art. 51 systemic threshold, Arts. 53 and 55 obligations, and the Art. 56
   code-of-practice review task.
5. Transparency: Art. 50(1) to (4) AIA.
6. Resolution: highest tier, review disposition, source-backed obligations
   (the Art. 4 AI literacy duty of every provider and deployer first), timeline
   and open legal questions.

## Operator Roles

`roles` lists the roles the organisation holds for the system, and every
obligation and graph item names the role it applies to. A profile holds at
least one role: the model and the published profile schema (`minItems: 1`)
reject an empty list, which used to classify with no duty at all. A
general-purpose AI model provider (`gpai_provider`) is not, as such, an
operator of the AI system (see Application Dates), so that role counts only
for the Chapter V items.

Where the roles do not match the facts the profile screens, the engine keeps
every item it lists and adds an open question, so the disposition becomes
`requires_review`. It drops no item and does not pick a role for the
organisation. The questions cover three cases:

1. A high-risk tier where the profile holds no operator role for the system
   (provider, deployer, importer, distributor or authorized_representative).
2. `is_gpai_model` without the `gpai_provider` role. The Chapter V items the
   report lists stay listed.
3. The `gpai_provider` role without `is_gpai_model`. The report lists no
   Chapter V item.

An Art. 50 item for a role the profile does not hold raises no question:
the catalog lists Art. 50(1) and (2) for the provider and Art. 50(3) and (4)
for the deployer, whatever roles the profile holds.

Outside the AI Act's scope no gate runs and no item is listed, so none of
these questions is asked there.

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
guidelines on the transparency obligations under Art. 50 (Communication
C(2026) 7702 final of 5 November 2026; the Commission's page dates their
publication to 20 July 2026) and the Code of Practice on Transparency of
AI-generated Content (final text of 10 June 2026; Art. 50(2), (4) and (5)).
It never changes the binding classification. The Art. 50 sources carry their
own retrieval date, 14 November 2026; the other advisory sources keep theirs.

## AI Literacy (Art. 4)

Art. 4(1) AIA, as replaced by Regulation (EU) 2026/1744, Art. 1, point (5)
(in force 27 July 2026), binds providers and deployers of AI systems whatever
the risk tier: they "take measures to support the development of AI literacy
of their staff and other persons dealing with the operation and use of AI
systems on their behalf", taking into account their technical knowledge,
experience, education and training, the context of use and the persons the
system is used on; no specific level of AI literacy of any individual has to
be guaranteed. Chapter I applies from 2 February 2025 (Art. 113, third
paragraph, point (a)), which is the item's date. The wording quoted applies
since Regulation (EU) 2026/1744 entered into force on 27 July 2026; until then
Art. 4 asked for measures "to ensure, to their best extent, a sufficient level
of AI literacy".

The report lists one Art. 4 obligation and one graph item (`literacy.provider.4`,
`literacy.deployer.4`, dated 2025-02-02, `determined`) per provider or deployer
role the profile holds, for every report whose scope is not outside the AI
Act, including a minimal-risk system and a system whose scope is under review.
Importers, distributors, authorised representatives and the provider of a
general-purpose AI model, as such, get none. A system the report classifies
as prohibited keeps the duty (below); `tests/test_ai_literacy.py` pins that.

Three positions are flagged "Literal reading, confirm with counsel" and sent
to review. For a Section B product Art. 2(2) does not list Art. 4 (the
obligation text and the item carry the flag). For a legacy high-risk system
Art. 111(2) applies the Regulation only after a significant change in design
(the item keeps its date and carries the flag). Both positions are the same
for Art. 50. For a system the report classifies as prohibited, Art. 4 names no
exception, and a prohibition can apply from a later date (Art. 5(1), first
subparagraph, points (ba) and (bb), from 2 December 2026) or be subject to an
exception (the obligation text and the item carry the flag).

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
machinery is a Section B product. `annex_i_legislation` names the act and
decides the section (section "Annex I acts" below). A profile that gives
neither the act nor the section keeps the Section A duties (the full Chapter
III set) and goes to review with an open question (C7), and the Art. 6(1)
finding says that a Section B product, machinery included, gets only the
Art. 2(2) provisions.

Two statements on the Art. 6(1) route are `info` findings of their own:
`HIGHRISK.6.1c`, Art. 6(1c) (a third-party conformity assessment required
solely for risks other than risks to health and safety does not meet
Art. 6(1)(b)), on every Annex I route, and, for Section A, `HIGHRISK.2.13`,
the Art. 2(13) note on delegated acts. Both citations were read in the
Official Journal text of Regulation (EU) 2026/1744 on 11 November 2026 and
are verified; the claim ledger records the source.

On its wording, Art. 2(2) covers any AI system
"classified as high-risk AI systems in accordance with Article 6(1)" for a
Section B product, and it lists no Chapter III provision other than
Art. 6(1), in particular not Art. 6(2), so a
Section B product that also falls in an Annex III area would get only the
listed provisions. Where the result is high-risk, the report keeps the
Annex III obligations as the conservative reading, since the system is also
classified high-risk under Art. 6(2) and Annex III. The Art. 6(1) finding,
the Art. 2(2) graph item, which is `review_required`, and an open question
state both after "Literal reading, confirm with counsel". Where an Art. 6(3)
derogation is asserted, they add that only the Art. 2(2) provisions apply if
it is established. A prohibited report lists no Annex III duties, so it has
no Art. 2(2) graph item and no such question, and its Art. 6(1) finding
states the literal reading without saying that the report keeps the duties.
As for every Section B product, Art. 5 and Art. 50 are kept and flagged
(next paragraph).

Art. 2(2) lists neither Art. 5 nor Art. 50, so on its wording neither applies
to a Section B product. The report keeps the prohibition and the Art. 50
duties as the conservative reading for every Section B product, Annex III
area or not, and flags both with "Literal reading, confirm with counsel": the
Art. 5 finding and an open question, and the `TRANSPARENCY.50` finding, each
Art. 50 graph item, which is `review_required`, and an open question.

Each of these three Section B flags asks whether a whole set of duties
reaches the product, so each is also an open question, and the disposition
becomes `requires_review`. The question opens with the provisions it
concerns ("Art. 2(2) AIA and Art. 6(2) AIA", "Art. 2(2) AIA and Art. 5 AIA"
or "Art. 2(2) AIA and Art. 50 AIA") and repeats the flag. The report still
picks no side: the duties stay listed. The Annex III flag on a prohibited
report is the one exception: that report lists no Annex III duties and raises
no "Art. 2(2) AIA and Art. 6(2) AIA" question, and the Art. 5 question sends
it to review. A Section B product with no Annex III
area and no Art. 5 or Art. 50 screen carries none of these flags. Other
counsel flags, such as the Art. 113 dating flags on the items of a plain
Annex III report or the Art. 50 flag for a high-risk system already on the
market, stay on their findings and items and do not by themselves change the
disposition.

Annex III systems are treated as high-risk unless an Art. 6(3) derogation is
asserted. An asserted derogation keeps the tier high-risk and changes the
disposition to `requires_review`, because Art. 6(4) requires documentation and
registration. Profiling of natural persons forecloses the derogation.

Annex III point 5(b) excepts AI systems used for the purpose of detecting
financial fraud. The exception is not applied silently: on a point 5(b)
profile, `used_for_financial_fraud_detection: true` or `null` keeps the tier
high-risk and adds an open question, so the disposition is `requires_review`.
The default, `false`, adds none.

The residual `AnnexIII.UNSURE` value is conservative. It marks the system
high-risk and records an unverified citation for review.

## FRIA Logic

Art. 27(1) reaches only high-risk AI systems referred to in Art. 6(2), that is
an Annex III area. A system that is high-risk only through Annex I gets no
FRIA item and no deployer status question.

Art. 27 is automatic for deployers of Annex III point 5(b) creditworthiness and
point 5(c) life and health insurance.

Art. 27 is also attached where the submitted facts establish a public-law
deployer or a private entity providing public services.

Annex III point 2 critical infrastructure is excluded from the Art. 27 trigger.
The engine suppresses the generic FRIA open question for that case.

Where the deployment is high-risk and the deployer status is incomplete, the
engine raises a review question instead of asserting a FRIA conclusion.

Two further cases raise an Art. 27 review question. With `III.unsure`, a
deployer whose status does not require a FRIA is told that points 5(b) and
5(c) would require one whatever the status. With an asserted Art. 6(3)
derogation on a system that is also on the Annex I route (Section A or not
given), the FRIA stays listed and the question says it falls away if the
derogation is established, since the system would then be high-risk only
under Art. 6(1).

## Obligation Graph

Every duty is written once, as an item of `obligation_graph`, the product
surface for review workflows. `obligations` lists the same duties in the same
order for compatibility: the article, actor and requirement of each graph
item, with a title, apart from the Art. 50 items, which
`transparency_obligations` lists, and four review tasks that state no duty of
the provider: Arts. 40 and 42 (presumptions of conformity), Art. 44
(certificates of notified bodies) and Art. 56 (codes of practice, addressed to
the AI Office and the Board). The graph keeps them
(`obligation_graph.GRAPH_ONLY_ITEMS`). Art. 41 is listed with its Art. 41(5)
duty, for a provider of a high-risk AI system (Section 2) and for a provider of
a general-purpose AI model (Chapter V, Section 2, and with systemic risk also
Section 3, "as applicable"). A GPAI provider's list
also names the Art. 53(4) and, with systemic risk, the Art. 55(2) duty to show
alternative adequate means of compliance. Three kinds of entry repeat a counsel flag
in the requirement that the graph item carries in its date note: the Art. 4
entry of a Section B product or a prohibited system, and the Art. 2(2) entry
of a Section B product in an Annex III area.

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
it too. Every other Annex III point raises the same open question, since a
missing status would otherwise read like "no"; for point 2 it names the
Art. 49(5) registration at national level instead. So the guided intake
records "I don't know" as null. For points 6 and 7 the item adds the Art. 49(4) secure non-public
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
A public-authority deployer counts only where the profile holds the deployer
role, as `deployer_public_authority` describes that role; it then counts for
the provider items too where the profile also holds the provider role, never
for importer, distributor or authorised-representative items. For a profile
without the deployer role the intended use is `public_authority_use` alone.
On an Annex I route without an Annex III area, a profile that holds the
deployer role raises an open question for both where a legacy or undated
system that is no Section B product has neither `public_authority_use` nor
the deployer's status, as the 2030 date may turn on them. The question for
an undated system also asks for the date, and it names the contested
cut-off where the answer rests on it.

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
states the Art. 111(1) carve-out for the Annex X large-scale IT systems
with its dates (read in the Official Journal text on 11 November 2026; VERIFIED
in the claim ledger), and
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
the profile gives no date but `public_authority_use` or, for a profile that
holds the deployer role, a `deployer_public_authority` of true that the
engine uses, it names the date to compare with, for a high-risk system with
no prohibited practice screened that is not a Section B product without an
Annex III area; where it
gives a date but no high-risk route, it says there is no Chapter III date to
compare with. A `significant_change_after_application_date` answer counts
only for a high-risk system, with no prohibited practice screened, placed on
the market or put into service before its Chapter III date; elsewhere the
check states that the answer is not used. In the same way it states that a
`deployer_public_authority` answer is not used unless the profile holds the
deployer role for a high-risk system with no prohibited practice screened, on
an Annex III point or, on an Annex I route, for a legacy or undated system that
is no Section B product and has no `public_authority_use`. It
also states the Art. 111(3)
check for a general-purpose AI model and the Art. 111(4) check for a system
generating synthetic content where the profile gives the date they turn on.
Outside the AI Act's scope there is no transitional status, so none of these
statements appears.

Art. 50 items (Chapter IV) carry 2 August 2026, subject to the Art. 50(2) rule
that follows. Under Art. 111(4), providers of generative systems placed on the
market before that date take the necessary steps to comply with Art. 50(2) by
2 December 2026.
If the profile's placing-on-market date is before 2 August 2026, the
Art. 50(2) item carries 2026-12-02 and the Art. 111(4) note. If it is on or
after that date, the item carries 2026-08-02 and no note. If the profile gives
no date, the item's `application_date` is null, its note names both dates, it
is `review_required` and an open question asks for the date, unless the
assessment date falls on or after both dates (C9). An assessment date before
both still raises the question: the duty does not apply that day, but the day
it starts turns on the missing date.

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
2 August 2025, every Chapter V item (Arts. 53, 55 and 56) carries 2027-08-02
and the Art. 111(3) note. If it is on or after that date, the items carry
2025-08-02 and no note. If the profile gives neither the model's date nor the
system's `placing_on_market_date`, their `application_date` is null, the note
names both dates, they are `review_required` and an open question asks for the
model's date, unless the assessment date falls on or after both dates (C9).
The GPAI Art. 41(5) item is in Chapter III, Section 5, which applies from
2 August 2026 (Art. 113, second paragraph): it carries 2026-08-02, or
2027-08-02 for a model placed before 2 August 2025, and with no date its note
names 2026-08-02 and 2027-08-02.

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
Whether the ban applies on the date assessed is decided from the profile's
`assessment_date`, never from the clock (next section).

The binding timeline also lists the point (a) exception (Art. 5(1), first
subparagraph, points (ba) and (bb), and Art. 5(1a) and (1b), from
2 December 2026), the full point (b) list (Chapter III Section 4, Chapters V,
VII and XII except Art. 101, and Art. 78, from 2 August 2025), point (d)
(Arts. 102 to 110, from 27 July 2026), the Art. 111(3) deadline of
2 August 2027 for general-purpose AI models already on the market before
2 August 2025, and the Art. 111(2) deadline of 2 August 2030 for high-risk
systems intended to be used by public authorities.

## Art. 5(1)(ba) and (bb), Annex I Acts And Open Dates

Read on 14 November 2026 in the Official Journal snapshots in `sources/`:
Regulation (EU) 2026/1744, Art. 1, points (2)(a), (7), (39)(b), (40) and (41),
Art. 4 and Recitals 11 to 13; Regulation (EU) 2024/1689, Art. 3, points (3),
(4), (6), (7), (9) and (11), Art. 111(3), Art. 113 and Annex I; Directive
2011/93/EU, Art. 2, points (c) and (e), and Art. 5(1). The legal fixtures in
`tests/legal/fixtures/` cite the same pinpoints.

### Points (ba) and (bb)

A profile reaches points (ba) and (bb) in one of two ways.

- It declares `5.1.ba` or `5.1.bb`. The declaration stands for every element:
  the reviewer has characterised the facts.
- It gives the element facts in `intimate_imagery` or
  `child_sexual_abuse_material`, each true, false or null. The engine subsumes
  them under Art. 5(1a)(a)(i) (intended purpose), Art. 5(1a)(a)(ii) (the
  system's design, training, architecture, capabilities or user-facing
  functionalities make it a reasonably foreseeable and reproducible outcome,
  without requiring significant technical modification, and the system has
  no reasonable and adequate technical safety measures and other safeguards
  to reliably prevent it, taking into account reasonably foreseeable misuse,
  and to correct observed or reported misuse), Art. 5(1a)(b) (use for that
  purpose) and, for point
  (ba), Art. 5(1b) (manipulation counts only where it increases exposure or
  alters the depicted activity). Unknown facts use three-valued logic: a null
  that could change the result keeps the point UNKNOWN, with an open question
  that names the facts; a null that cannot change it does not hold it open.

A profile can contradict itself on the content element. Where
`foreseeable_and_reproducible` (Art. 5(1a)(a)(ii)) or
`deployer_uses_for_that_purpose` (Art. 5(1a)(b)) is true, the generation or
manipulation of the material is stated as a foreseeable outcome or as the
deployer's purpose; if the content facts (`generates_material` and, for point
(ba), `manipulates_material_increasing_exposure`, or `generates_or_manipulates`)
nevertheless deny it, and that denial decides the result, the point is UNKNOWN
with an open question naming the conflicting facts, never "not met". Recital 12
of Regulation (EU) 2026/1744 counts a system for which that generation is a
reasonably foreseeable and reproducible outcome among the systems that generate
the material, and covers a deployer who uses for that purpose a system not
intended for it. An intended purpose (Art. 5(1a)(a)(i)) is not checked this
way, because a manipulation that Art. 5(1b) does not count may be a system's
purpose without being "that manipulation".

A point that is not met gives an `info` finding (`PROHIBITED.5.1.ba.not_met`),
an UNKNOWN point a `medium` finding (`.unknown`) and an open question. A met
point is dated by `assessment_date`, the date of the placing on the market,
putting into service or use under assessment:

- on or after 2 December 2026, the tier is prohibited (`PROHIBITED.5.1.ba`);
- before 2 December 2026, a `high` finding says the point applies from that
  date (`.not_yet_applicable`), the tier is not raised, and an open question
  sends the result to review (C4);
- with no assessment date, the prohibited tier is kept and an open question
  asks for the date (C4).

A system that generates synthetic content or deep fakes and neither declares
nor screens a point is asked about it, as the interim screen of #63 does; a
system already prohibited is not, because a further point cannot change its
result. A declaration that the element facts contradict is kept, with an open
question. The guided intake does not ask the element facts, so a guided
generator always gets the screen question.

### Annex I acts

`annex_i_legislation` names the Annex I act, as a locator (`I.B.21` is
Section B, point 21), and decides the section. Regulation (EU) 2026/1744,
Art. 1, point (41), deleted Section A, point 1 (Directive 2006/42/EC) and added
Regulation (EU) 2023/1230 on machinery as Section B, point 21, so `I.A.1` is
rejected and machinery is Section B. `annex_i_section` stays for profiles that
give only the section; a section that contradicts the act is rejected.

### Open dates and the assessment date

`applies_on_assessment_date` on an obligation-graph item says whether the item
applies on the assessment date, "on or after" its application date. It is null
without an assessment date. Where the application date itself is open (null),
it is known only if both possible dates give the same answer. The same holds
for a Chapter III, Section 5 or Chapter IX item, whose literal date (2 August
2026) is contested with the point (c) date the note names: the field does not
pick a side. For an item that Art. 111(2) makes attach only after a significant
change in design (an unchanged legacy high-risk system's Chapter III and
Art. 50 items), the field is false before the item's date and null from then
on, because whether the duty has attached turns on the change and on the
contested cut-off.

### Harmonised standards

Read on 14 November 2026 in the Official Journal snapshot
`sources/oj/32026D2274.en.xhtml`, fetched again that day and identical byte
for byte, and in Art. 40(1), Art. 17 and Art. 43(1) of Regulation (EU)
2024/1689. Commission Implementing Decision (EU) 2026/2274 publishes the
reference of one harmonised standard, EN 18286:2026, titled "Quality
management system for EU AI Act regulatory purposes" after the words
"Artificial intelligence", and enters
into force on the day of publication, 14 October 2026 (Art. 2). It names no
AI Act article. The Art. 40 graph item of every high-risk provider names the
standard. For an Annex III, point 1 system the Art. 43 item states the
Art. 43(1) choice: internal control (Annex VI) only where harmonised standards
or common specifications were applied for the Section 2 requirements, Annex
VII otherwise; an unsettled Annex III point gets the same sentence as a
condition, and a product under Annex I, Section A legislation, which follows
that legislation's procedure (Art. 43(3), last subparagraph), does not. The
Decision is not in the report's source manifest, whose `binding_level_1`
status covers the AI Act and its amendments only. Fixture:
`tests/legal/fixtures/art40_art43_1_harmonised_standards.json`.

Two readings are the classifier's own and not yet answered by the owner. The
graph items label them "Interpretation (S1)" and "Interpretation (S2)".

- S1: Art. 40(1) presumes conformity with the requirements in Chapter III,
  Section 2 (Arts. 8 to 15) and the Chapter V obligations. The quality
  management system is Art. 17, in Section 3, and the Decision's recital 1
  speaks only of "the requirements covered by those standards". Against
  that, Art. 40(2), third subparagraph, added by Regulation (EU) 2026/1744,
  Art. 1, point (17), asks for standardisation deliverables "to facilitate the
  joint compliance and presumption of conformity with the requirements or
  obligations set out in Chapter III, Sections 2 and 3"; Art. 40(1) itself
  was not amended. The item names the standard and leaves to review whether
  it gives a presumption for Art. 17.
- S2: EN 18286:2026 is by its title a quality management system standard, so
  the classifier reads it as not covering the Section 2 requirements:
  applying it alone does not open Annex VI under Art. 43(1).

### Interpretation choices

These are the answers given on 10 November 2026 under the owner's delegation
(continuation of the GitHub profile plan, section 2). They are Claude's
answers, recorded as such, and not a lawyer's sign-off. Where a result turns
on C1, C2, C3 or C10, the finding or open question says "Interpretation (Cn)".

- C1, consent in point (ba): read at system level for placing on the market
  and putting into service. Art. 5(1a)(a) frames its conditions at system
  level ("design, training, architecture, capabilities"), and Recital 12 asks
  for means to collect and demonstrate consent. Consent stays a reviewer fact.
- C2, the use limb: Art. 5(1a)(b) is read literally. Use is prohibited only
  where the deployer uses the system for the purpose of generating or
  manipulating the material; the content element stays and the Art. 5(1a)(a)
  conditions do not apply to use.
- C3, roles: providers (Art. 3(3)) and importers (Art. 3(6)) place on the
  market or put into service; deployers (Art. 3(4)) use. A distributor makes
  available (Art. 3(7)), which is not the first making available that
  Art. 3(9) calls placing on the market, so a distributor-only profile stays
  UNKNOWN with review, whether the point is declared or screened.
- C4, dates: before 2 December 2026 the result reads "applies from
  2 December 2026" and goes to review; with no assessment date the stricter
  result is kept, with review. This is a routing choice, not a reading of the
  text, so the output does not label it an interpretation.
- C6, Section B products: Art. 2(2) read literally lists neither Art. 5 nor
  Art. 50. The report keeps both. It raises an open question for Art. 5
  where a prohibition applies or a point (ba) or (bb) is met, and for
  Art. 50 wherever an Art. 50 duty is triggered.
- C7, an Art. 6(1) product with neither the act nor the section given: the
  report keeps the Section A duties and goes to review.
- C8, machinery: Section B, point 21 from 27 July 2026, the entry into force
  under Art. 4 of Regulation (EU) 2026/1744, which sets no later date for
  Art. 1, point (41). No Chapter III date changes, because the Annex I duties
  start on 2 August 2028. Limit: the engine applies the amended list on every
  assessment date; for a date before 27 July 2026, machinery was Section A.
- C9, Art. 111(3) and (4): "comply by" a date is read as applying from that
  date, inclusive; "before" a cut-off excludes the cut-off date; Art. 111(4)
  is triggered by placing on the market only, and the general-purpose AI
  model keeps its own date (`gpai_model_placing_on_market_date`). An unknown
  placing date leaves the item's `application_date` null and raises an open
  question, unless the assessment date falls on or after both possible dates.
  Refined on 15 November 2026: an assessment date before both dates raises the
  question too, because the day the duty starts still turns on the missing date.
- C10, the "without right" defence in point (bb): a fact the reviewer
  establishes under national law (Directive 2011/93/EU, Art. 5(1); Recital 13
  of Regulation (EU) 2026/1744). The engine does not evaluate national law.

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
`report.unverified_citations`. Nothing is invented. A pinpoint stated in prose,
such as the Art. 111(1) carve-out, carries the flag in the text while its
citation is unverified; the binding timeline, the same in every report, flags
it in its note only and does not add it to `report.unverified_citations`. A
pinpoint becomes verified only with a claim-ledger row that names the source,
the pinpoint and the access date.

## Boundaries

The classifier is a triage and review tool. It does not replace legal judgment,
conformity assessment work, notified-body processes, regulator filings or
organisation-specific advice.
