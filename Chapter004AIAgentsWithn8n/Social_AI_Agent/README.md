# ContentForge

ContentForge is a local, automated content-generation pipeline and web dashboard. It utilizes:
- **Groq SDK** (`llama-3.3-70b-versatile`) to generate topic ideas and draft copy (LinkedIn post, Medium article, Instagram script, YouTube script, Dev.to article) in a direct, technical voice.
- **Google Gen AI SDK** (`gemini-2.5-flash-image` / `imagen-3.0-generate-002`) to generate image assets locally.
- **ExcelJS** to manage a local `content_calendar.xlsx` spreadsheet under atomic mutex locks.
- **Node-Cron** to automatically trigger the content pipeline daily at 9:00 AM local time.

---

## 🛠️ Stack & Architecture

- **Framework**: Next.js 14 (App Router) + React + Tailwind CSS
- **Orchestration**: Direct TypeScript classes & functions inside `/lib` (no external heavyweight agent frameworks)
- **Database**: Local `content_calendar.xlsx` file in the project root
- **Assets**: Images saved to `./public/images/` and served dynamically by the Next.js dev server

---

## 🚀 Setup & Installation

### 1. Clone & Install Dependencies
Navigate to the project directory and install the packages:
```bash
npm install
```

### 2. Configure Environment Keys
Copy `.env.example` to `.env.local`:
```bash
cp .env.example .env.local
```
Open `.env.local` and paste your actual credentials:
```env
GROQ_API_KEY=gsk_...
GEMINI_API_KEY=AIzaSy...
```

### 3. Run Development Server
Start the server. The cron scheduler will bootstrap exactly once upon startup (using a hot-reload guard):
```bash
npm run dev
```
Open [http://localhost:3000](http://localhost:3000) in your browser.

---

## 📂 Output Locations

- **Spreadsheet**: `content_calendar.xlsx` will be generated in the root of the project folder.
- **Image Assets**: Generated illustrations are stored in the `./public/images` folder (as `/images/linkedin_*.png`, etc.).

---

## 🤖 Agent Flow details

1. **Agent 1 — Topic Generator**: Uses Groq to generate a new topic from the keyword pool while checking the existing sheet to avoid duplication. Appends a new row in status `Pending`.
2. **Agent 2 — Content Writer**: Reads today's topic, sets status to `Writing`, and drafts copy for 5 content channels in a technical, direct voice. Sets status to `Imaging`.
3. **Agent 3 — Image Generator**: Uses Gemini to generate 3 distinct layout graphics (Medium 16:9, LinkedIn 16:9, Instagram 1:1) and saves them in the public folder. Sets status to `Done`.
4. **Agent 4 — Sheet Updater**: ExcelManager wrapper ensuring concurrent safe, atomic writes to the spreadsheet with an async mutex queue.
