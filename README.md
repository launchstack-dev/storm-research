# Storm Research (skill)

A Claude Code skill that runs Stanford's **STORM** research method on any topic and
produces two artifacts: a structured **outline** (`.md`) and a verified, self-contained
**HTML briefing**.

## Files

- `SKILL.md` — the 6-phase pipeline Claude executes. This is the skill.
- `report-template.html` — the HTML report template the skill clones in Phase 5. Keep
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
  - `discover` (**default**) — Claude derives 5 personas that fit *your* topic
    (domain expert / practitioner / skeptic / newcomer / adjacent expert). Best for
    decision-support and technical/product topics.
  - `market` — the fixed hype-check panel (practitioner / academic / skeptic /
    economist / historian). Best for "is `<trend>` overhyped / real / a bubble".
- `--model-profile fast|balanced|max` — shifts model tiers together. Default `balanced`
  (opus discovery · sonnet interviews · sonnet verification).

## What you get

1. `storm-reports/<slug>-outline.md` — the STORM outline (themes, inline contradictions,
   open questions). **This is STORM's core deliverable** — the pre-writing structure is
   where the method's measured edge comes from.
2. `storm-reports/<slug>-briefing.html` — the polished, citation-verified report, opened
   automatically.

Both land in `storm-reports/` relative to your current working directory.

## When to use it (and when not)

- **Use** for multi-stakeholder decisions, competitive/market analysis, due diligence,
  and any topic where viewpoint breadth and fact-checked claims matter.
- **Don't use** for a simple factual lookup — it spawns ~14–18 agents in `discover`
  mode (~9–11 in `market`) and takes minutes. That cost is the point; it's deliberate.

## Cost & model notes

- Reasoning-heavy phases (persona discovery, interviews) route to strong models;
  citation verification routes to a lighter tier. See the routing table in `SKILL.md`.
- Never uses a fable/Mythos tier (exhausts usage limits under fan-out).

## Provenance & attribution

This skill adapts **STORM** — *Assisting in Writing Wikipedia-like Articles From Scratch
with Large Language Models*, Shao, Jiang, Kanell, Xu, Khattab & Lam, **NAACL 2024**,
Stanford OVAL Lab. Reference implementation: `github.com/stanford-oval/storm`
(`pip install knowledge-storm`); live demo: `storm-project.stanford.edu`.

**What this skill adds beyond the original method:** an adversarial primary-source
**verification layer** (confirm/correct/demote every citation), reliability scoring on an
explicit evidence hierarchy, an honesty disclosure (the persona panel is author-built —
agreement is a strong hypothesis, not field consensus), reader-role targeting, and a
claim-safety guide. Those are not in the Stanford paper.

The original SKILL/template were seeded from a community package (MindStudio / Linas
Beliūnas "Boardroom STORM" lineage) and were substantially rewritten here to restore
STORM fidelity (perspective discovery + interview loop + outline-first output). Marketing
/ video links from the source distribution were intentionally dropped.

## Design

The report template is a self-contained editorial layout — constrained palette via CSS
custom properties, Montserrat / Roboto / Roboto Mono type system, print + mobile styles.
It is deliberately restrained (not a generic gradient/emoji "AI" look) and does not depend
on any external design system. To restyle for a specific brand, edit the `:root` tokens
and the `<style>` block; the skill body's Phase 5 only fills content tokens.
