# Prompt: make local repositories writable

```text
Use the repository list in repo_manifest.json as the complete scope. First inspect
make_repos_writable.py and explain what it will change. Run it without --apply to
show the dry-run plan. Do not apply changes unless I explicitly authorize it.

The script should add only the current user's write bit to regular files and
directories under each listed repository. It must preserve all other permission
bits, must not follow or modify symlinks, and must not change anything outside
the listed repositories. Report any inspection errors and do not apply changes
if inspection fails. Never broaden permissions for a whole group or all users.
```
