# Experiment 2 — AI Supplier Offer & Installation Compatibility Advisor

**Target:** small German SHK heating-installation businesses purchasing domestic heating circulation pumps.

**Hypothesis:** Installers who can compare two supplier offers *against their actual installation and the potential installed cost*, rather than just purchasing price, will find the free tool useful and will be more likely to explore Plancraft's project-folder, purchasing documents and costing features.

**Funnel stage:** acquisition → tool engagement → product consideration.

**Primary metric:** unique Plancraft outbound CTA clickers / unique anonymous sessions who finish a valid comparison. Clicking is an **outbound-interest proxy**, not verified signup, demo booking or revenue.

**Secondary metrics:** landing views, started submissions, successfully AI-extracted results, manual comparison results, result exports, critical false-positive compatibility decisions, qualitative feedback. `ai_result_generated` is only raised after an actual successful AI extraction. The prototype stores the implemented events to a local/persistent-host SQLite database. Session IDs are anonymous, so counts are approximate unique sessions rather than known unique people.

**Smallest useful test:** recruit 3–5 independent German plumbers/heating installers. Each tries two scenarios: (1) a straightforward documented pump match with missing hydraulic inputs, (2) a pump with a wrong port-to-port length. Ask them to use a real or clearly labelled synthetic supplier quotation; never claim synthetic offers are actual customer quotes. Observe whether they understand the status without coaching and whether the cost/fit report would influence a buying decision. Record industry, date, outcome and actual user statements with consent.

**Provisional success threshold (pre-declared, not observed):** at least 3/5 participants independently consider the result useful for a realistic purchase decision, and no critical false-positive safety/compatibility verdict. For a follow-on acquisition test, a directional target is 5% qualified outbound CTA CTR after comparison. Extremely small samples are exploratory, not proof of scalable acquisition.

**Stop/revise conditions:** erroneous pump model or article-number identification, ungrounded accessory claims, critical wrong-positive compatibility findings, confusing result status, or no additional value beyond basic price sorting.

**Key tradeoffs:** exact model catalogue is narrow (nine product variants across two brands); quote inputs can be messy; manufacturer product values are not an automatic hydraulic design check; missing prices block full-cost ranking; manual path trades AI extraction for resilience. Backend uses FastAPI + vanilla JS/CSS to keep the experiment deployable with minimal dependencies, rather than building a large React/Next.js stack for this standalone prototype. There is no Plancraft API integration.

**What was actually observed in development:** local deterministic and API tests passed (see test output when independently re-run). A browser interaction test with synthetic quotes exercised manual entry, comparison, a conflict result, manufacturer sources and responsive layout. AI provider calls with a real user key, public access from an independent device, and genuine craftsman feedback **have not been verified**.

| Field | Actual result |
|---|---|
| Public URL | Not deployed |
| Real unique visitors | Not measured |
| AI extraction calls with live user key | Not tested |
| Real tool completions | Not measured |
| Real Plancraft outbound clicks | Not measured |
| Qualified opt-in leads | Not implemented / not measured |
| Professional interviews | Not conducted |
| Development time | Not accurately time-tracked; do not claim compliance with the four-hour brief |

**Next action:** add the server-side API key, verify a real live extraction using two actual supplier quotations (with consent), deploy to a legally suitable public HTTPS host with persistent event storage, then run the 3–5-person SHK usability test. Recalculate actual metrics from the genuine public sessions, excluding synthetic QA tests.
