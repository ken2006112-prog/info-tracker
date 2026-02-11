# How to fix "Usage of Google App Password"

If you can't create a Google App Password, 99% of the time it is because **2-Step Verification (2FA)** is NOT enabled. Google **requires** 2FA to be on before it lets you create an App Password.

## Step-by-Step Fix

1.  **Go to Google Account Security**:
    - Visit: [https://myaccount.google.com/security](https://myaccount.google.com/security)
2.  **Enable 2-Step Verification**:
    - Look for "How you sign in to Google".
    - Click **2-Step Verification**.
    - If it says "Off", click it and follow the steps to turn it **ON** (you'll need a phone number).
3.  **Generate App Password**:
    - Once 2FA is ON, go back to the Security page.
    - Search for "App passwords" in the top search bar (or look under "2-Step Verification" settings).
    - Click **App passwords**.
    - Create a new one named "Info Tracker".
    - Copy the 16-character code (e.g., `abcd efgh ijkl mnop`).
4.  **Update Config**:
    - Paste that code into your `config.yaml` (or GitHub Secret).

## Alternative: Use a different email
If you still can't get it to work, you can use an **Outlook.com** or **Yahoo** account to send the email.
1.  Create a free Outlook/Hotmail account.
2.  Update `notifier.py` to use `smtp.office365.com` (port 587).
