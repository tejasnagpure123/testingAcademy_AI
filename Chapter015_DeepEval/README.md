# Chapter 015: DeepEval

This chapter uses DeepEval to evaluate LLM outputs. The project uses the local
`venv` virtual environment and Python 3.12.

## Setup

From this folder in PowerShell:

```powershell
.\venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Run the offline setup check:

```powershell
python -m pytest -q
```

The offline tests do not contact an LLM. To configure Groq, copy `.env.example`
to `.env` and add a valid `GROQ_API_KEY`. The integration test uses
`GROQ_MODEL` and `GROQ_BASE_URL` from that file and makes a real API call, which
may incur usage charges:

```powershell
Copy-Item .env.example .env
# Edit .env and set GROQ_API_KEY to your rotated key.
python -m pytest -q
```

Keep `.env` out of source control. `groq_model.py` configures DeepEval's
OpenAI-compatible model client for Groq.

## Installed version

DeepEval is pinned to `4.2.7` in `requirements.txt` for repeatable installs.