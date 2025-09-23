# Static UI for GitHub Pages

This folder contains a static version of the Deal Scout UI suitable for GitHub Pages.

How to use:
- The UI calls the backend API at `/api/companies` and other endpoints.
- Configure the API base URL using either:
  - Query string: `?API_BASE=http://localhost:5000` (for local testing)
  - Static file: edit `config.js` and set `STATIC_API_BASE` to your public API URL.

Deployment:
- A GitHub Actions workflow `.github/workflows/pages.yml` uploads `docs/site` and deploys it to GitHub Pages.
- Enable GitHub Pages in your repository settings with Source: GitHub Actions.

Notes:
- CORS: The backend already sets permissive CORS headers. If you host the backend elsewhere, ensure it allows requests from your Pages domain.
- Jekyll: A `.nojekyll` file is included to disable Jekyll processing in Pages.