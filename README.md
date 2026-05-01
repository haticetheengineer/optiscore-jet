# ⚡ OptiScore Jet

> Optical mark reader output processor — auto-grades exams from TXT and exports results to Excel

OptiScore Jet parses raw optical mark reader (OMR) output files, scores each student's answers against an answer key, and produces a clean Excel report — all through a simple web interface powered by Streamlit.

---

## ✨ Features

- 📂 Upload any OMR `.txt` file directly in the browser
- 🔑 Enter your answer key — score per question is calculated automatically as `100 ÷ question count`
- 🇹🇷 Full Turkish character support (UTF-8, CP1254, Latin-1 auto-detection)
- 🎓 Handles both regular student IDs (8 digits) and double-major IDs (`C` + 8 digits)
- 📊 Instant preview table with progress bars
- 📥 One-click Excel download with two sheets:
  - **SONUCLAR** — Student ID + per-question scores (no header row)
  - **KONTROL** — Student ID + Full Name + Total Score
- ⚠️ Detailed warnings for unparseable rows

---

## 🚀 Getting Started

### Run locally

```bash
git clone https://github.com/YOUR_USERNAME/optiscore-jet.git
cd optiscore-jet
pip install -r requirements.txt
streamlit run app.py
```

Open [http://localhost:8501](http://localhost:8501) in your browser.

### Deploy to Streamlit Cloud

1. Fork this repo
2. Go to [share.streamlit.io](https://share.streamlit.io) and sign in with GitHub
3. Click **Create app** → select this repo → set main file to `app.py`
4. Click **Deploy** — your app will be live in ~2 minutes

---

## 📄 TXT File Format

Each line must follow this structure:

```
FULL NAME    <TC_ID><STUDENT_ID>    ANSWERS
```

| Field | Format | Example |
|---|---|---|
| Full Name | Variable length, may contain Turkish chars | `YILMAZ MEHMET` |
| TC ID + Student ID | 19 digits (concatenated) | `1234567890123456789` |
| Student ID (double-major) | `C` + 8 digits | `C12345678` |
| Answers | Letters A–E, `0` or space = blank | `ABCDEABCDEABCDEABCDE` |

---

## 🧮 Scoring

| Result | Points |
|---|---|
| Correct | `100 ÷ question count` |
| Wrong or blank | `0` |

Example: 25-question exam → each correct answer = **4.00 pts** → max score = **100**

---

## 🛠 Tech Stack

- [Streamlit](https://streamlit.io)
- [pandas](https://pandas.pydata.org)
- [openpyxl](https://openpyxl.readthedocs.io)

---

## 📜 License

MIT © 2026
