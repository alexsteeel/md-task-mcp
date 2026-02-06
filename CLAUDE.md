# CLAUDE.md

## UV Tool Installation - Template Updates

When updating templates (HTML files in `templates/`), `uv tool install --force` does NOT update the cached template files due to uv caching.

**Solution:** Use `--no-cache` flag to force rebuild:
```bash
uv tool uninstall md-task-mcp
uv tool install --no-cache /media/bas/data/repo/github/md-task-mcp
```

Then restart tm-web.

## Screenshots and Private Data

NEVER commit screenshots or files that may contain private/sensitive data to the repository. The `.playwright-mcp/` folder is gitignored for this reason.

Before committing, verify no sensitive files are staged:
```bash
git status
```

## Git Commits

Before pushing commits, always verify the commit author matches the expected repository contributor:

```bash
git log --oneline -1 --format='%an <%ae>'
```

Expected author for this repo: `alexsteeel <bodrov.as.1989@gmail.com>`

If the author is incorrect, amend commits before pushing:

```bash
git commit --amend --author="alexsteeel <bodrov.as.1989@gmail.com>" --no-edit
```

For multiple commits, use interactive rebase with `exec`:

```bash
git rebase -i HEAD~N --exec 'git commit --amend --author="alexsteeel <bodrov.as.1989@gmail.com>" --no-edit'
```
