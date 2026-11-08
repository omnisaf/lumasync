# Onboarding: our first team session

**30–45 minutes, all five of us, laptops open.** Run it right after the meeting with Dr. Chen,
while the questions are fresh. One person drives the screen; everyone talks.

By the end, each of us has: the repo running, an AI set up, a confirmed module, a one-line spec,
and a first test to run this week.

---

## 1. Read the vision together (5 min)

Open [VISION.md](VISION.md) on the big screen. Read it top to bottom. Stop at anything unclear.

The three ideas to leave with:
- **Baseline:** the show runs well from a laptop mic alone, plus one layer on top (DJ controls
  over MIDI).
- **Superposition:** every other input is a layer on top. A missing layer counts for zero; the
  show still runs.
- **Hyper-modularity:** inputs and outputs are swappable. Modules only talk through the contract.

## 2. See the prototype run (5 min)

On one laptop: `./run.sh`, then open http://localhost:8765. Play some music near the mic.

What to notice: this is a **first draft built for the team** so the whole chain runs from day one.
Each module folder holds a rough version of that module. Your job from today is to own your piece:
measure it, question it, replace it.

Quick look at [ARCHITECTURE.md](ARCHITECTURE.md): the pipeline diagram and the contract table.

## 3. Module assignment round (10 min)

The modules were assigned in our proposal. Confirm or re-assign each one now. Fill in
[team/ROSTER.md](../team/ROSTER.md) live, and change "proposed" to "confirmed".

| # | Module | Proposed owner |
|---|---|---|
| 1 | Signal Processing of Audio | Youtso |
| 2 | Real-Time Adaptive Lighting Control and LED Interface | Mo |
| 3 | Rhythm, Tempo and Transient Detection | Rohan or Remsha |
| 4 | Superposition of Inputs and Latency Optimization | Sathvik |
| 5 | Machine Learning: Mood and Crowd-Energy Estimation | Rohan or Remsha |

Two things to settle:

- **Who owns 3, and who owns 5?** Read the "core engineering challenge" in each
  [MODULE.md](../lumasync/m3_rhythm/MODULE.md) ([M5](../lumasync/m5_recognition/MODULE.md)) and pick
  by interest. Module 3 is signal timing (when things happen). Module 5 is machine learning
  (what kind of music this is).
- **Module 5's name.** In the prototype, song recognition (matching live audio against our song
  library by fingerprint) lives in module 5. Options:
  - keep "Machine Learning: Mood and Crowd-Energy Estimation", and treat recognition as part of it;
  - rename to "Machine Learning: Music Recognition and Mood Estimation", with crowd energy as an
    add-on;
  - move recognition somewhere else.

  Talk through it: does the name match the work, and is the module balanced against the others?
  Modules change only if necessary. Write the result as `decisions/007-module-5-scope.md` (see
  [decisions/003-five-modules.md](../decisions/003-five-modules.md)).

Also add everyone's **GitHub username** to the roster, so the repo owner can add them.

## 4. Set up your AI (10 min, everyone at once)

Follow [SETUP.md](SETUP.md): clone, `./run.sh`, install Claude Code or Codex, open the folder.
Then send the first message:

```
I'm <your name>, I own module <number>. Onboard me.
```

If someone gets stuck, pair up. Nobody leaves without this working.

## 5. Your one-liner (5 min)

Each person says, then writes in their section of [team/STATUS.md](../team/STATUS.md):

> My module takes in **X**, gives out **Y**, and my first test is **Z**.

Use the contract type names for X and Y. Z should be something you can run this week against
fakes or recorded audio. Example for module 3: "takes in `AudioFrame`, gives out `RhythmState`,
my first test is beat times on five recorded tracks against tapped-in beats".

Ask your AI to help word it.

## 6. First team decisions (5–10 min to list, owners to follow up)

These are open. Do not solve them all now. Give each one an owner and a date.

1. **Owners for modules 3 and 5**, and module 5's name (step 3).
2. **What "one third of deliverables" means for Dec 10**: per module, or the whole system? Ask
   Dr. Chen. Then each owner sets a Dec 10 target (each `MODULE.md` suggests one).
3. **First live test at Resonnce.** The DMX cable has not been tested on a light yet. Pick a date
   for a short session: run `tools/dmx_test.py walk` on the rig and write down the channel maps.
4. **Rig facts to confirm:** a photo of an LPC1818 display (`A001` or `d001`), the blinder model,
   3-pin or 5-pin DMX.
5. **Which MIDI controller** for the promised MIDI layer, and how MIDI enters the contract
   (today `LiveControls` says "UI / MIDI later"). Needs modules 4 and 2 at least.
6. **Line-in from the mixer:** baseline or add-on? It is the cheapest upgrade and may make every
   other feature work better.
7. **How we measure "good":** beat-sync error, end-to-end latency, a DJ or crowd survey?
8. **Who it helps outside clubs:** which one or two angles lead the report.
9. **Parts and budget:** who orders the ESP32 node, terminator and line-in interface
   ([HARDWARE.md](HARDWARE.md) §9).

Each decision that gets made goes in `decisions/` with the reasoning.

## How we keep in sync after today

- **[team/STATUS.md](../team/STATUS.md)** is the main centre. Your AI updates your section at the
  end of every session. Read the top section before the Wednesday meeting.
- **Wednesday meetings** (from our proposal): each person gives their update from STATUS.md.
- **Dr. Chen meetings** about every 2 weeks. −3% for each one missed. Never miss one.
- **Pull requests** for every change. Contract changes need every owner's approval.
