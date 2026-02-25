# User Preferences

- **Communication Language**: Always use Chinese.

# Project: Tastegent (Restaurant AI Agent)

## Architecture Overview
- **Frontend**: React + Vite (deployed on Vercel)
- **Backend**: Python FastAPI (deployed on Render)
- **Database**: In-memory JSON (`menu.json`) for simplicity, mimicking a database.
- **AI Integration**: Google Gemini, Anthropic, or OpenAI (configurable via env).

## Key Patterns & Configurations

### 1. Environment & API Handling (`frontend/src/services/api.js`)
- **Dual Environment Support**:
  - **Local Development**: `API_URL` defaults to `''` (empty string). This triggers Vite's internal proxy to forward requests (e.g., `/menu`) to the backend, solving CORS issues locally.
  - **Production (Vercel)**: `API_URL` uses `import.meta.env.VITE_API_URL` (set to `https://tastegent.onrender.com`). Vercel connects directly to Render.

### 2. Corporate Proxy Handling (`vite.config.js`)
- **Problem**: Local Vite proxy fails behind corporate proxies (e.g., Zscaler) with `ETIMEDOUT`.
- **Solution**: Uses `https-proxy-agent` to tunnel Vite's internal proxy requests through the corporate proxy (e.g., `http://127.0.0.1:9000`).
- **Config**:
  ```javascript
  const proxyAgent = new HttpsProxyAgent('http://127.0.0.1:9000');
  // In server.proxy targets:
  agent: proxyAgent
  ```

### 3. Frontend Architecture
- **State Management**: Custom hook `useTastegent` (`frontend/src/hooks/useTastegent.js`) manages chat state, menu fetching, and grouping logic.
- **Component Pattern**: Composition over inheritance. UI components split into `MessageBubble`, `TypingIndicator`, `MenuCategory`.
- **Styling**:
  - **Tailwind CSS v3**: Configured in `tailwind.config.js` and `postcss.config.js`.
  - **Design System**: Glassmorphism (backdrop-blur), Lucide React icons, mobile-first full-screen layout.
  - **Utility**: `cn` helper (clsx + tailwind-merge) in `src/lib/utils.js`.

### 4. Deployment
- **Render (Backend)**:
  - Requires `ALLOWED_ORIGINS` env var to include Vercel domain and localhost.
  - Python dependencies managed in `backend/requirements.txt`.
- **Vercel (Frontend)**:
  - Requires `VITE_API_URL` env var set to Render backend URL.
  - Node dependencies managed in `frontend/package.json` (ensure `tailwindcss` is in devDependencies).

## Development Workflow
1.  **Start Backend** (Local or Remote): Ensure `menu.json` exists.
2.  **Start Frontend**: `npm run dev` (uses proxy).
3.  **Deploy**: `git push` triggers auto-deployment on both platforms.
