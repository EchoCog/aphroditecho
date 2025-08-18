# Fix for "Argument list too long" Error in GitHub Actions

## Problem

The EchoPilot Self-Improvement Workflow was failing with the error:
```
Error: An error occurred trying to start process '/home/runner/actions-runner/cached/externals/node20/bin/node' with working directory '/home/runner/work/echodash/echodash'. Argument list too long
```

## Root Cause

This error occurs when the command line arguments exceed the system's limit (typically around 131,072 characters on Linux). The repository contained 5,425 files, with large directories like:
- `todo/` (2,193 files)
- `deep_tree_echo_profile/cache2/entries` (1,999 files)
- `chrome_user_data/` (many cache files)
- `browser_data/` (many cache files)

When CodeQL analysis tried to process all these files, the file paths exceeded the command line argument limit.

## Solution

### 1. Updated `.gitignore`
Added the following directories to `.gitignore`:
```
# Large directories that should not be in repository
todo/
browser_data/
```

### 2. Modified CodeQL Workflows
Updated both `.github/workflows/codeql.yml` and `.github/workflows/codeqladd.yml` to exclude large directories from analysis:

```yaml
paths: |
  - '**'
  - '!todo/**'
  - '!deep_tree_echo_profile/**'
  - '!chrome_user_data/**'
  - '!browser_data/**'
```

### 3. Created Cleanup Script
Created `cleanup_repository.sh` to remove large directories from git tracking while keeping them locally.

## How to Apply the Fix

1. **Run the cleanup script:**
   ```bash
   ./cleanup_repository.sh
   ```

2. **Commit the changes:**
   ```bash
   git add .
   git commit -m "Clean up repository to fix argument list too long error"
   ```

3. **Push the changes:**
   ```bash
   git push
   ```

## Prevention

To prevent this issue in the future:

1. **Keep `.gitignore` updated** with directories that contain temporary or cache files
2. **Regularly clean up** large directories that shouldn't be in version control
3. **Use `.gitignore` patterns** for common cache and temporary file patterns
4. **Monitor repository size** and file count regularly

## Files Modified

- `.gitignore` - Added large directories to ignore list
- `.github/workflows/codeql.yml` - Added path exclusions for CodeQL analysis
- `.github/workflows/codeqladd.yml` - Added path exclusions for CodeQL analysis
- `cleanup_repository.sh` - Script to clean up repository (new file)
- `ARGUMENT_LIST_TOO_LONG_FIX.md` - This documentation (new file)

## Expected Result

After applying these fixes, the GitHub Actions workflows should run successfully without the "Argument list too long" error. The CodeQL analysis will focus on the actual source code while ignoring the large cache and temporary directories.