---
name: storm-research
description: Use when someone asks to run Storm Research, use the storm-research skill, run the STORM method on a topic, says "storm research this" / "storm report on X" / "give me a STORM briefing on X", or wants a multi-perspective, citation-verified research briefing on a topic. Runs a 6-phase STORM pipeline: perspective discovery (topic-derived personas) -> multi-perspective interview loop (questions -> grounded answers -> follow-ups) -> contradiction + gap map -> structured outline -> synthesized HTML report -> adversarial peer review + primary-source verification. Best for multi-stakeholder decisions and topics where viewpoints and fact-checked claims matter; overkill for a simple factual lookup.
argument-hint: "[topic to research] [--panel discover|market] [--model-profile fast|balanced|max]"
---

# Storm Research

## What this does

Turns one topic into a verified, multi-perspective research outline **and** an HTML briefing. It is a faithful adaptation of Stanford's STORM method (Shao et al., NAACL 2024; `stanford-oval/storm`): it discovers the expert perspectives that fit *this* topic, runs a short simulated interview per persona (each asks its own questions, gets grounded answers, then asks a follow-up), maps where the personas contradict each other, and synthesizes the result into a structured outline — **the outline is STORM's core deliverable**. It then renders a self-contained HTML report on top of that outline, adversarially peer-reviews its own output, and verifies every citation against its primary source before delivering.

STORM's founding insight: the bottleneck in AI research is the **pre-writing**, not the writing. The edge lives in perspective breadth and outline structure, so this skill spends its budget there. Run the full pipeline end to end. Do not shortcut a phase. This is heavier than a quick web lookup; that is the point.

## Portability

Self-contained. Depends only on built-in Claude Code tools (the `Agent` tool, `Write`, and web search/fetch used inside those agents) plus `report-template.html` in this same folder. No external scripts, APIs, paid services, or other skills. Drop the folder into any `.claude/skills/` directory and it works.

## Arguments

- `$ARGUMENTS` — the topic. If absent, ask.
- `--panel discover|market` — override panel mode (see Phase 0). Default: auto-select.
- `--model-profile fast|balanced|max` — shift model tiers together (see Model routing). Default: `balanced`.

## Model routing (persona quality cascades — do not skip)

Bad personas produce bad questions produce bad research. Route the reasoning-heavy phases to a strong model and the mechanical phases to a lighter one. Pass `model:` explicitly on every `Agent` call:

| Phase | Work | balanced (default) | fast | max |
|---|---|---|---|---|
| 1 Discovery | derive personas | `opus` | `sonnet` | `opus` |
| 2 Interviews | questions -> answers -> follow-up | `sonnet` (x5) | `sonnet` | `opus` |
| 6 Verification | citation check | `sonnet` (x4-6) | `haiku` | `sonnet` |

Phases 3, 4, 5 run inline on the main thread (no agents). **Never use a fable/Mythos tier** — it exhausts usage limits under multi-agent fan-out.

## Phase 0: Scope the topic + select the panel

1. If `$ARGUMENTS` has the topic, use it. Otherwise ask what to research.
2. State your interpretation of the topic in one line (`{TOPIC_FRAME}`) and proceed. Only ask a clarifying question if the topic is genuinely ambiguous in a way that changes the research. Default to proceeding.
3. Identify the **reader's role** so the actionable section can target it. Infer from the topic/context; if unclear, ask in one line, or default to "a practitioner or decision-maker in this field."
4. **Select the panel mode** (this is the STORM perspective-discovery decision):
   - **`discover`** (default) — derive topic-fit personas. Use for decision-support and technical/product/domain topics ("should we build X", "how do we detect Y", "evaluate approach Z", "design a framework for W").
   - **`market`** — the fixed hype-check preset (Practitioner, Academic, Skeptic, Economist, Historian). Use for "is [trend] overhyped / real / a bubble", "the future of X", competitive-narrative topics.
   - Auto-select by topic shape; honor an explicit `--panel` flag. State the chosen mode in one line.
5. Derive a kebab-case `topic-slug` for filenames.
6. Tell the user the pipeline is running (discover personas, interview, map, outline, report, verify). One line.

## Phase 1: Perspective discovery (single strong-model agent)

**`market` mode:** skip this agent. Load the fixed preset personas (see Appendix A) and go to Phase 2.

**`discover` mode:** spawn ONE agent (Discovery model tier). Prompt:

```
Topic: {TOPIC} ({TOPIC_FRAME}). Reader: {ROLE}.
Derive EXACTLY 5 research personas, one per canonical STORM slot. Instantiate each
for THIS topic with a concrete role title — never a generic "expert":
  1. DOMAIN EXPERT   — deepest technical/subject authority on this topic
  2. PRACTITIONER    — does it day-to-day; cares what actually ships/works
  3. SKEPTIC         — builds the strongest steelman for why it fails
  4. NEWCOMER        — foundational clarity; assumes nothing; asks the "obvious"
  5. ADJACENT EXPERT — from a neighboring field; brings transferable frameworks
Anti-homogeneity rule: if any two personas would ask overlapping questions,
replace one with a more distinct role. Distinct lenses are the whole point.
Return a TOON persona table:
personas[5]{slot,name,role,background,stake,bias}:
  domain,...,...,...,...,...
  ...
```

Keep the persona table; you will pass it into every interview in Phase 2 and cite personas by name in the outline.

## Phase 2: Multi-perspective interview loop (five parallel agents)

Spawn **five agents in a single message** (Interview model tier), one per persona, so they run concurrently. Each agent runs a self-contained three-step interview and separates question-finding from answer-finding (do NOT collapse these — that is STORM's #1 anti-pattern). Prompt each with its persona block substituted:

```
You are this persona researching {TOPIC} ({TOPIC_FRAME}):
{PERSONA: name, role, background, stake, bias}

Run a 3-step interview. Do REAL web research; every answer must trace to a fetched URL.

STEP A — QUESTIONS: Write 6-8 questions ONLY this persona would ask (unique to its
lens; do not answer them yet).
STEP B — GROUNDED ANSWERS: For each question, web-search and answer in 2-3 sentences
with a concrete data point / case / figure + the primary source URL. If you cannot
find a real source, mark the answer UNVERIFIED — never invent one.
STEP C — FOLLOW-UP: Pick the 1-2 thinnest or most surprising answers, ask a sharper
follow-up question, and re-research it.

Return EXACTLY this TOON, under 550 words total:
persona: {name}
coreClaim: {this persona's 2-sentence position}
theOneThing: {the single insight only this lens would surface}
qa[N]{question,answer,sourceUrl,status}:      # status: answered|thin|unverified
  {q},{a},{url},answered
  ...
followUps[M]{question,answer,sourceUrl,status}:
  {q},{a},{url},answered
```

When all five return: **dedup the question set inline** — merge exact duplicates, keep near-duplicates that probe different aspects. You should land at ~25-35 unique questions. Then post a 2-3 line chat note: which way the personas converge, and the sharpest disagreement. Keep raw briefs out of chat.

## Phase 3: Map the contradictions and gaps (inline, no agents)

Working from the five interviews and the deduped question set, determine:

1. **Direct conflicts** — where two+ personas claim opposite things. Name the specific clashing claims.
2. **Strongest vs weakest evidence** — rank by source hierarchy: peer-reviewed causal > official data > single survey > analogy > preprint. Which persona is best-supported, which weakest, why.
3. **The resolving question** — the single empirical question that would settle the biggest contradiction.
4. **Universal agreement** — what every persona confirms, even opponents. The likely-true load-bearing finding.
5. **The blind spot** — what NO persona addressed (the "missing 6th lens").
6. **Open questions (gap list)** — every question tagged `thin`, `unverified`, or unanswered across all interviews. This is a first-class output, not an afterthought.

This map is raw material for the outline (Phase 4) and the report (Phase 5): findings, contradictions, 6th-lens box, frontier question, and the Open Questions section.

## Phase 4: Write the structured outline (STORM's core deliverable)

Emit the outline BEFORE the HTML. This is the artifact STORM's research shows carries the edge. Write to `storm-reports/{topic-slug}-outline.md` (create the folder if needed):

```markdown
# {Topic}
_STORM outline · panel: {discover|market} · {N} questions · {date}_

## 1. {Theme}
### 1.1 {Question group}
{synthesized answer} — [persona name], src: {url}
> CONTESTED: {Persona A claim} vs {Persona B claim}   ← inline where they clash
...

## N. Open Questions
- {question the loop could not close} — why: {no primary source | contested | out of scope}
```

Group the deduped Q&A into themes (H2/H3), arrange coherently, flag every contradiction inline, and end with the Open Questions section from Phase 3.6. Attribute claims to personas and keep source URLs.

## Phase 5: Render the HTML report

1. Read `report-template.html` in this skill folder. Clone it; do not rebuild the CSS.
2. The report is a render of the Phase 4 outline plus this skill's value-add sections. Fill every token:
   - **`{{METHOD_TAG}}` / `{{METHOD_LINE}}` / `{{PANEL_DISCLOSURE}}` / `{{LEDE}}`** — state the panel mode, the five persona roles actually used, interview depth, deduped question count, and verification.
   - **60-second summary** — decision-maker-grade; settled fact first, then contested interpretation.
   - **5 key findings, ranked by reliability** — highest reliability first; each a 1-10 confidence score (set in Phase 6) + Supported-by / Challenged-by chips from the contradiction map.
   - **Hidden connection** — the non-obvious link visible only across all personas.
   - **Missing 6th lens** — the Phase 3.5 blind spot, framed as the lens that could invert the conclusions.
   - **Actionable insight** — 3-6 specific moves for the Phase 0 reader role.
   - **Claim safety guide** — assert / caveat / avoid, populated after Phase 6.
   - **Open Questions** — the Phase 3.6 gap list (delete the section only if the loop closed everything).
   - **Frontier question** — select the sharpest item from Open Questions / the resolving question.
   - **Method & Lineage** — leave the STORM citation intact; fill `{{METHOD_LINE}}`.
   - **References** — every citation with a verification-status tag (set in Phase 6).
3. Write to `storm-reports/{topic-slug}-briefing.html`.

## Phase 6: Adversarial peer review + verification (do not skip)

This is what separates Storm Research from a normal report, and it is a layer the original STORM does not have. Run it before delivering.

**6a. Self-review (inline).** Score each of the 5 findings 1-10 for reliability and justify on the source hierarchy. Identify the weakest link and what would verify it. Run a bias check (which persona dominated the synthesis, what got underweighted). Name the missing 6th perspective. Assign an honest overall grade.

**6b. Verify every citation (parallel agents, Verification model tier).** Spawn agents in one message, one per distinct citation cluster (group related claims; ~4-6 agents). Each prompt:

```
Independently verify a citation against its PRIMARY source. Be skeptical; do not trust
secondary blog summaries. CLAIM: {claim + cited figure + named source}. Find the actual
primary source. Confirm or correct: exact title/authors/venue/year/URL, the real figure
or effect size as published, sample/method and any author-stated limits, and peer-review
status (published vs preprint). For any contested claim, find the strongest credible
counter-source. Return: VERDICT = CONFIRMED / PARTIALLY CONFIRMED (list corrections) /
UNVERIFIED / FALSE, then the corrected one-line citation, then 2-4 bullets of specifics
with the primary URL. Under 280 words.
```

**6c. Apply corrections.** Edit the report AND the outline:
- Fix wrong figures, titles, dates, or mischaracterizations.
- Downgrade confidence where evidence turned out thin; demote preprints and contested claims into the "Contested signal" sidebar.
- Re-attribute single-survey or commissioned stats honestly.
- Fill the verification banner (`X fabricated, Y corrected, Z demoted`) and per-citation status tags.
- Populate the claim safety guide from the verdicts.

## Output

1. **Two deliverables:** the STORM outline `storm-reports/{topic-slug}-outline.md` (the pre-writing artifact — the core STORM output) and the verified `storm-reports/{topic-slug}-briefing.html` (the polished render).
2. Open the HTML for the user with the platform's default opener: macOS `open <path>`, Linux `xdg-open <path>`, Windows `start "" <path>`. If the OS is unclear, just give the paths.
3. In chat, give: both file paths, the panel mode + deduped question count, the verification tally (`N/N checked, X fabricated, Y corrected, Z demoted`), the one universal finding, the top open question, and the claim safety summary. Keep it tight.

## Notes & guardrails

- **Real research only.** Every persona, answer, and citation must trace to a real, fetched source. No invented studies, numbers, or URLs. If a figure can't be verified, mark it `unverified`, demote or cut it; never paper over it.
- **Separate question-finding from answer-finding.** Phase 2 asks before it answers. Do not merge them into one pass — that is the STORM anti-pattern that collapses breadth.
- **The outline is the point.** Do not skip Phase 4. STORM's measured edge (+25 organization, +10 coverage) came from pre-writing structure, not prose polish.
- **The panel is author-built.** Always disclose it in the report. Agreement across personas is a strong hypothesis, not independent proof or field consensus.
- **Verification is mandatory.** A report delivered without Phase 6 is not a Storm Research report. The verification banner must be truthful.
- **Reliability = evidence quality, not confidence.** Score on the source hierarchy: peer-reviewed causal > official policy/financial data > single commissioned survey > analogy > preprint.
- **Persona quality cascades.** Use the Discovery model tier for Phase 1; do not cheap out. Never fable/Mythos.
- **Cost.** `discover` mode spawns ~14-18 agents per run (1 discovery + 5 interviews + 4-6 verifiers); `market` mode ~9-11 (no discovery). That is expected. Do not fan out wider than five personas or one verifier per citation cluster.
- **Design.** Editorial working-paper style (Fraunces display serif, Newsreader body, IBM Plex Mono for data, warm paper + pine accent). Keep the template `<style>` block intact and fill only the content tokens; do not swap in a different visual style. To rebrand, edit the `:root` custom properties.

## Appendix A: `market` preset personas

Used only in `market` mode (hype-check / competitive-narrative topics). Each runs the same Phase 2 interview loop.

1. **THE PRACTITIONER** — works with this daily. Surface the gap between what hands-on operators know and what academics/pundits miss; practical realities (workflow friction, what actually works, where it breaks). Bias: operator-grounded.
2. **THE ACADEMIC** — cares about peer-reviewed evidence and effect sizes, not anecdotes. What does rigorous evidence actually say vs popular belief, and where does it contradict the hype. Flag thin/contested evidence and peer-review status. Bias: rigor over relevance.
3. **THE SKEPTIC** — thinks the mainstream view is overstated. Build the strongest steelman bear case: backlash, failures, contradicting data, regulatory changes, debunkings. Rigorous, not contrarian for sport. Bias: distrusts the narrative.
4. **THE ECONOMIST** — follows the money: revenues, valuations, market size, funding, unit economics, incentives. Who profits from the current narrative and what shapes the hype. Bias: incentives explain everything.
5. **THE HISTORIAN** — has seen disruption cycles before. Genuine historical parallels (prior technologies, manias, market shifts) — who won, who lost, what stabilized. Bias: pattern-matches to the past.
