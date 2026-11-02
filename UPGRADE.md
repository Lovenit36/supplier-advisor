# Supplier Advisor v1.1 - install over v1.0 (your API key remains untouched)

This update does not include, modify, or replace `.env` or the SQLite events database.

From Terminal, **inside your existing `supplier-advisor` project folder**, stop the server with Ctrl+C, then run:

```bash
unzip -o ~/Downloads/Supplier_Advisor_Update.zip
bash start.command
```

Open http://localhost:8000 and hard refresh with Cmd+Shift+R. If you downloaded the ZIP to a different folder, replace the Downloads path with its actual location. No code or API key needs to be pasted into Terminal.

Version 1.1 changes:
- Blocks wrong model/article selections that contradict original supplier quotation text or AI evidence; a catalogue selection can no longer silently rewrite the quote.
- AI extraction auto-selects a catalogue model ONLY when the full model name and exact article number agree. Text extracted from a supplier PDF is retained as identity evidence.
- Replaces JSON report download with a formatted PDF created by the Python server.
- Adds result-grounded AI chat after a comparison (New chat, suggested questions, bounded conversational history). Requires the existing server-side OpenAI API key.
- Uses supported `reasoning_effort` settings for GPT-6.1 Sol rather than an unsupported `temperature` parameter.
- Includes regression tests and browser test for the user's real mismatch (4215516/4215515 versus 4215513/4215514).

Accuracy guard: the advisor does not certify hydraulic suitability or automatically source adapters. Known installed costs and unsupported technical requirements remain explicitly separated.

Validation: 33 automated tests, plus browser-level desktop/mobile and mismatch/UI flows. A synthetic PDF was rendered and inspected. Live OpenAI responses and public hosting were not tested from this build environment.
