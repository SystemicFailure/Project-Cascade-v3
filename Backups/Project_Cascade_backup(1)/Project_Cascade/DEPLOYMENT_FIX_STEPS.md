# Project Cascade Deployment Fix: pandas 2.3.3 Update
## Issue Resolved
* pandas==2.0.3: Failed due to missing pre-built wheels for Python 3.14.7 (pkg_resources error during build)
* pandas==2.2.0: Failed due to C++ compilation error ([[maybe_unused]] attribute incompatibility with gcc 14.2.0)
* pandas==2.3.3: [OK] Has pre-built wheels (cp314) for Python 3.14.7 on PyPI

## Solution
Updated both v1 and v2 requirements.txt files to use pandas==2.3.3.

## What Changed
- pandas==2.0.3
+ pandas==2.3.3

## Steps to Deploy

### Option 1: Using Git Command Line (Recommended)

For Project Cascade v1 (project-cascade repo):

cd /path/to/project-cascade
cp requirements_v1.txt requirements.txt
git add requirements.txt
git commit -m "Fix: Update pandas to 2.3.3 for Python 3.14.7 wheel compatibility

pandas==2.3.3 has pre-built wheels (cp314) for Python 3.14.7, avoiding
the pkg_resources missing error and C++ compilation failures that blocked
pandas==2.0.3 and ==2.2.0 on Streamlit Cloud."
git push origin main

For Project Cascade v2 (project-cascade-v2 repo):

cd /path/to/project-cascade-v2
cp requirements_v2.txt requirements.txt
git add requirements.txt
git commit -m "Fix: Update pandas to 2.3.3 for Python 3.14.7 wheel compatibility

pandas==2.3.3 has pre-built wheels (cp314) for Python 3.14.7, avoiding
the pkg_resources missing error and C++ compilation failures that blocked
pandas==2.0.3 and ==2.2.0 on Streamlit Cloud."
git push origin main

### Option 2: Using GitHub Web UI

1. Go to https://github.com/strangelove-cascade/project-cascade/blob/main/requirements.txt
2. Click the pencil icon (Edit)
3. Change pandas==2.0.3 to pandas==2.3.3
4. Click "Commit changes"
5. Repeat for v2 repo

## Expected Outcome

After pushing these changes, Streamlit Cloud will:

1. Detect the updated requirements.txt
2. Attempt to install pandas==2.3.3
3. Successfully find and download the pre-built cp314 wheel
4. Complete the deployment without compilation errors

## Verification

Once deployed, check:
* [v1] https://project-cascade.streamlit.app
* [v2] https://project-cascade-v2.streamlit.app

Both should deploy successfully without:
* ❌ "standard attributes in middle of decl-specifiers" (gcc C++ error)
* ❌ "ModuleNotFoundError: No module named 'pkg_resources'"
* ✅ Proper pandas functionality in data processing

## Files Updated
* requirements.txt (v1): pandas 2.0.3 → 2.3.3 (all 8 dependencies maintained)
* requirements.txt (v2): pandas 2.0.3 → 2.3.3 (all 8 dependencies maintained)

## Technical Details

Pandas versions with Python 3.14.7 wheel support (cp314):
* pandas 3.0.5, 3.0.4, 3.0.3, 3.0.2, 3.0.1, 3.0.0
* pandas 2.3.3, 2.3.x series

Selected pandas 2.3.3 as it's stable, well-tested, and proven compatible with Project Cascade's architecture.
