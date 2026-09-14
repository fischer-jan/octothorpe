# Dependabot triage — one-time setup

`.github/workflows/dependabot.yml` auto-merges dependency pull requests that
carry no major version bump, and sends the ones that do to Grok for review. It
needs two **repository secrets** (Settings → Secrets and variables → Actions →
Secrets). Until both exist it explains what is missing and goes green.

| Secret | What it is | Why |
|--------|------------|-----|
| `XAI_API_KEY` | the same xAI key KanBanito uses | pays for the major-bump reviews |
| `AUTOMERGE_TOKEN` | a fine-grained personal access token scoped to this repo | performs the merge |

## How a major bump reaches you

It needs no secret at all. The workflow assigns the pull request to the
repository owner and mentions them in the review comment.

Assignment rather than email, on purpose. This job checks out and runs code
from the pull request under review, so extra credentials (SMTP, a second API)
are a risk. Assignment also parks the pull request in **Assigned to you**.

If the mention still gets lost among Dependabot's other mail, filter on:

```
X-GitHub-Reason: mention
```

## Why the merge needs its own token

A merge performed with the built-in `GITHUB_TOKEN` does not trigger further
workflows. The PAT is so the squash onto `main` still runs CI.

Create it at **Settings → Developer settings → Personal access tokens →
Fine-grained tokens**:

- Repository access: **only** `fischer-jan/octothorpe`
- Permissions: `Contents: Read and write`, `Pull requests: Read and write`
- Expiry: whatever you'll remember to renew. When it lapses the workflow goes
  green and says what is missing, so an expired token stalls merges rather than
  breaking the repo.

You can reuse KanBanito's `AUTOMERGE_TOKEN` only if that token is also granted
this repository. A KanBanito-only token will not merge here.

## What happens then

| | |
|---|---|
| Bump with no major | CI passes → squash-merged and branch deleted |
| Bump with a major | CI passes → labelled `dependency-major`, assigned, review posted → waits |
| Review says risk NONE | still waits. The review informs the decision; it does not make it |
| Pull request fell behind `main` | comment `@dependabot rebase`; CI and triage run again |

Try the review by hand:

```bash
python3 scripts/review-major-bump.py <pr-number> --dry-run
python3 scripts/review-major-bump.py <pr-number>
```
