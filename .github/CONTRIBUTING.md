# Contributing to nbs-pods

## Branches

| Branch | Role |
| --- | --- |
| `master` | Default integration branch. Day-to-day work lands here via pull request. Merging here does **not** publish container images. |
| `build` | Promote branch. Advancing this branch triggers the image build workflow and updates GHCR `:latest`. |
| feature branches | Short-lived. Open PRs into `master`. |

Do not open feature PRs into `build`. Prefer keeping `build` a fast-forward of `master` so it never diverges.

## Day-to-day development

1. Branch from `master`.
2. Open a pull request into `master` and merge when ready.
3. When container images should update, fast-forward `build` to `master` and push:

```bash
git checkout build
git merge --ff-only master
git push origin build
```

4. Confirm the **Build and Push Container Images** workflow succeeded, then smoke-test `:latest` if needed.

Manual runs of that workflow (`workflow_dispatch`) are available when a rebuild is needed without moving the branch.

## Cutting a release

Image releases **retag** the current `:latest` images; they do **not** rebuild from the git tag. Python packages publish when a GitHub Release is published.

**Never tag a release until the intended commit is on `build` and the image build has finished.** Otherwise version tags can point at the wrong image digest.

1. Merge all release work to `master`.
2. Fast-forward `build` to that commit and wait for image CI to finish.
3. Verify GHCR `:latest` is good.
4. On the same commit, create and push an annotated tag:

```bash
git checkout master
git tag -a vX.Y.Z -m "vX.Y.Z"
git push origin vX.Y.Z
```

5. Pushing `v*` runs **Re-tag Release Images**, which copies `:latest` to `:X.Y.Z` and `:X.Y` for each image.
6. Publish a GitHub Release for that tag. That runs **Upload Python Package** and publishes to PyPI.

Use `workflow_dispatch` on the retag workflow only for recovery (for example, re-applying a version from a known-good source tag), not as the normal release path.

## Workflow map

| Workflow | Trigger | Result |
| --- | --- | --- |
| [build-images.yml](workflows/build-images.yml) | Push to `build`, or manual | Build and push images; overwrite `:latest` |
| [retag-release.yml](workflows/retag-release.yml) | Tag `v*`, or manual | Promote `:latest` → `:VERSION` and `:MAJOR.MINOR` |
| [python-publish.yml](workflows/python-publish.yml) | GitHub Release published | Build and upload the Python package to PyPI |
| [profile-test.yml](workflows/profile-test.yml) | PR, push to `master`/`main`, or manual | Start sim stack and run profile pytest via queueserver `--test` |

## Testing

Profile tests live under `src/nbs_pods/config/ipython/profile_default/tests/` and run inside IPython after the demo profile starts.

### Local images

Build images into the local prefix `localhost/nbs-<name>:latest` (does not touch GHCR):

```bash
pixi run build-images
# or a subset (built one at a time):
pixi run build-images -- queueserver sim
```

Builds run **serially**. Building several large pixi-based images in parallel from the same base often fails in podman with `io: read/write on closed pipe` while committing layers.

Then point the CLI at those images with `--local` (no env export needed):

```bash
nbs-pods start --local bluesky-services sim
nbs-pods start --local --test --teardown queueserver
# or
nbs-pods test --local --teardown
```

`--local` sets `NBS_IMAGE_REG=localhost/nbs-`. Override further with `--image-reg` / `--image-tag` if needed. Without `--local`, compose uses the default GHCR prefix.

### Profile pytest

With published GHCR images:

```bash
nbs-pods start bluesky-services sim
nbs-pods start --test --teardown queueserver
```

Or the preset: `nbs-pods test --teardown`

With locally built images: `nbs-pods test --local --teardown`

`--test queueserver` stacks `compose/queueserver/docker-compose.test.yml`, runs in the foreground with default task `qs-pytest` (override with `queueserver=qs-dev-pytest`), and only tears down if you pass `--teardown`. `--dev` is a boolean that stacks development mounts on every service in the same command (including `--test` services). Pick the pixi task with `SERVICE=TASK`:

```bash
nbs-pods start --dev bluesky-services sim queueserver=qs-dev
nbs-pods start --dev --test --teardown queueserver=qs-dev-pytest
```

Beamline repos that ship their own `docker-compose.test.yml` override the test mounts.

## Branch and release hygiene

- Protect `master`: require pull requests; disallow force-push.
- Restrict who can push to `build`; keep merges fast-forward-only from `master`.
- Restrict who can create `v*` tags and publish GitHub Releases.
