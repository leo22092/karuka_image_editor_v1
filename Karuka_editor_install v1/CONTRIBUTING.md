# Contributing

Thanks for helping improve Karuka Image Editor.

## Development Setup

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev,bgremove]"
```

On Windows, activate the virtual environment with:

```powershell
.venv\Scripts\Activate.ps1
```

## Local Checks

Run a syntax check before opening a pull request:

```bash
python -m compileall .
```

Build the package when changing packaging metadata:

```bash
python -m build
```

## Pull Requests

- Keep changes focused on one issue or feature.
- Include a short description of user-visible behavior changes.
- Avoid committing generated files such as `__pycache__/`, edited image outputs, build artifacts, or local virtual environments.
- Update `README.md` when changing install, run, or packaging behavior.
