# Project Setup Guide

This guide details the **constraining operations** (setup steps) required to make the Info Tracker project work correctly.

## 1. Prerequisites & Installation

### Environment
- **Python 3.8+** installed.
- **Google Chrome** (optional but recommended for Playwright).

### Install Dependencies
Run the following commands in your terminal:

```bash
# 1. Install Python libraries
pip install -r requirements.txt

# 2. Install Playwright browsers (required for Facebook scraping)
playwright install
```

---

## 2. Configuration (`config.yaml`)

You must configure `config.yaml` before running the program.

### A. Email Setup (Gmail)
To send daily reports via Gmail, you **must** use an **App Password**, not your regular login password.

1.  Open `config.yaml`.
2.  Set `enabled: true` under `email`.
3.  Fill in your details:
    ```yaml
    email:
      sender: "your_email@gmail.com"
      password: "your_16_char_app_password" # See GMAIL_FIX.md if you don't have this
      recipient: "recipient@example.com"
    ```
4.  **Important**: Refer to `GMAIL_FIX.md` if you need help generating an App Password (requires 2FA).

### B. Facebook Setup
The scraper visits public pages and groups.

1.  **Edit Pages/Groups**:
    - Open `config.yaml`.
    - Add or modify entries under `sites: -> facebook: -> pages:`.
    - **Note**: If you have a list of groups in `sources_to_fill.yaml`, you need to manually copy the valid URLs into `config.yaml`. The system **only** reads from `config.yaml`.

2.  **Cookies (Recommended)**:
    - Facebook often blocks automated access from "checking in" too frequently.
    - **Action**: Export your cookies from your browser (e.g., using a "Get Config.json" or "EditThisCookie" extension) and save them as `cookies.json` in the project root.
    - Ensure the file is valid JSON format.
    - This allows the scraper to access the site as a logged-in user, which is more reliable for Groups.

### C. Discord Setup (Optional)
To receive notifications on Discord:

1.  Create a Webhook in your Discord Server (Server Settings -> Integrations -> Webhooks).
2.  Paste the Webhook URL into `config.yaml`:
    ```yaml
    discord:
      webhook_url: "https://discord.com/api/webhooks/..."
      enabled: true
    ```

---

## 3. Running the Project

Once configured, run the main script:

```bash
python main.py
```

### Automation
To run this daily, you can set up a "cron job" (Linux/Mac) or "Task Scheduler" (Windows) to execute `python main.py` at a specific time.
