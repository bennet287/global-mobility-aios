# Examples

Runnable, self-contained walkthroughs. Each script builds everything in a
scratch directory and never touches the repository it lives in.

- [`hello.sh`](hello.sh) -- the setup walkthrough, end to end: scratch repo,
  `fractal init`, wiki scaffold commit, and a capped `hello` node with a real
  mission authored into its NODE.md. Everything up to `fractal node start` runs
  for real; the start, watch, and merge commands are printed instead of run, so
  the walkthrough is free.

```bash
bash examples/hello.sh --dir=/tmp/hello --agent=claude
```
