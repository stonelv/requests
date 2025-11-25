# GitHub Copilot Configuration for Large PRs

## Problem
When pull requests contain large data files or many changed files (e.g., PR #9 with 28 files and 1,296 additions including cached web content), GitHub Copilot may have difficulty accessing the complete file differences. This can result in Copilot only being able to retrieve PR metadata without the actual code changes.

## Solution
This repository uses a `.gitattributes` file to mark certain files as `linguist-generated`, which excludes them from:
- PR diff displays
- Language statistics
- Code review tools like GitHub Copilot

### Files Marked as Generated
The following patterns are marked as `linguist-generated=true`:
- `data/*.html` - Cached web content
- `data/*.json` - Cache index and metadata
- `data/*.txt` - Text cache files
- `test_urls.txt` - Test URL lists
- `bench_urls.txt` - Benchmark URL lists
- `*.cache` - Cache files
- `*.log` - Log files

### Benefits
1. **Improved Copilot Access**: GitHub Copilot can now access PR metadata and code diffs without being overwhelmed by large data files
2. **Faster PR Reviews**: Reviewers can focus on actual code changes without scrolling through generated content
3. **Cleaner Diffs**: PR diffs show only relevant code changes
4. **Better Language Stats**: Repository language statistics accurately reflect the codebase, not test data

## Best Practices
When contributing to this repository:
1. Avoid committing large data files or generated content directly to the repository
2. Use the `data/` directory for temporary cache files (which is gitignored)
3. If data files are necessary for tests, keep them minimal or use fixtures
4. Consider using external data sources or generating test data programmatically

## For Repository Maintainers
If you need to allow specific data files to be committed:
1. Add them to the repository first
2. Update `.gitattributes` to mark them as `linguist-generated=true`
3. Document why they're necessary in the PR description

## Testing the Configuration
To verify that files are properly marked:
```bash
# Check gitattributes for a specific file
git check-attr linguist-generated data/example.html

# Expected output:
# data/example.html: linguist-generated: true
```

## Related Issues
- PR #9: Added WebCache Explorer project with large cached data files
- Issue: Copilot unable to access file diffs due to PR size

## References
- [GitHub Linguist Documentation](https://github.com/github/linguist/blob/master/docs/overrides.md)
- [Git Attributes Documentation](https://git-scm.com/docs/gitattributes)
- [GitHub Copilot Best Practices](https://docs.github.com/en/copilot)
