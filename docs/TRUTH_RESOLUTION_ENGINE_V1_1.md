# Truth Resolution Engine v1.1

## Fix

This patch fixes the admin truth-resolution dashboard stage counter.

The v1 admin dashboard built `stage_counts` using:

```python
stage_counts[item["stage"]] = stage_counts.get(stage, 0) + 1
```

but `stage` had not been assigned yet, causing:

```text
NameError: name 'stage' is not defined
```

The corrected logic is:

```python
stage = item["stage"]
stage_counts[stage] = stage_counts.get(stage, 0) + 1
```

## Scope

- API truth-resolution endpoint was already working.
- Admin dashboard `/admin/truth-resolution` is fixed.
- No database migration is required.
