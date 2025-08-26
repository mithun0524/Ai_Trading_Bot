# Single Dashboard Mode

This project is now simplified to a single, clean, black‑themed dashboard at /app with a landing page at /.

What's changed:
- Removed legacy/enhanced/mobile dashboards and routes
- Landing page updated with clearer content and single CTA to /app
- PWA start_url now points to /
- Service worker caches only '/', '/app', and manifest

How to use:
- Start the app: python -u main.py
- Open http://127.0.0.1:5000 for landing, then click "Open Dashboard"
