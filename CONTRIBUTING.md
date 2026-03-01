# Contributing

## Releases

This project uses [semantic-release](https://semantic-release.gitbook.io/) to automate versioning and publishing. The CI workflow (`.github/workflows/docker-publish.yml`) runs `npx semantic-release` which:

1. Analyzes commit messages since the last git tag
2. Determines the next version bump (patch/minor/major)
3. Creates a GitHub release, builds, and publishes the Docker image

For semantic-release to detect a version change, commits must follow the [Conventional Commits](https://www.conventionalcommits.org/) format (e.g., `fix:`, `feat:`).

## Reverting Changes

**Never use `git reset` + force-push** to undo commits on `main`. This rewrites history and breaks semantic-release because there are no new commits ahead of the last tag, so no version bump is detected and no build/publish occurs.

**Instead, use `git revert`** to create a new forward commit:

```bash
# Revert the last commit
git revert HEAD

# IMPORTANT: amend the message with a conventional commit prefix
git commit --amend -m "fix: revert <short description of what you're reverting>"
```

This ensures:

- History is preserved (no force-push needed)
- Semantic-release detects the new commit and bumps the version
- A new Docker image is built and published
- The server can be updated to the new version

### Why this matters

| Approach | New commit? | Version bump? | Build + publish? |
|-|-|-|-|
| `git revert` with `fix:` prefix | Yes | Yes | Yes |
| `git revert` (default message) | Yes | No | No |
| `git reset --hard` + force-push | No | No | No |
