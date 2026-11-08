# Setup: get the repo running and work with an AI

About 20 minutes the first time. You need a laptop (macOS, Windows or Linux) and a GitHub account.

## 1. Install the basics

- **git** (the tool that tracks versions of the code).
  - macOS: open Terminal and run `git --version`. If it is missing, macOS offers to install it.
  - Windows: install **Git for Windows** from https://git-scm.com. It includes **Git Bash**, a
    terminal where the commands below work.
  - Linux: `sudo apt install git` (or your distro's package manager).
- **Python 3** from https://www.python.org (3.10 or newer is safest). Check with `python3 --version`.
- Optional but useful: **GitHub CLI** (`gh`) from https://cli.github.com, then run `gh auth login`
  yourself. It lets the AI open pull requests for you.

## 2. Get the code and run it

```bash
git clone <the repo URL from GitHub>    # copy it from the green "Code" button
cd lumasync
./run.sh
```

`./run.sh` starts the prototype and opens **http://localhost:8765** in your browser (a page served
by your own laptop, not the internet). Read the script if anything fails; it is short. On Windows,
run it from Git Bash.

To test the DMX cable without the app, see [HARDWARE.md](HARDWARE.md):
`.venv/bin/python tools/dmx_test.py ports`.

## 3. Set up an AI assistant (pick one)

Both read this repo's instructions automatically, so they already know the project, the rules
and how we work. You need an account with the provider; what it costs depends on your plan.

### Option A: Claude Code

1. Install it from https://claude.com/claude-code (terminal version), or use Claude Code inside the Claude desktop
   app.
2. Open the `lumasync` folder in it (terminal: `cd lumasync` then `claude`).
3. It reads `CLAUDE.md` automatically, which points it to `AGENTS.md`.

### Option B: Codex

1. Install OpenAI's Codex (the CLI, the IDE extension or the app) from OpenAI's Codex page.
2. Open the `lumasync` folder in it (terminal: `cd lumasync` then `codex`).
3. It reads `AGENTS.md` automatically.

### Your first message (either one)

```
I'm <your name>, I own module <number>. Onboard me.
```

It will read the vision, the architecture, your module's brief and the status board, then tell you
what affects your work and what to do first.

## 4. Git in five words: branch, commit, push, pull request

- **Branch:** your own copy of the code to work on, so `main` stays working.
  `git switch -c <name>/<topic>` (e.g. `youtso/band-edges`).
- **Commit:** save a snapshot with a short message. `git add -A && git commit -m "what changed"`.
- **Push:** send your branch to GitHub. `git push -u origin <name>/<topic>`.
- **Pull request (PR):** ask the team to merge your branch into `main`. GitHub shows a button
  after you push. Someone reviews it, then it merges.
- **Get the latest:** `git switch main && git pull`.

Or just say: **"Save my work and open a pull request."** The AI does all of the above, names
the branch, updates your section of `team/STATUS.md`, and fills in the PR template.

## 5. Good prompts to start with

- "What should I work on next for my module?"
- "Explain how my module fits the system."
- "Give me options for <X> and help me decide."
- "Try building <Y> and test it against fakes."
- "What changed since I last worked?"
- "What would a good Dec 10 result for my module look like, and how do I measure it?"
- "Find two papers that back up this choice, from the citation bank first."
- "Explain <term> from first principles."

## 6. Ground rules (the AI follows these too)

- Work in your own module folder. Do not edit someone else's module.
- `lumasync/contract.py` changes only through a `contract` pull request that every owner approves.
- Real design choices get a decision record in `decisions/`, with **your** reasoning.
- The AI suggests and builds; **you decide**. You are marked on your module, so make sure you
  can explain every choice in it.
