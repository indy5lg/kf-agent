# Set up
1. Install uv: [uv install link](https://docs.astral.sh/uv/getting-started/installation/)
2. Run `uv sync`

# Git Workflow

Ground rules for how we branch, review, and merge on this project.

## 1. Never commit directly to `main`

All work happens on a branch. `main` only changes through a reviewed pull request.

## 2. Branch naming

`<type>/<short-description>`, all lowercase, hyphen-separated.

| Type | Use it for |
|---|---|
| `feature` | New functionality |
| `fix` | Bug fixes |
| `chore` | Tooling, dependencies, config — no behavior change |
| `refactor` | Restructuring code without changing behavior |

Examples: `feature/login-registration`, `fix/session-cookie-expiry`, `chore/upgrade-fastapi`.

Keep the description 2–4 words and specific enough that `git branch` is self-explanatory without opening anything.

## 3. Every merge to `main` goes through a pull request

- No self-merging, ever — even for small changes.
- Get **one other teammate** to review and approve before merging.
- The reviewer should pull the branch and actually run it when the change touches something clickable or testable, not just read the diff.

## 4. Keep PRs small and focused

One PR = one logical change. If you notice something unrelated that needs fixing while you're in there, note it and open a separate PR — don't bundle it in.

## 5. Write a real PR description

At minimum:
- **What** changed and **why** (link the issue/task if there is one).
- **How you tested it** — commands run, screens clicked through, edge cases checked.

A reviewer shouldn't have to ask "wait, what does this do?" before they can review it.

## 6. Sync with `main` before opening a PR

```bash
git checkout main
git pull
git checkout your-branch
git merge main
```

Resolve conflicts on your own branch — don't let them surface for the first time during merge.

## 7. Delete your branch after it's merged

Keeps the branch list readable. GitHub will offer a "Delete branch" button right on the merged PR.

## 8. Never commit secrets

`.env` files, API keys, and credentials never get committed — only `.env.example` templates with placeholder values. If you're not sure whether something's sensitive, ask before pushing it.
