# Example: How .gitattributes Fixes Copilot PR Access

This example demonstrates how the `.gitattributes` configuration solves the problem where GitHub Copilot cannot access file diffs in pull requests containing large data files.

## The Problem

Before adding `.gitattributes`, PR #9 contained:
- 28 changed files
- 1,296 additions
- Large data files (e.g., `data/httpbin.org_encoding_utf8.html` with 220 lines)

When trying to access this PR, GitHub Copilot could retrieve:
- ✅ PR metadata (title, description, status)
- ❌ File diffs (the actual code changes)

This is because GitHub's API has limits on the size of diffs that can be accessed, and large data files exceeded these limits.

## The Solution

By adding `.gitattributes` with the following content:

```gitattributes
# Mark data files as linguist-generated
data/*.html linguist-generated=true
data/*.json linguist-generated=true
data/**/*.html linguist-generated=true
data/**/*.json linguist-generated=true
test_urls.txt linguist-generated=true
bench_urls.txt linguist-generated=true
```

Now when Copilot accesses the PR:
- ✅ PR metadata (title, description, status)
- ✅ File diffs for code files (excluding marked data files)
- ℹ️  Data files are still in the repository but excluded from diff views

## Testing the Configuration

You can verify this works by running:

```bash
# Check if a data file is marked as linguist-generated
$ git check-attr linguist-generated data/example.html
data/example.html: linguist-generated: true

# Check if a code file is NOT marked
$ git check-attr linguist-generated src/requests/api.py
src/requests/api.py: linguist-generated: unspecified
```

Or use the provided test script:

```bash
$ python test_copilot_setup.py
Testing .gitattributes configuration for Copilot PR access...
======================================================================
✓ PASS: Data HTML files should be linguist-generated
✓ PASS: Data JSON files should be linguist-generated
✓ PASS: Test URL files should be linguist-generated
✓ PASS: Config files should not be linguist-generated
✓ PASS: Documentation should not be linguist-generated
======================================================================
Results: 5 passed, 0 failed

✅ All tests passed! Copilot should now be able to access PR diffs.
```

## How It Works

1. **linguist-generated attribute**: This Git attribute tells GitHub's Linguist tool (which powers language detection and diff display) to treat these files as auto-generated content.

2. **Excluded from diffs**: Files marked as `linguist-generated` are:
   - Collapsed by default in PR diffs
   - Excluded from language statistics
   - Not processed by Copilot when analyzing PRs

3. **Still in repository**: The files remain in Git history and can be viewed individually, but they don't bloat PR diffs.

## Best Practices

### For New Projects

If you're starting a new project that might generate large data files:

1. Add `.gitattributes` early:
   ```bash
   echo "data/*.html linguist-generated=true" > .gitattributes
   ```

2. Update `.gitignore` to exclude data by default:
   ```bash
   echo "data/" >> .gitignore
   echo "!data/.gitkeep" >> .gitignore
   ```

3. Document why files are marked as generated in your README or CONTRIBUTING guide.

### For Existing Projects

If you're fixing an existing repository with large PRs:

1. Add `.gitattributes` to mark existing data files
2. The attribute applies to future commits/PRs immediately
3. Existing PRs may still have issues, but new PRs will work correctly

### Files to Mark as Generated

Consider marking these types of files:
- Cache files (`.cache`, `*.cache`)
- Downloaded content (`data/*.html`, `downloads/*`)
- Generated test fixtures (`fixtures/generated/*`)
- Build artifacts that must be committed (`dist/*.min.js`)
- Large log files (`logs/*.log`)
- Compiled assets (`assets/compiled/*`)

### Files NOT to Mark as Generated

Don't mark these as generated:
- Source code files (`.py`, `.js`, `.java`, etc.)
- Configuration files (`.yml`, `.toml`, `.json` config files)
- Documentation (`.md`, `.rst`, `.txt` docs)
- Test code (`test_*.py`, `*_test.go`)
- Build scripts (`Makefile`, `build.sh`)

## Verifying Copilot Access

After applying this fix, you can verify Copilot can access your PRs by:

1. Opening a PR with data files
2. Using GitHub Copilot to ask about the PR:
   - "What changes are in this PR?"
   - "Summarize the code changes"
   - "Review this PR"

3. Copilot should now be able to:
   - See all code file changes
   - Ignore marked data files
   - Provide meaningful summaries and reviews

## Additional Resources

- [GitHub Linguist Documentation](https://github.com/github/linguist/blob/master/docs/overrides.md)
- [Git Attributes Documentation](https://git-scm.com/docs/gitattributes)
- [GitHub Copilot Documentation](https://docs.github.com/en/copilot)
- [Best Practices for Large Repositories](https://docs.github.com/en/repositories/working-with-files/managing-large-files)

## Troubleshooting

### Copilot still can't access diffs

If Copilot still has issues after adding `.gitattributes`:

1. **Verify the attributes are set**:
   ```bash
   git check-attr -a path/to/file
   ```

2. **Check PR size**: Even with marked files, if the PR is extremely large (>100 files or >10,000 lines), there may still be limits.

3. **Create smaller PRs**: Break large changes into multiple PRs focusing on different aspects.

4. **Contact support**: If issues persist, contact GitHub support with your PR link.

### Files still showing in diffs

The `linguist-generated` attribute may take effect after:
- Pushing new commits
- GitHub reprocessing the PR (can take a few minutes)
- Closing and reopening the PR

To force GitHub to reprocess:
```bash
git commit --allow-empty -m "Trigger reprocess"
git push
```
