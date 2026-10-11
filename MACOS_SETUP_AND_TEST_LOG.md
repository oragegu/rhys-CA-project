# macOS Setup and Test Log

Date: 11 October 2026  
Machine: macOS development machine  
Project: Infomaniak kDrive Bulk Sharing Link Manager

This document records the macOS setup work completed before live kDrive testing. It contains no API token, sharing password, or account data.

## Initial environment

The project directory was:

```text
/path/to/kdrive_link_manager
```

The initial `python3` command resolved to a Homebrew Python installation:

```text
Python 3.14.0
```

Running the standard Tkinter check:

```bash
python3 -m tkinter
```

failed with:

```text
ModuleNotFoundError: No module named '_tkinter'
```

The traceback showed that Python came from:

```text
/opt/homebrew/Cellar/python@3.14/3.14.0_1/
```

## Cause of the first problem

Homebrew packages the Tkinter bindings separately from `python@3.14`. The matching package is:

```bash
brew install python-tk@3.14
```

Tkinter should be verified after installation with:

```bash
/opt/homebrew/bin/python3.14 -m tkinter
```

Success means a small Tk demonstration window opens without a traceback.

Official references:

- [Homebrew `python-tk@3.14`](https://formulae.brew.sh/formula/python-tk%403.14)
- [Python Tkinter documentation](https://docs.python.org/3/library/tkinter.html)

## First virtual-environment test

A virtual environment named `.venv-tk` was created and the offline suite was run:

```bash
python -m pytest -m "not integration"
```

Test result:

```text
21 passed, 1 deselected, 1 warning
```

All selected application tests passed:

```text
tests/test_api_client.py ..........
tests/test_exporter.py ..
tests/test_sharing.py .........
```

The deselected test was the opt-in, read-only live integration test. No connection to the teacher's kDrive account and no kDrive modification occurred.

## Interpreter problem discovered

Although the tests passed, pytest reported:

```text
platform darwin -- Python 3.9.6
```

This proved that `.venv-tk` was based on Apple's system Python 3.9.6 instead of Homebrew Python 3.14.

The project requires Python 3.11 or newer, so `.venv-tk` must not be used for live application testing or packaging.

## LibreSSL warning

The Python 3.9.6 test emitted:

```text
NotOpenSSLWarning: urllib3 v2 only supports OpenSSL 1.1.1+;
the ssl module is compiled with LibreSSL 2.8.3
```

This warning came from Apple's older system Python and its LibreSSL build. It was not a failed application test, but it confirms that the wrong interpreter created the environment.

The correct fix is to use Homebrew Python explicitly, not to suppress the warning or downgrade networking packages.

## Correct environment procedure

First leave the incorrect environment:

```bash
deactivate
```

Verify the exact Homebrew interpreter and its Tk support:

```bash
/opt/homebrew/bin/python3.14 --version
/opt/homebrew/bin/python3.14 -m tkinter
```

Then create a new environment with that exact interpreter:

```bash
cd /path/to/kdrive_link_manager
/opt/homebrew/bin/python3.14 -m venv .venv314
source .venv314/bin/activate
```

Confirm that the new environment is correct before installing anything:

```bash
python --version
python -c 'import sys; print(sys.executable)'
python -c 'import ssl; print(ssl.OPENSSL_VERSION)'
python -m tkinter
```

Expected interpreter information:

```text
Python 3.14.x
.../kdrive_link_manager/.venv314/bin/python
```

The Tkinter command should open a small window. The SSL command should report OpenSSL rather than LibreSSL 2.8.3.

Install the project dependencies:

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
```

Run the offline suite again:

```bash
python -m pytest -m "not integration"
```

Required release-gate result:

```text
21 passed, 1 deselected
```

There should be no LibreSSL warning from the Apple Python installation.

## Launch command

With `.venv314` activated:

```bash
python run_app.py
```

The application should open as a graphical window. Keep the launching Terminal window open so that an unexpected traceback can be recorded.

## Environment identification commands

If Python selection becomes confusing, run:

```bash
which -a python3
which python
python --version
python -c 'import sys; print(sys.executable)'
```

When `.venv314` is active, `which python` and `sys.executable` must point inside `.venv314`.

Using an explicit executable such as `/opt/homebrew/bin/python3.14` when creating a virtual environment prevents macOS from silently selecting `/usr/bin/python3`.

## Current verified status

Verified:

- The complete offline suite passes: 21 selected tests passed.
- The read-only integration test remains disabled by default.
- No live kDrive request was made during this recorded test.
- No link was created, changed, or removed.
- No credential was stored in the repository or test output.

Still to verify:

- Homebrew Python 3.14 can import Tkinter after installing `python-tk@3.14`.
- `.venv314` reports Python 3.14 and an OpenSSL build.
- The 21 offline tests pass again inside `.venv314` without the LibreSSL warning.
- The GUI launches successfully from `.venv314`.
- The optional read-only live integration test can list accessible kDrives.
- Folder discovery and known link states match the real API.
- One controlled test link requires a password and permits downloading.
- Rescanning preserves the created URL and does not create a duplicate.

## Do not use the wrong environment

Do not run the live test from this environment:

```text
.venv-tk — Python 3.9.6
```

Use:

```text
.venv314 — Homebrew Python 3.14 with Tkinter
```

The old `.venv-tk` directory may be kept temporarily for comparison. It is ignored by Git because virtual-environment directories are local development artifacts. It can be removed later after `.venv314` is confirmed working.

