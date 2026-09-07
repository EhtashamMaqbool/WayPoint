import gradio as gr
import sqlite3
import hashlib
import json
import os
from openai import OpenAI
import spaces

# Satisfy Hugging Face ZeroGPU runtime check
@spaces.GPU
def init_gpu():
    return True

init_gpu()

# ----------------- CONFIGURATION -----------------
# SECURITY: never hardcode API keys in source. Set GROQ_API_KEY as a
# Hugging Face Space secret (Settings -> Repository secrets).
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise ValueError(
        "GROQ_API_KEY not set. Add it as a Hugging Face Space secret "
        "(Settings -> Repository secrets -> GROQ_API_KEY)."
    )

GROQ_BASE_URL = "https://api.groq.com/openai/v1"

client = OpenAI(
    api_key=GROQ_API_KEY.strip(),
    base_url=GROQ_BASE_URL
)

# ----------------- DATABASE SETUP -----------------
def init_db():
    conn = sqlite3.connect("trailhead.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT,
            fullname TEXT,
            grade TEXT
        )
    """)
    conn.commit()
    conn.close()

def hash_pass(password):
    return hashlib.sha256(password.encode()).hexdigest()

def register_user(username, password, fullname, grade):
    if not username.strip() or not password.strip() or not fullname.strip():
        return "⚠️ All fields are required."
    conn = sqlite3.connect("trailhead.db")
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users VALUES (?, ?, ?, ?)", 
                  (username.strip(), hash_pass(password), fullname.strip(), grade))
        conn.commit()
        return "✅ Account created successfully! Please switch to the Sign In tab."
    except sqlite3.IntegrityError:
        return "⚠️ Username already exists. Please choose another."
    finally:
        conn.close()

def authenticate_user(username, password):
    conn = sqlite3.connect("trailhead.db")
    c = conn.cursor()
    c.execute("SELECT fullname, grade FROM users WHERE username=? AND password=?", 
              (username.strip(), hash_pass(password)))
    user = c.fetchone()
    conn.close()
    return user

init_db()

# ----------------- AI ENGINE (GROQ) -----------------
def call_career_gps(grade, domain, exam, vacation, interest):
    prompt = f"""
    You are TrailHead, an elite career intelligence engine built for Pakistani students.
    Generate data-grounded pathways, salary trends, entry gates, and holiday upskilling certifications.
    Return STRICT JSON (no markdown fences, no extra text):
    Student Profile:
    - Current Stage: {grade}
    - Field of Interest: {domain}
    - Competitive Exam/Gate: {exam}
    - Free Time / Holidays: {vacation}
    - Student Background & Ambitions: {interest}
    Required JSON Schema:
    {{
      "executive_summary": "Pakistani and global market reality for this pathway",
      "paths": [
        {{
          "track_name": "Primary Track (e.g. FSc -> FAST/NUST BS CS -> AI Engineer)",
          "time_to_ready": "e.g., 4 Years BS + 6 Months Portfolio",
          "market_demand_pk": "High / Medium / Emerging",
          "avg_starting_salary_pkr": "e.g., 90,000 - 160,000 PKR / month",
          "merit_exam": "Required gate/test (e.g. ECAT / NET / FAST Entry)",
          "milestones": ["Milestone 1", "Milestone 2", "Milestone 3", "Milestone 4"]
        }},
        {{
          "track_name": "Alternative Track (e.g. Global Remote AI / Direct Freelancing)",
          "time_to_ready": "Duration",
          "market_demand_pk": "Demand index",
          "avg_starting_salary_pkr": "PKR / USD salary range",
          "merit_exam": "Entry requirements",
          "milestones": ["Milestone 1", "Milestone 2", "Milestone 3", "Milestone 4"]
        }}
      ],
      "break_certifications": [
        {{
          "title": "Certification / Course Name",
          "provider": "e.g., DigiSkills, Coursera, NAVTTC, Alibaba Cloud Academy",
          "duration": "e.g., 4-6 weeks",
          "cost": "Free / Paid"
        }}
      ]
    }}
    """

    # NOTE: llama-3.1-8b-instant has been deprecated/decommissioned by Groq.
    # openai/gpt-oss-20b is Groq's recommended production replacement.
    try:
        response = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[
                {"role": "system", "content": "You are TrailHead AI Career GPS. Return raw JSON only."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.3,
            max_tokens=4096
        )
        data = json.loads(response.choices[0].message.content)

        md = f"## 📊 Pakistani Market Telemetry\n> {data.get('executive_summary', '')}\n\n---\n"
        md += "## 🧭 Recommended Career Tracks (Side-by-Side)\n\n"

        for idx, p in enumerate(data.get("paths", [])):
            md += f"### 📌 Track 0{idx+1}: {p.get('track_name')}\n"
            md += f"| Metric | Detail |\n| :--- | :--- |\n"
            md += f"| **⏱️ Time to Ready** | {p.get('time_to_ready')} |\n"
            md += f"| **📈 Market Demand in PK** | `{p.get('market_demand_pk')}` |\n"
            md += f"| **💵 Median Starting Salary** | {p.get('avg_starting_salary_pkr')} |\n"
            md += f"| **🎯 Entry Gate / Test** | {p.get('merit_exam')} |\n\n"
            md += "**Milestone Action Plan:**\n"
            for m in p.get("milestones", []):
                md += f"- 📍 {m}\n"
            md += "\n---\n"

        md += "## 🏖️ Holiday & Break Upskilling (Targeted Certifications)\n"
        for c in data.get("break_certifications", []):
            md += f"- 🎓 **{c.get('title')}** via *{c.get('provider')}* ({c.get('duration')} • `{c.get('cost')}`)\n"

        return md

    except json.JSONDecodeError:
        return "⚠️ The model returned an unexpected response format. Please try again."
    except Exception as e:
        return f"⚠️ Error generating career plan: {str(e)}"

# ----------------- GRADIO INTERFACE -----------------
custom_css = """
@import url('https://fonts.googleapis.com/css2?family=Lora:ital,wght@0,500;0,600;0,700;1,500&family=Inter:wght@400;500;600;700&display=swap');
:root {
    --wp-navy: #0F1B2E;
    --wp-navy-soft: #16273E;
    --wp-brass: #B8862E;
    --wp-brass-soft: #D9AE5E;
    --wp-parchment: #F6F3EC;
    --wp-card: #FFFFFF;
    --wp-slate: #4A5568;
    --wp-ink: #1A2333;
    --wp-green: #3F7A5C;
    --wp-border: #E4DFD3;
}
html, body, .gradio-container {
    height: auto !important;
    min-height: 100vh !important;
    overflow-y: auto !important;
    background: var(--wp-parchment) !important;
    font-family: 'Inter', sans-serif !important;
    color: var(--wp-ink) !important;
}
.gradio-container {
    max-width: 880px !important;
    margin: 0 auto !important;
    padding: 32px 20px 64px !important;
}
/* ---------- Headings ---------- */
h1, h2, h3, .gradio-container h1, .gradio-container h2, .gradio-container h3 {
    font-family: 'Lora', serif !important;
    color: var(--wp-navy) !important;
    letter-spacing: -0.01em;
}
.wp-hero h1 {
    font-size: 2.1rem !important;
    font-weight: 600 !important;
    margin-bottom: 2px !important;
}
.wp-hero p {
    color: var(--wp-slate) !important;
    font-size: 1.02rem;
    margin-top: 0;
}
/* Thin brass rule under hero, evokes a compass bearing line */
.wp-hero {
    border-bottom: 2px solid var(--wp-brass);
    padding-bottom: 18px;
    margin-bottom: 28px;
}
/* ---------- Cards / containers ---------- */
.wp-card {
    background: var(--wp-card) !important;
    border: 1px solid var(--wp-border) !important;
    border-radius: 10px !important;
    padding: 28px !important;
    box-shadow: 0 1px 2px rgba(15, 27, 46, 0.04) !important;
}
/* ---------- Inputs ---------- */
.gradio-container input[type=text],
.gradio-container input[type=password],
.gradio-container textarea,
.gradio-container select {
    background: var(--wp-parchment) !important;
    border: 1px solid var(--wp-border) !important;
    border-radius: 6px !important;
    color: var(--wp-ink) !important;
    font-family: 'Inter', sans-serif !important;
}
.gradio-container input:focus,
.gradio-container textarea:focus,
.gradio-container select:focus {
    border-color: var(--wp-brass) !important;
    box-shadow: 0 0 0 3px rgba(184, 134, 46, 0.18) !important;
    outline: none !important;
}
.gradio-container label span {
    color: var(--wp-navy) !important;
    font-weight: 500 !important;
    font-size: 0.92rem !important;
}
/* ---------- Buttons ---------- */
.gradio-container button {
    border-radius: 6px !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 600 !important;
    transition: transform 0.08s ease, box-shadow 0.15s ease;
}
.gradio-container button.primary,
#generate-btn button {
    background: var(--wp-navy) !important;
    color: var(--wp-parchment) !important;
    border: 1px solid var(--wp-navy) !important;
}
.gradio-container button.primary:hover,
#generate-btn button:hover {
    background: var(--wp-navy-soft) !important;
    box-shadow: 0 2px 8px rgba(15, 27, 46, 0.25) !important;
}
.gradio-container button.secondary {
    background: transparent !important;
    color: var(--wp-navy) !important;
    border: 1px solid var(--wp-navy) !important;
}
.gradio-container button.secondary:hover {
    background: var(--wp-navy) !important;
    color: var(--wp-parchment) !important;
}
/* ---------- Tabs (Sign In / Create Account) ---------- */
.gradio-container .tab-nav button {
    font-family: 'Lora', serif !important;
    font-size: 1rem !important;
    color: var(--wp-slate) !important;
    border-bottom: 2px solid transparent !important;
}
.gradio-container .tab-nav button.selected {
    color: var(--wp-navy) !important;
    border-bottom: 2px solid var(--wp-brass) !important;
}
/* ---------- Results view ---------- */
#output_display {
    max-height: none !important;
    overflow-y: visible !important;
    background: var(--wp-card);
    border: 1px solid var(--wp-border);
    border-radius: 10px;
    padding: 28px 32px;
    animation: wp-fade-in 0.35s ease;
}
#output_display h2, #output_display h3 {
    font-family: 'Lora', serif !important;
}
#output_display table {
    border-collapse: collapse;
    width: 100%;
}
#output_display table td, #output_display table th {
    border: 1px solid var(--wp-border) !important;
    padding: 8px 12px !important;
}
@keyframes wp-fade-in {
    from { opacity: 0; transform: translateY(6px); }
    to { opacity: 1; transform: translateY(0); }
}
/* ---------- Tag chips ---------- */
#tags_display p {
    line-height: 2.1 !important;
}
#tags_display code {
    background: var(--wp-navy) !important;
    color: var(--wp-parchment) !important;
    border-radius: 20px !important;
    padding: 4px 12px !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 0.85rem !important;
    margin-right: 4px;
}
/* ---------- Responsive ---------- */
@media (max-width: 640px) {
    .gradio-container {
        padding: 20px 14px 48px !important;
    }
    .wp-hero h1 {
        font-size: 1.6rem !important;
    }
    .wp-card, #output_display {
        padding: 18px !important;
    }
    .gradio-container .form {
        flex-direction: column !important;
    }
}
/* Accessibility: visible focus ring on all interactive elements */
.gradio-container *:focus-visible {
    outline: 2px solid var(--wp-brass) !important;
    outline-offset: 2px !important;
}
@media (prefers-reduced-motion: reduce) {
    * { animation: none !important; transition: none !important; }
}
"""

with gr.Blocks(title="TrailHead - AI Career GPS", css=custom_css) as demo:
    user_session = gr.State({})

    # Header
    with gr.Column(elem_classes="wp-hero"):
        gr.Markdown("# 🧭 TrailHead")
        gr.Markdown("**AI-powered career roadmaps, built for Pakistani students.**")

    # 1. AUTHENTICATION VIEW
    with gr.Column(visible=True, elem_classes="wp-card") as auth_container:
        with gr.Tabs():
            with gr.TabItem("Sign In"):
                login_user = gr.Textbox(label="Username")
                login_pass = gr.Textbox(label="Password", type="password")
                login_btn = gr.Button("Sign In to TrailHead", variant="primary")
                login_msg = gr.Markdown()

            with gr.TabItem("Create Account"):
                gr.Markdown("### Register for TrailHead")
                reg_name = gr.Textbox(label="Full Name")
                reg_user = gr.Textbox(label="Choose Username")
                reg_pass = gr.Textbox(label="Choose Password", type="password")
                reg_grade = gr.Dropdown(
                    label="Current Academic Stage",
                    choices=[
                        "Matriculation (Science)", "Matriculation (Arts)",
                        "O Levels", "FSc Pre-Engineering", "FSc Pre-Medical",
                        "ICS (Computer Science)", "I.Com / FA", "A Levels",
                        "Undergraduate Student (BS/BE)", "Fresh Graduate / Job Seeker"
                    ],
                    value="FSc Pre-Engineering"
                )
                reg_btn = gr.Button("Complete Registration")
                reg_msg = gr.Markdown()

    # 2. DASHBOARD VIEW
    with gr.Column(visible=False, elem_classes="wp-card") as dash_container:
        with gr.Row():
            dash_welcome = gr.Markdown("### Welcome to TrailHead")
            logout_btn = gr.Button("Sign Out", scale=1)

        gr.Markdown("---")
        gr.Markdown("### 📍 Career Intake & Guidance Engine")

        with gr.Row():
            in_domain = gr.Dropdown(
                label="Target Domain of Interest",
                choices=[
                    "Current AI & Machine Learning",
                    "Software & Web Engineering",
                    "Medical & Healthcare (MBBS/BDS/Allied)",
                    "Engineering (Electrical/Civil/Mechanical)",
                    "Business, FinTech & CA/ACCA",
                    "Central Superior Services (CSS) & Civil Bureaucracy",
                    "Freelancing & Digital Services"
                ],
                value="Current AI & Machine Learning"
            )
            in_exam = gr.Dropdown(
                label="Target Entry Gate / Competitive Exam",
                choices=[
                    "None / Direct Admission",
                    "ECAT / NUST NET / FAST Entry",
                    "MDCAT (Medical College Entry)",
                    "CSS (Civil Bureaucracy)",
                    "IELTS / GRE (Foreign Scholarships)"
                ],
                value="ECAT / NUST NET / FAST Entry"
            )
            in_vacation = gr.Dropdown(
                label="Availability / Vacation Schedule",
                choices=[
                    "Summer / Winter Vacation (2-3 Months Free)",
                    "Active School/Semester Studies",
                    "Gap Year (Full Time Upskilling)",
                    "Part-time (Evenings only)"
                ],
                value="Summer / Winter Vacation (2-3 Months Free)"
            )

        in_interest = gr.Textbox(
            label="Strengths, Preferred Subjects & Goals",
            placeholder="e.g., Strong in math and Python, want to build software applications, target global remote roles.",
            lines=3
        )

        gr.Markdown("**Add your own interests** — optional, add as many as you like")
        user_tags_state = gr.State([])
        with gr.Row():
            tag_input = gr.Textbox(
                label="",
                placeholder="e.g., Robotics, Cybersecurity, UI/UX Design...",
                scale=4,
                show_label=False
            )
            add_tag_btn = gr.Button("➕ Add Interest", scale=1)
        tags_display = gr.Markdown("", elem_id="tags_display")

        with gr.Column(elem_id="generate-btn"):
            generate_btn = gr.Button("🚀 Calculate Career GPS Roadmaps", variant="primary")

    # 3. RESULTS VIEW (opens as its own page after generating)
    with gr.Column(visible=False) as results_container:
        with gr.Row():
            gr.Markdown("## 🧭 Your TrailHead Career Roadmap")
            back_btn = gr.Button("← Back / New Search", scale=1)
        output_display = gr.Markdown(elem_id="output_display")

    # ----------------- EVENT LOGIC -----------------
    def on_register(name, user, pwd, grade):
        return register_user(user, pwd, name, grade)

    def on_login(user, pwd):
        user_info = authenticate_user(user, pwd)
        if user_info:
            session = {"fullname": user_info[0], "grade": user_info[1], "username": user}
            welcome = f"### Welcome back, {user_info[0]}! | Registered Stage: `{user_info[1]}`"
            return (
                session,
                gr.update(visible=False),
                gr.update(visible=True),
                "",
                welcome
            )
        return (
            {},
            gr.update(visible=True),
            gr.update(visible=False),
            "⚠️ Invalid username or password.",
            ""
        )

    def on_logout():
        return (
            {},
            gr.update(visible=True),
            gr.update(visible=False)
        )

    def on_add_tag(tag, tags):
        tag = tag.strip()
        if tag and tag not in tags:
            tags = tags + [tag]
        chips = " ".join([f"`{t}`" for t in tags])
        return tags, chips, ""

    def on_generate_full(session, domain, exam, vacation, interest, tags):
        combined_interest = interest.strip()
        if tags:
            tag_str = ", ".join(tags)
            combined_interest = (
                f"{combined_interest}. Specific interests to prioritize: {tag_str}."
                if combined_interest else f"Specific interests to prioritize: {tag_str}."
            )
        if not combined_interest.strip():
            return (
                "⚠️ Please enter your interests or strengths before calculating.",
                gr.update(visible=True),
                gr.update(visible=False)
            )
        grade = session.get("grade", "Undergraduate Student (BS/BE)")
        result = call_career_gps(grade, domain, exam, vacation, combined_interest)
        return (
            result,
            gr.update(visible=False),
            gr.update(visible=True)
        )

    def on_back():
        return (
            gr.update(visible=True),
            gr.update(visible=False),
            [],
            ""
        )

    reg_btn.click(
        fn=on_register,
        inputs=[reg_name, reg_user, reg_pass, reg_grade],
        outputs=reg_msg
    )

    login_btn.click(
        fn=on_login,
        inputs=[login_user, login_pass],
        outputs=[user_session, auth_container, dash_container, login_msg, dash_welcome]
    )

    logout_btn.click(
        fn=on_logout,
        outputs=[user_session, auth_container, dash_container]
    )

    add_tag_btn.click(
        fn=on_add_tag,
        inputs=[tag_input, user_tags_state],
        outputs=[user_tags_state, tags_display, tag_input]
    )

    generate_btn.click(
        fn=on_generate_full,
        inputs=[user_session, in_domain, in_exam, in_vacation, in_interest, user_tags_state],
        outputs=[output_display, dash_container, results_container]
    )

    back_btn.click(
        fn=on_back,
        outputs=[dash_container, results_container, user_tags_state, tags_display]
    )

if __name__ == "__main__":
    demo.launch(ssr_mode=False)
