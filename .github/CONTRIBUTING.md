# Contributing to nbs-pods

## Branches

| Branch | Role |
| --- | --- |
| `master` | Default integration branch. Day-to-day work lands here via pull request. Merging here **promotes** GHCR `:build` images to `:latest`. |
| `build` | Image-build branch (protected). Pushing here runs the image build workflow and updates GHCR `:build` only (not `:latest`). |
| feature branches | Short-lived. Open PRs into `master`. |

Do not open feature PRs into `build`. Prefer fast-forwarding `build` to the feature commit when you need new images.

## Image tags

| Tag | Meaning |
| --- | --- |
| `:build` | Last successful image build from the `build` branch. Pre-merge candidate; used by PR profile tests. |
| `:latest` | Promoted after merge to `master`. Default for beamlines and normal CLI use. |
| `:X.Y.Z` / `:X.Y` | Release tags, copied from `:latest` when you push a `v*` git tag. |

## Day-to-day development

### Host-only changes

CLI, docs, and other work that does **not** change what is baked into the container images:

1. Branch from `master`.
2. Open a PR into `master`. Profile tests pull GHCR `:build` (unchanged if you did not rebuild; typically the same digest as the last promote).
3. Merge. The promote workflow retags `:build` → `:latest`.

### Image-affecting changes

Containerfiles, image layers, or profile/pixi content shipped inside the images:

1. Land the work on a feature branch.
2. Fast-forward `build` to that commit and push:

```bash
git checkout build
git merge --ff-only my-feature
git push origin build
```

3. Wait for **Build and Push Container Images** to finish (updates `:build` only).
4. Open or update the PR into `master`. Profile tests use `:build`.
5. Merge. Promote retags `:build` → `:latest`.

Manual runs of the build workflow (`workflow_dispatch`) are available when a rebuild is needed without moving the branch.

## Cutting a release

Image releases **retag** the current `:latest` images; they do **not** rebuild from the git tag. Python packages publish when a GitHub Release is published.

**Never tag a release until `:latest` is the digest you intend** (usually right after a master merge that promoted a known-good `:build`).

1. Merge release work to `master` (after building on `build` if images changed) and confirm promote / `:latest`.
2. On that commit, create and push an annotated tag:

```bash
git checkout master
git tag -a vX.Y.Z -m "vX.Y.Z"
git push origin vX.Y.Z
```

3. Pushing `v*` runs **Re-tag Release Images**, which copies `:latest` to `:X.Y.Z` and `:X.Y` for each image.
4. Publish a GitHub Release for that tag. That runs **Upload Python Package** and publishes to PyPI.

Use `workflow_dispatch` on the retag workflow only for recovery (for example, re-applying a version from a known-good source tag), not as the normal release path.

## Workflow map

| Workflow | Trigger | Result |
| --- | --- | --- |
| [build-images.yml](workflows/build-images.yml) | Push to `build`, or manual | Build and push images; overwrite `:build` |
| [promote-build-to-latest.yml](workflows/promote-build-to-latest.yml) | Push to `master`, or manual | Retag `:build` → `:latest` |
| [retag-release.yml](workflows/retag-release.yml) | Tag `v*`, or manual | Promote `:latest` → `:VERSION` and `:MAJOR.MINOR` |
| [python-publish.yml](workflows/python-publish.yml) | GitHub Release published | Build and upload the Python package to PyPI |
| [profile-test.yml](workflows/profile-test.yml) | PR (uses `:build`), push to `master`/`main` (uses `:latest`), or manual | Unit tests; create a throwaway child and smoke its CLI/compose resolution; start sim stack and run profile pytest via queueserver `--test` |

## Testing

Profile tests live under `src/nbs_pods/config/ipython/profile_default/tests/` and run inside IPython after the demo profile starts.

CI also exercises child-repo creation: it runs `nbs-pods-create` (which pins `nbs-pods` to a PyPI version range from the current release), rewrites that pin to the checked-out tree for the PR, `pixi install`s the child, smokes the child CLI (`list`), and checks that beamline compose overrides resolve correctly. The full sim/`--test` stack still runs against the parent nbs-pods checkout — a blank child is not expected to be a runnable profile.

### Local images

Build images into the local prefix `localhost/nbs-<name>:latest` (does not touch GHCR):

```bash
pixi run build-images
# or a subset (built one at a time):
pixi run build-images queueserver sim
```

Builds run **serially**. Building several large pixi-based images in parallel from the same base often fails in podman with `io: read/write on closed pipe` while committing layers.

Then point the CLI at those images with `--local` (no env export needed):

```bash
nbs-pods start --local bluesky-services sim
nbs-pods start --local --teardown --test queueserver
# or
nbs-pods test --local --teardown
```

`--local` sets `NBS_IMAGE_REG=localhost/nbs-`. Override further with `--image-reg` / `--image-tag` if needed. Without `--local`, compose uses the default GHCR prefix (`:latest` unless you pass `--image-tag build`).

### Profile pytest

With published GHCR images:

```bash
nbs-pods start bluesky-services sim
nbs-pods start --teardown --test queueserver
```

Or the preset: `nbs-pods test --teardown`

Against the pre-merge candidate: `nbs-pods test --image-tag build`

With locally built images: `nbs-pods test --local --teardown`

`--test` takes the service names that follow it (`nargs="*"`), so put them immediately after `--test` — not after another flag like `--teardown`. It stacks `compose/queueserver/docker-compose.test.yml`, runs in the foreground with default task `qs-pytest` (override with `queueserver=qs-dev-pytest`), and only tears down if you pass `--teardown`. `--dev` is a boolean that stacks development mounts on every service in the same command (including `--test` services). Pick the pixi task with `SERVICE=TASK`:

```bash
nbs-pods start --dev bluesky-services sim queueserver=qs-dev
nbs-pods start --dev --teardown --test queueserver=qs-dev-pytest
```

Beamline repos that ship their own `docker-compose.test.yml` override the test mounts.

## Branch and release hygiene

- Protect `master`: require pull requests; disallow force-push.
- Protect / restrict who can push `build`.
- Restrict who can create `v*` tags and publish GitHub Releases.
