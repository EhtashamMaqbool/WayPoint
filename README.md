# 🧭 TrailHead

**AI-powered career roadmaps, built for Pakistani students.**

TrailHead helps students in Pakistan turn a vague sense of direction ("I like computers" / "I'm good at biology") into a concrete, data-grounded career plan — complete with academic pathways, competitive-exam gates, realistic starting salaries, and holiday upskilling certifications they can start right now.

---

## ✨ Features

- **Account system** — simple sign-up / sign-in so students can return to a personalized experience
- **Guided intake** — students select their current academic stage, field of interest, target competitive exam (ECAT, MDCAT, CSS, IELTS/GRE, etc.), and vacation availability
- **Custom interest tags** — beyond the dropdowns, students can add their own specific interests (e.g. "Robotics", "UI/UX Design") which get folded into the AI prompt
- **AI Career GPS engine** — generates:
  - An executive summary of the Pakistani + global market reality for the chosen path
  - Two side-by-side tracks (e.g. a traditional university → job pipeline vs. a freelancing/remote alternative), each with time-to-ready, market demand, starting salary range, entry gate, and a milestone action plan
  - A curated list of holiday/break upskilling certifications (DigiSkills, Coursera, NAVTTC, etc.)
- **Dedicated results view** — output opens in its own clean, full-page view rather than being buried under the form
- **Custom design system** — a distinctive navy/brass "compass" theme (see [Design](#-design)) instead of default Gradio styling, fully responsive down to mobile

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| UI | [Gradio](https://gradio.app) (Blocks API) |
| AI inference | [Groq](https://groq.com) (OpenAI-compatible API), model: `openai/gpt-oss-20b` |
| Storage | SQLite (`trailhead.db`) for user accounts |
| Hosting | [Hugging Face Spaces](https://huggingface.co/spaces) (ZeroGPU) |

---

## 🚀 Getting Started

### 1. Clone the repo

```bash
git clone https://github.com/<your-username>/trailhead.git
cd trailhead
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Set your Groq API key

TrailHead **never hardcodes API keys**. Set it as an environment variable:

```bash
export GROQ_API_KEY="your_groq_api_key_here"
```

Get a free key at [console.groq.com](https://console.groq.com).

### 4. Run the app

```bash
python app.py
```

The app will start locally (Gradio will print a local URL to open in your browser).

---

## ☁️ Deploying to Hugging Face Spaces

1. Create a new **Space** on Hugging Face, choosing **Gradio** as the SDK.
2. Push `app.py` and `requirements.txt` to the Space repo.
3. Go to **Settings → Repository secrets** and add:
   - `GROQ_API_KEY` → your Groq API key
4. If using ZeroGPU hardware, make sure the Space's hardware tier supports it — the `@spaces.GPU` decorator satisfies the ZeroGPU runtime check.
5. The Space will build and launch automatically.

---

## 📁 Project Structure

```
trailhead/
├── app.py              # Main Gradio application (UI + auth + AI engine)
├── requirements.txt    # Python dependencies
├── trailhead.db        # SQLite user database (auto-created on first run)
└── README.md
```

---

## 🎨 Design

TrailHead's UI is themed around the idea of a **compass and a marked trail** rather than a generic dashboard:

- **Navy (`#0F1B2E`)** for structure and trust, **brass/gold (`#B8862E`)** as a compass-needle accent, and a **parchment (`#F6F3EC`)** background for a map-like feel
- **Lora** (serif) for headings, **Inter** (sans-serif) for body and UI text
- Fully responsive layout (breakpoint at 640px) with visible focus states for accessibility and `prefers-reduced-motion` support

---

## 🔒 Security Notes

- API keys are read only from environment variables / Space secrets — **never commit a real key to this repo**.
- Passwords are hashed with SHA-256 before being stored in SQLite. For production use with real user data, consider migrating to a stronger, salted hashing scheme (e.g. `bcrypt` or `argon2`) and a managed database.

---

## 🗺️ Roadmap Ideas

- [ ] Migrate from SQLite to a hosted database for multi-instance deployments
- [ ] Add password strength requirements and salting
- [ ] Support exporting a generated roadmap as a PDF
- [ ] Add more competitive exam gates and regional academic tracks

---

## 📄 License

Choose a license for your repo (e.g. MIT) and add it here.

---

## 🙏 Acknowledgements

Built with [Gradio](https://gradio.app) and powered by [Groq](https://groq.com)'s fast inference API.
