# Storm Research (skill)

A Claude Code skill that runs Stanford's **STORM** research method on any topic and
produces two artifacts: a structured **outline** (`.md`) and a verified, self-contained
**HTML briefing**.

## Files

- `SKILL.md` — the pipeline Claude executes. This is the skill.
- `report-template.html` — the HTML report template the skill clones in Phase 6. Keep
  the `<style>` block verbatim; fill the `{{TOKENS}}`.
- `README.md` — this file (provenance + usage).

## Install

Drop the folder into your Claude Code skills directory (personal or project):

```bash
git clone https://github.com/launchstack-dev/storm-research.git ~/.claude/skills/storm-research
```

Claude Code discovers it on the next session start. Works in any repo; also portable to
other agent runtimes that read `.claude/skills/`.

## How to invoke

No slash command. Just say it in chat:

- "run storm research on `<topic>`"
- "storm report on `<topic>`"
- "give me a STORM briefing on `<topic>`"

Optional arguments (state them in the request):

- `--panel discover|market`
  - `discover` (**default**) — Claude reads 3-5 overview sources on your topic and
    derives 5 personas from them (domain expert / practitioner / skeptic / basic-facts
    writer / adjacent expert). Best for decision-support and technical/product topics.
  - `market` — the fixed hype-check panel (practitioner / academic / skeptic /
    economist / historian). Best for "is `<trend>` overhyped / real / a bubble".
- `--model-profile fast|balanced|max` — shifts model tiers together. Default `balanced`
  (opus discovery and review · sonnet interviews, moderator and verification).
- `resume <run folder>` — continue a run that stopped; it restarts at the first missing file.

## What you get

Each run gets its own folder, `storm-reports/<slug>-<date>/` relative to your current
working directory (never overwritten; a same-day rerun gets `-2`):

1. `outline.md` — the STORM outline (themes, inline contradictions, open questions), every
   claim tied to the ledger. **This is STORM's core deliverable** — the pre-writing
   structure is where the method's measured edge comes from.
2. `briefing.html` — the polished report with numbered, verified citations, opened (or
   published as a private artifact where the session can).
3. The audit trail: `personas.md`, `interviews/`, `moderator.md`, `ledger.md` (every claim
   with its source, date, verbatim quote, grade and verdict), `verification.md`.

## When to use it (and when not)

- **Use** for multi-stakeholder decisions, competitive/market analysis, due diligence,
  and any topic where viewpoint breadth and fact-checked claims matter.
- **Don't use** for a simple factual lookup — it spawns ~16–17 agents in `discover`
  mode (~15–16 in `market`) plus retries, and takes a while. That cost is the point; it's deliberate.

## Cost & model notes

- Reasoning-heavy single agents (persona discovery, the independent reviewer) route to
  the strongest tier; fan-outs (interviews, verifiers) to a lighter one. See the routing
  table in `SKILL.md`.
- A `fable` tier is used only under `max`, and only for single agents — never for a
  fan-out (it exhausts usage limits).

## Provenance & attribution

This skill adapts **STORM** — *Assisting in Writing Wikipedia-like Articles From Scratch
with Large Language Models*, Shao, Jiang, Kanell, Xu, Khattab & Lam, **NAACL 2024**,
Stanford OVAL Lab. Reference implementation: `github.com/stanford-oval/storm`
(`pip install knowledge-storm`); live demo: `storm-project.stanford.edu`.

**What it keeps from STORM / Co-STORM** (checked against `knowledge_storm`): personas
derived from related sources' structure plus a basic-facts writer, a turn-by-turn
interview (each question written from the previous answers, before searching),
multi-query grounded answers with untrustworthy sources excluded, a Co-STORM-style
moderator that researches retrieved-but-unused evidence, a draft-then-refine outline,
and sections written from their own evidence with numbered citations, lead last.

**What this skill adds beyond the original method:** a claims ledger (source, date,
verbatim quote, grade per claim), an adversarial primary-source **verification layer**
over every cited claim (fetch failures are never called fabrication; every FALSE is
re-checked by the main session), an independent reviewer, checkpointed and resumable
runs, reliability scoring on an
explicit evidence hierarchy, an honesty disclosure (the persona panel is author-built —
agreement is a strong hypothesis, not field consensus), reader-role targeting, and a
claim-safety guide. Those are not in the Stanford paper.

The original SKILL/template were seeded from a community package (MindStudio / Linas
Beliūnas "Boardroom STORM" lineage) and were substantially rewritten here to restore
STORM fidelity (perspective discovery + interview loop + outline-first output). Marketing
/ video links from the source distribution were intentionally dropped.

## Design

The report template is an original editorial "working-paper" layout — Fraunces display
serif, Newsreader body, IBM Plex Mono for data labels, a warm-paper palette with a pine
accent, all via CSS custom properties, plus print + mobile styles. It is deliberately
restrained (not a generic gradient/emoji "AI" look) and does not depend on any external
design system. To restyle for a specific brand, edit the `:root` tokens and the `<style>`
block; the skill body's Phase 5 only fills content tokens.
