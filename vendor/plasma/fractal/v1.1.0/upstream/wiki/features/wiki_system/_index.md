---
name: features/wiki_system
desc: |
  The wiki system: the two knowledge stores, the wiki CLI, page and index
  conventions, and how wikis merge across branches.
created: 2026-07-21T04:35:35Z
updated: 2026-07-21T05:14:15Z
---

# features/wiki_system

[[features/_index|..]]

[[features/wiki_system/cli|cli]]: The wiki command-line interface: every verb's
contract, how a command resolves which wiki it targets, and the exit-code
discipline scripts rely on.

[[features/wiki_system/index_regeneration|index_regeneration]]: How derived wiki
state is regenerated: what wiki update rewrites, the update-then-lint loop,
issues versus advisory notes, and where the commit pipeline runs the refresh
automatically.

[[features/wiki_system/knowledge_stores|knowledge_stores]]: The two knowledge
stores a node works with: the shared project wiki and the node's private memory,
their locations, audiences, and how fractal creates and maintains each.

[[features/wiki_system/merge_behavior|merge_behavior]]: How wikis merge across
git branches: the custom merge driver for index files, which regions
auto-resolve versus conflict, and the parent's reconciliation duties after
integrating children.

[[features/wiki_system/page_conventions|page_conventions]]: Page and frontmatter
conventions: naming rules, leaf pages versus folders, which frontmatter keys are
authored versus regenerated, wikilink scoping, and the formatter interactions an
author must write around.

***

The wiki system is fractal's knowledge layer: every node works with two wikis —
the shared, git-tracked project wiki and its private per-node memory — both
maintained through the standalone `wiki` CLI and refreshed automatically by the
commit pipeline.

- [[features/wiki_system/knowledge_stores]] — the two stores, their locations
  and audiences, and how fractal creates and maintains each.
- [[features/wiki_system/cli]] — the CLI verbs, path resolution, and exit-code
  discipline.
- [[features/wiki_system/page_conventions]] — naming, frontmatter tiers, page
  bodies, and wikilink scoping.
- [[features/wiki_system/index_regeneration]] — what `wiki update` rewrites, the
  update/lint loop, and the automatic refresh at commit.
- [[features/wiki_system/merge_behavior]] — the index merge driver and the
  parent's reconciliation job after integrating children.
