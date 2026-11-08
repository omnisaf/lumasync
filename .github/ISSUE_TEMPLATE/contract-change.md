---
name: Contract change
about: Propose a change to lumasync/contract.py (affects every module)
title: "Contract: "
labels: contract
---

**Proposed by:** <!-- name, module -->

## The change

<!-- Which type and field? Add / rename / remove / change meaning? Show the new line of code. -->

## Why

<!-- What can your module not do without it? -->

## Who is affected

- [ ] M1 Signal Processing of Audio
- [ ] M2 Lighting Control and LED Interface
- [ ] M3 Rhythm, Tempo and Transients
- [ ] M4 Superposition and Latency
- [ ] M5 Machine Learning

## Cost

- [ ] New **optional** field with a default (cheap: nobody has to change code)
- [ ] Rename, removal, or changed meaning (every affected module updates in the same PR)

## Process

1. Discuss here.
2. Open a PR labelled `contract`: change `contract.py`, bump `CONTRACT_VERSION`, update `fakes.py` and docs.
3. **Every module owner approves** the PR before merge.
