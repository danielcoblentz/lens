# Lens Frontend (Create React App, TypeScript)

React + TypeScript + react-pdf UI for uploading PDFs, viewing pages, and chatting against backend RAG endpoints.

## Scripts (CRA)
- `npm start` - dev server at http://localhost:3000
- `npm test` - jest and React Testing Library
- `npm run build` - production build to `build/`

## Project structure (key)
- `src/pages/Home.tsx` - layout wiring sidebar, viewer, and chat.
- `src/components/Sidebar.tsx` - file list.
- `src/components/FileViewer.tsx` - PDF rendering via `react-pdf`.
- `src/components/ChatBox.tsx` - chat UI.
- `src/services/aws.ts` - the only module that talks to API Gateway.
- `src/types.ts` - shapes shared by the components and the API client.

## Wiring to the backend
Add your API base and any defaults via environment variables (CRA uses `REACT_APP_*`):
- `REACT_APP_API_BASE` - API Gateway base URL (e.g., `https://xyz.execute-api.us-east-1.amazonaws.com/Prod`). This is the only variable the app reads.

`services/aws.ts` posts to `${REACT_APP_API_BASE}/llamaGet` and `${REACT_APP_API_BASE}/query`, and polls `${REACT_APP_API_BASE}/sessions/{sessionId}` after an upload until parsing finishes. Keep secrets out of the frontend; only non-sensitive URLs belong in env files.

## Requirements
- Node 18+
- npm

## Notes
- This project uses Create React App (not Vite). Use `npm start`/`npm run build` from CRA scripts.
- `npm start` and `npm run build` first copy the pdf.js worker from `pdfjs-dist` into `public/`, and `FileViewer.tsx` loads it from there.
