# 001 — The repo works through a contract, decision records, a status board and an AI sparring partner

- **Status:** proposed (for the team to accept at the first session)
- **Module:** whole team
- **Decided by:** to be confirmed by the team · **Date:** 2026-11-08

## Context

Five people build five modules at the same time, and each person is marked on their own module.
Our proposal already commits to GitHub for code and task tracking, weekly Wednesday meetings and
a Teams chat. What we need on top: a way to build in parallel without waiting on each other, a
record of why each choice was made (the reports need it), and a way for everyone to use AI tools
without the AI quietly making decisions for us.

## Options

1. **Shared code, coordinate in chat.** Everyone edits anything; we sort it out in Teams.
   Fast at first. Breaks as soon as two people change the same thing, and the reasoning is lost
   in chat. Test: count how often we redo work.
2. **Contract-only coupling, one module per folder, decisions and status in the repo, AI reads
   the same rules.** More structure up front. Each person can work and test alone. The reasons
   for choices are written down where the report writer will find them.
3. **A project-management tool outside the repo** (GitHub Projects, Notion). Good overview. A
   second place to keep updated, and the AI cannot easily read it.

## Decision

Option 2:
- **Contract-only coupling.** Modules share only the types in `lumasync/contract.py`. Changes go
  through a `contract` pull request that every owner approves.
- **One folder per module**, each with a `MODULE.md` brief. Code is tested against fakes.
- **Decision records** in `decisions/` for every real design choice, with the decider's own
  reasoning quoted.
- **A status board**, `team/STATUS.md`, updated at the end of every work session.
- **An AI sparring partner.** `AGENTS.md` tells the AI to catch each person up, lay out options
  and trade-offs, let the person decide, and write the record. It builds code only inside that
  person's module.
- **Both Claude Code and Codex work.** Codex reads `AGENTS.md`; Claude Code reads `CLAUDE.md`,
  which points to `AGENTS.md`. One set of rules, whichever tool you prefer.

## Why

Summary of the reasoning (to be replaced by the team's own words when accepted):
- Parallel work is a course rule, and the contract is what makes it real.
- Marks are individual, so each person must own and explain their choices. An AI that decides for
  you would make that harder; one that asks you to decide makes it easier.
- Writing the reasoning down as we go means the Dec 10 and April reports are half-written by the
  time we need them.

> (team reasoning to add)

## How we'd know we were wrong

- People skip STATUS.md updates for two weeks in a row → the board is too heavy; simplify it.
- Contract pull requests sit unapproved for more than a few days → the approval rule is too
  strict; agree a faster path for optional fields.
- Decision records are empty boilerplate → too many trivial records; raise the bar.
