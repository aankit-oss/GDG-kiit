# 📜 LexAudit — Local Setup & User Guide

Welcome to **LexAudit**! This document provides complete instructions on how to set up, configure, run, and test LexAudit on your local machine.

---

## 📋 Prerequisites

Before running the application, make sure you have the following installed:

1. **Docker Desktop** (Recommended) — [Download Docker Desktop](https://www.docker.com/products/docker-desktop/)
2. **Git** — [Download Git](https://git-scm.com/)

*(Optional for non-Docker development: Python 3.11+ and Node.js 22+).*

---

## 🔑 Step 1: Obtain API Keys

LexAudit uses **NVIDIA NIM** (Llama 3.1 70B) for zero-hallucination legal compliance auditing and multilingual grounded Q&A.

1. **NVIDIA API Key (Required for live performance):**
   - Go to [NVIDIA Build](https://build.nvidia.com/)
   - Sign up / Sign in and generate a free API key (starts with `nvapi-`).

2. **Google Gemini API Key (Optional fallback):**
   - Go to [Google AI Studio](https://aistudio.google.com/app/apikey)
   - Generate a free Gemini API key.

3. **Razorpay Test Keys (Optional for Payments testing):**
   - Go to [Razorpay Dashboard](https://dashboard.razorpay.com/) → Settings → API Keys
   - Generate free test keys (`rzp_test_...`).

---

## ⚡ Step 2: Configure Environment

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Open `.env` in any text editor and paste your API keys:
   ```env
   NVIDIA_API_KEY=nvapi-YOUR-ACTUAL-NVIDIA-KEY-HERE
   GEMINI_API_KEY=YOUR-ACTUAL-GEMINI-KEY-HERE
   JWT_SECRET=a-long-random-secret-key
   ```

---

## 🚀 Step 3: Run the Application

### Option A — 1-Click Startup (Recommended)

Run the startup script for your operating system:

* **Windows (PowerShell):**
  ```powershell
  .\run.ps1
  ```

* **Linux / macOS (Terminal):**
  ```bash
  chmod +x run.sh && ./run.sh
  ```

---

### Option B — Manual Docker Command

```bash
docker compose up --build
```

---

### Access Points once running:
- 🌐 **Web Interface:** [http://localhost:3000](http://localhost:3000)
- ⚙️ **Backend API:** [http://localhost:8000](http://localhost:8000)
- 📖 **Interactive OpenAPI Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 🧪 Step 4: How to Test All Features

### 1. Compliance Audit Flow
1. Open [http://localhost:3000/audit](http://localhost:3000/audit).
2. Select a statutory rule set (e.g., **DPDP Act 2023** or **Indian Contract Act 1872**).
3. Drag & drop or browse a PDF/DOCX privacy policy or agreement.
4. Click **Run Compliance Audit**.
5. Inspect the generated report: view overall compliance score, pass/fail status per clause, severity levels, and **verbatim quoted evidence**.

### 2. Document Auto-Summarizer & Structural Analysis
1. Open [http://localhost:3000/qa](http://localhost:3000/qa).
2. Upload any legal document (even informal/unstructured dispute records).
3. Watch the system automatically generate a **2-3 sentence overview**, **topic chips**, and **3 suggested questions**.

### 3. Multilingual Grounded Q&A
1. On [http://localhost:3000/qa](http://localhost:3000/qa), type a question in **English or any Indian language** (e.g., Hindi: *इस दस्तावेज़ में डेटा सुरक्षा की अवधि क्या है?*).
2. Click **Ask Question** (or press `⌘+Enter`).
3. View the grounded response returned in the same language with verbatim cited passages.

### 4. User Sign Up, Login & Billing
1. Click **Get Started** / **Sign In** at top right ([http://localhost:3000/signup](http://localhost:3000/signup)).
2. Create a new account with your name, email, and password.
3. Observe your active plan badge (**FREE**) displayed on the top right.
4. Go to **Pricing** ([http://localhost:3000/pricing](http://localhost:3000/pricing)) to inspect Pro and Enterprise plan tiers.

### 5. Admin Dashboard
1. Log in with an admin account or navigate to [http://localhost:3000/admin](http://localhost:3000/admin).
2. View platform statistics (total users, active plan breakdowns, monthly audit and Q&A usage).
3. Manage users and toggle subscription tiers dynamically.

---

## 🛠️ Useful Commands & Troubleshooting

### View Container Logs
```bash
docker compose logs -f
```

### Stop Application
```bash
docker compose down
```

### Port 3000 or 8000 Already in Use
If ports 3000 or 8000 are occupied by another program on your computer:
```bash
docker compose down --remove-orphans
```

### Reset Vector Database & SQLite Data
```bash
docker compose down -v
```

---

## 📬 Need Help?

If you encounter any issues, check the backend OpenAPI documentation at [http://localhost:8000/docs](http://localhost:8000/docs) or view container logs with `docker compose logs backend`.
