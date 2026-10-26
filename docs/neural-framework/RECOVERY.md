# Repository scope and local data

The user chose the smaller development repository on2026-10-24 and clarified that training will always run on
the original laptop. The full120GB workspace archive/upload was cancelled. Its snapshot, uploader and full-archive
verifier were stopped; no original data was deleted.

Use DEVELOPMENT_SETUP.md to clone and continue development. Source, models, schemas, tools, tests, required
fixtures/frozen replays, useful evaluation evidence, benchmark maps and the official Windows CLI are included.
The original training environment, raw training/self-play runs, large historical archives, compiler/package caches
and old experiment copies stay on this laptop. Their original paths remain in config/paths.json where applicable.
A fresh development laptop is not a replacement for that training-data store.

Generated partial full-backup output and exploratory clone/tool copies were preserved locally under
artifacts/local-only/cancelled-large-recovery/. That directory is ignored by Git. Original files in sibling work
folders, historical archives, CLI/SDK/map locations and references were not modified. Some early archival objects
had already reached GitHub before cancellation; they are removed from the development branch and are not part
of its clone. GitHub may retain unreachable LFS objects separately.

config/repository_scope.json records this decision. Old full-backup utilities remain for provenance, but their
bulk snapshot/upload workflow refuses to run in development-only mode. Do not restart it without new user
authorization. archive/history/project-before-lean.bundle preserves the local source/commit history before removing the
cancelled archive branch; it contains Git objects and LFS pointer metadata, not the huge LFS payloads.

Git text conversion is disabled to preserve exact frozen schedule/schema bytes. Do not regenerate protocol locks
or normalize immutable references to hide checkout differences. The new bot remains untrained/incomplete.
