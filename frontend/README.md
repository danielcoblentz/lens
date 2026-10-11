# Lens Frontend (Create React App)

React + react-pdf UI for uploading PDFs, viewing pages, and chatting against backend RAG endpoints.

## Scripts (CRA)
- `npm start` - dev server at http://localhost:3000
- `npm test` - jest and React Testing Library
- `npm run build` - production build to `build/`

## Project structure (key)
- `src/pages/Home.js` - layout wiring sidebar, viewer, and chat.
- `src/components/Sidebar.js` - file list.
- `src/components/FileViewer.js` - PDF rendering via `react-pdf`.
- `src/components/ChatBox.js` - chat UI.
- `src/services/aws.js` - the only module that talks to API Gateway.

## Wiring to the backend
Add your API base and any defaults via environment variables (CRA uses `REACT_APP_*`):
- `REACT_APP_API_BASE` - API Gateway base URL (e.g., `https://xyz.execute-api.us-east-1.amazonaws.com/Prod`). This is the only variable the app reads.

`services/aws.js` posts to `${REACT_APP_API_BASE}/llamaGet` and `${REACT_APP_API_BASE}/query`. Keep secrets out of the frontend; only non-sensitive URLs belong in env files.

## Requirements
- Node 18+
- npm

## Notes
- This project uses Create React App (not Vite). Use `npm start`/`npm run build` from CRA scripts.
- `npm start` and `npm run build` first copy the pdf.js worker from `pdfjs-dist` into `public/`, and `FileViewer.js` loads it from there.
