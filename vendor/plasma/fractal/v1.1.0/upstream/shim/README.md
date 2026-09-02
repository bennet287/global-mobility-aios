# fractal

[![license](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](https://github.com/plasma-ai/fractal/blob/main/LICENSE)
[![build](https://github.com/plasma-ai/fractal/actions/workflows/build.yaml/badge.svg)](https://github.com/plasma-ai/fractal/actions/workflows/build.yaml)
[![docs](https://github.com/plasma-ai/fractal/actions/workflows/docs.yaml/badge.svg)](https://github.com/plasma-ai/fractal/actions/workflows/docs.yaml)
[![lint](https://github.com/plasma-ai/fractal/actions/workflows/lint.yaml/badge.svg)](https://github.com/plasma-ai/fractal/actions/workflows/lint.yaml)
[![tests](https://github.com/plasma-ai/fractal/actions/workflows/tests.yaml/badge.svg)](https://github.com/plasma-ai/fractal/actions/workflows/tests.yaml)
[![codecov](https://codecov.io/gh/plasma-ai/fractal/branch/main/graph/badge.svg?token=FB0T12O2ZP)](https://codecov.io/gh/plasma-ai/fractal)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](https://github.com/pre-commit/pre-commit)

Hierarchical agent loops with recursive self-organization.

In a fractal, autonomous agent loops arrange themselves into a tree: a node
iterates toward a goal in its own `git worktree` and spawns child nodes for
separable subtasks, so the tree grows to fit the problem rather than a fixed
plan. Hard caps (iterations, depth, children, cost, time) keep each loop
bounded, and an operator can steer or stop it at any point. Run metadata
(including cost) lands in one local `SQLite` database, which can be interacted
with live in a terminal UI.

______________________________________________________________________

**Source**:
[https://github.com/plasma-ai/fractal](https://github.com/plasma-ai/fractal)

**Package**:
[https://pypi.org/project/plasma-fractal/](https://pypi.org/project/plasma-fractal/)

**Documentation**:
[https://docs.plasma.ai/fractal](https://docs.plasma.ai/fractal)

______________________________________________________________________

This package is a pointer to
[`plasma-fractal`](https://pypi.org/project/plasma-fractal/) and contains no
code. Each release pins the matching `plasma-fractal` release exactly, so the
two names are interchangeable:

```bash
pip install fractal
```

installs `plasma-fractal`. Versions of `fractal` before 1.0.0 were an unrelated
package from a previous owner of the name; the pointer begins at 1.0.0.

## License

Licensed under the Apache License 2.0 — see
[LICENSE](https://github.com/plasma-ai/fractal/blob/main/LICENSE).

Copyright © 2026 Plasma AI
