# ⚡ OptiScore Jet

> Optical mark reader output processor — auto-grades exams from TXT and exports results to Excel

OptiScore Jet parses raw optical mark reader (OMR) output files, scores each student's answers against an answer key, and produces a clean multi-sheet Excel report — all through a simple web interface powered by Streamlit.

---

## ✨ Features

- 📂 Upload any OMR `.txt` file directly in the browser
- 🔑 Enter your answer key — score per question is calculated automatically as `100 ÷ question count`
- 🇹🇷 Full Turkish character support (UTF-8, CP1254, Latin-1 auto-detection)
- 🎓 Handles both regular student IDs (8 digits) and double-major IDs (`C` + 8 digits)
- 📱 Automatically extracts phone numbers when present in the OMR data
- 📊 Instant preview table with progress bars (Student ID · Full Name · TC · Phone · Total)
- 📥 One-click Excel download with **5 sheets**:
  - **Proliz Not Girişi** — Student ID + per-question scores (with header)
  - **Detaylı Liste** — Student ID + Full Name + TC + Phone + Total + per-question scores
  - **Özet** — Student ID + Full Name + TC + Phone + Total
  - **Ham TXT** — Row number + raw answer string for every student
  - **İşlem Özeti** — Answer key, question count, points per question, student count
- 📈 Question-level analysis with downloadable PDF report
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

Each line must follow one of these structures:

### Format A — TC + Student ID + Phone concatenated (29–30 digits)

```
FULL NAME    <TC(11)><STUDENT_ID(8)><PHONE(10-11)>    ANSWERS
```

```
ALİ YILMAZ    12345678901123456785554443311    ABCDEABCDE...
```

### Format B — TC + Student ID concatenated, no phone (19 digits)

```
FULL NAME    <TC(11)><STUDENT_ID(8)>    ANSWERS
```

```
ALİ YILMAZ    1234567890112345678 48    ABCDEABCDE...
```

### Format C — TC and Student ID space-separated (legacy)

```
FULL NAME    <TC(11)>    <STUDENT_ID(8)>    ANSWERS
```

```
ALİ YILMAZ    12345678901    20230001    ABCDEABCDE...
```

| Field | Format | Notes |
|---|---|---|
| Full Name | Variable length | Turkish characters supported |
| TC ID | 11 digits | Always the first 11 digits of the numeric block |
| Student ID | 8 digits or `C` + 8 digits | `C` prefix = double-major (ÇAP) student |
| Phone | 10–11 digits starting with `05` or `5` | Optional; normalized to `05xxxxxxxxxx` |
| Answers | Letters A–E, `0` or space = blank | Trailing blanks padded automatically |

---

## 🧮 Scoring

| Result | Points |
|---|---|
| Correct | `100 ÷ question count` |
| Wrong or blank (`0`) | `0` |

Example: 25-question exam → each correct answer = **4.00 pts** → max score = **100**

---

## 📈 Question Analysis & PDF

After grading, OptiScore Jet generates a per-question breakdown showing correct-answer rates and score distribution across the class. The analysis can be exported as a **PDF report** directly from the interface.

---

## 🛠 Tech Stack

- [Streamlit](https://streamlit.io)
- [pandas](https://pandas.pydata.org)
- [openpyxl](https://openpyxl.readthedocs.io)

---

## 📜 License

MIT © 2026
