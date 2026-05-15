# LLORA — Librarian & Staff Manual

**LLORA** (Lorma Library Online Research Assistant) is the library's AI chat assistant. As a librarian, you can monitor patron conversations, manage the chat system settings, and respond to patrons directly through the live chat feature.

---

## Table of Contents

1. [Accessing the Admin Dashboard](#1-accessing-the-admin-dashboard)
2. [Dashboard Overview](#2-dashboard-overview)
3. [Monitoring Patron Sessions](#3-monitoring-patron-sessions)
4. [Live Chat — Responding to Patrons](#4-live-chat--responding-to-patrons)
5. [Managing FAQs and Library Info](#5-managing-faqs-and-library-info)
6. [Setting Library Hours](#6-setting-library-hours)
7. [Managing Staff Contacts](#7-managing-staff-contacts)
8. [Configuring the AI Assistant](#8-configuring-the-ai-assistant)
9. [Analytics and Reports](#9-analytics-and-reports)
10. [Reviewing Patron Feedback](#10-reviewing-patron-feedback)
11. [Exporting and Cleaning Up Data](#11-exporting-and-cleaning-up-data)
12. [Frequently Asked Questions](#12-frequently-asked-questions)

---

## 1. Accessing the Admin Dashboard

Open your browser and go to:

```
https://your-chatbot-url/admin/
```

You will be prompted to log in with your username and password. Contact your system administrator if you do not have credentials.

> **Note:** The admin dashboard is only accessible to authorized staff. Do not share your login credentials.

---

## 2. Dashboard Overview

After logging in, you will see the main dashboard with the following sections in the sidebar:

| Section | What it does |
|---|---|
| **Sessions** | View all patron chat conversations |
| **Analytics** | Usage statistics and charts |
| **Quality** | Patron feedback and unanswered questions |
| **Live Chat** | Active librarian handoff queue and history |
| **Staff Ratings** | Patron satisfaction scores per librarian |
| **AI Settings** | Configure the bot's name and personality |
| **Library Info** | Manage FAQ buttons shown in the widget |
| **Library Hours** | Set opening hours per day |
| **Staff Contacts** | Add librarian emails for notifications |
| **Settings** | Notification preferences |

---

## 3. Monitoring Patron Sessions

### Viewing sessions

Go to **Sessions** in the sidebar. You will see a list of all patron conversations with:

- A friendly display name (e.g. "Blue Owl 42") — patrons are anonymous
- Date and time of the conversation
- Number of messages exchanged
- Status: **Active** (patron is currently chatting) or **Expired** (session ended)

Click any session to open the full conversation transcript.

### Searching sessions

Use the search bar at the top of the Sessions page to find conversations containing a specific word or phrase — useful for finding sessions about a particular topic or book.

### Flagging a session

If a session needs follow-up, click the **Flag** button inside the session detail view and add a note. Flagged sessions appear in the **Flagged Sessions** tab so you can find them easily later.

### Filtering by status

Use the **Active / Expired** filter buttons to narrow down the list.

---

## 4. Live Chat — Responding to Patrons

When a patron clicks the **Librarian** button in the chat widget, you will receive an email notification. Here is the full process:

### Step 1 — Receive the notification

You will get an email with the subject **"📚 A patron wants to ask a librarian"** containing a link to the live chat queue.

### Step 2 — Open the live chat queue

Click the link in the email, or go directly to:

```
https://your-chatbot-url/chat/
```

Enter your name when prompted. This name will be shown to the patron when you join.

### Step 3 — Claim a session

The queue shows all patrons currently waiting. Each card shows:

- The patron's display name
- How long they have been waiting
- Their patron type (Student, Faculty, Alumni, or Visitor)

Click **Claim** on the session you want to handle. Once you claim it, other librarians are automatically notified by email so they know not to join that session.

### Step 4 — Chat with the patron

Type your reply in the message box at the bottom and press **Send** or hit **Enter**.

- You can see the patron's full conversation history with the AI bot above your chat
- The patron sees your messages in real time
- A typing indicator shows when the patron is typing

### Step 5 — End the chat

When you are done, click **End Chat**. The patron will see a message saying the chat has ended and will be returned to the AI assistant. They will also be asked to rate their experience.

### If a session is already claimed

If you click a session that another librarian has already claimed, you will see a message saying who claimed it. You will also receive an email notification automatically.

### Releasing a session

If you claimed a session by mistake, click **Release** to put it back in the queue for another librarian to pick up.

---

## 5. Managing FAQs and Library Info

Go to **Library Info** in the sidebar to manage the quick-reply FAQ buttons shown in the chat widget.

### Adding a new FAQ

1. Click **Add FAQ**
2. Fill in the fields:
   - **Label** — the button text shown in the widget (e.g. `🕐 Library hours`)
   - **Question** — the full question text sent when the patron clicks the button
   - **Answer** — the bot's reply
3. Optionally attach an **image** (max 200 KB) or a **PDF** (max 5 MB) to be shown with the reply
4. Click **Save**

### Editing an existing FAQ

Click the **Edit** (pencil) icon next to any FAQ item, make your changes, and click **Save**.

### Reordering FAQs

Drag and drop FAQ items to change the order they appear in the widget.

### Deleting a FAQ

Click the **Delete** (trash) icon next to the FAQ item. This cannot be undone.

### Tips for writing good FAQs

- Keep the **Label** short — it appears as a button in the widget
- Write the **Question** as a patron would naturally ask it (e.g. "What are the library hours?")
- The **Answer** should be complete and self-contained — the patron may not ask a follow-up
- Use plain language — avoid jargon
- For hours and policies with multiple details, consider attaching an image of the official schedule

---

## 6. Setting Library Hours

Go to **Library Hours** in the sidebar.

Set the opening and closing times for each day of the week. Use 24-hour format (e.g. `07:00` for 7:00 AM, `19:00` for 7:00 PM).

To mark a day as closed, leave the time windows empty.

### Why this matters

The **Librarian** button in the chat widget is automatically:

- **Enabled** during library hours
- **Disabled** 30 minutes before closing time
- **Disabled** on closed days, with a message showing the next available time

Always keep library hours up to date so patrons know when they can reach a librarian.

---

## 7. Managing Staff Contacts

Go to **Staff Contacts** in the sidebar to manage who receives email notifications when a patron requests a librarian.

### Adding a staff contact

1. Click **Add Contact**
2. Enter the librarian's **Name** and **Email address**
3. Click **Save**

The contact is active by default. All active contacts receive an email whenever a patron clicks the Librarian button.

### Deactivating a contact

Toggle the **Active** switch off to stop sending notifications to that person without deleting their record. Useful for staff who are on leave.

### Removing a contact

Click **Delete** to permanently remove a contact.

> **Tip:** Add all librarians who are available to handle live chat. The first one to click the link in their email gets the session.

---

## 8. Configuring the AI Assistant

Go to **AI Settings** in the sidebar to customize how LLORA behaves.

| Field | Description |
|---|---|
| **Assistant Name** | The name shown in the widget header (default: `LLORA`) |
| **Personality** | How the bot speaks — tone, style, emoji usage |
| **Limitations** | Topics the bot is restricted to (keep this focused on library topics) |
| **Welcome Message** | The first message shown when a patron opens the chat. Use `{name}` to insert the bot name |

Click **Save** to apply changes immediately — no restart needed.

> **Important:** Do not remove the topic limitations unless you want the bot to answer general knowledge questions. Keeping it focused on library topics gives patrons more accurate and relevant responses.

---

## 9. Analytics and Reports

Go to **Analytics** in the sidebar to view usage statistics.

### Available charts and metrics

| Metric | Description |
|---|---|
| **Intent Breakdown** | What types of questions patrons are asking (catalog search, library info, greetings, etc.) |
| **Hourly Activity** | Which hours of the day are busiest |
| **Daily Activity** | Which days of the week are busiest |
| **Avg. Messages per Session** | How long conversations typically are |
| **Failed Queries** | Questions the bot could not answer well |
| **Total User Messages** | Total patron messages in the selected period |

Use the **Days** selector (7, 30, 90, 365) to change the time range.

### Using analytics to improve the FAQ

Check the **Failed Queries** count and the **Quality → Unanswered Queries** section regularly. If patrons are repeatedly asking questions the bot cannot answer, add those questions to the FAQ in **Library Info**.

---

## 10. Reviewing Patron Feedback

Go to **Quality** in the sidebar.

### Feedback (thumbs up / thumbs down)

Patrons can rate individual bot responses with a thumbs up or thumbs down. The **Feedback** tab shows:

- The patron's question
- The bot's response
- The rating given
- The date

Use negative feedback to identify responses that need improvement — either by updating the FAQ answer or adjusting the AI personality settings.

### Unanswered Queries

The **Unanswered Queries** tab lists patron messages that the bot classified as unclear or off-topic. Review these regularly to find gaps in your FAQ coverage.

### Staff Ratings

Go to **Staff Ratings** to see how patrons rated their live chat experience with each librarian. Ratings are on a 1–4 scale:

| Rating | Meaning |
|---|---|
| 1 | Not Satisfied |
| 2 | Moderately Satisfied |
| 3 | Satisfied |
| 4 | Very Satisfied |

---

## 11. Exporting and Cleaning Up Data

### Exporting sessions to CSV

Go to **Sessions** and click **Export CSV**. You can filter by status or date range before exporting. The CSV file can be opened in Excel or Google Sheets.

The export includes: session ID, timestamps, message count, status, all messages with roles and intents.

### Deleting old sessions

Go to **Sessions → Cleanup** to delete expired sessions older than a specified number of days. This keeps the database lean and removes old patron data.

> **Recommendation:** Run a cleanup every 30–90 days to remove sessions older than 30 days.

### Deleting live chat history

Go to **Live Chat → History** and use the **Delete** option to remove completed live chat records older than a specified number of days.

---

## 12. Frequently Asked Questions

**A patron says the Librarian button is greyed out — why?**

The button is automatically disabled 30 minutes before closing time and on closed days. Check that the library hours in **Library Hours** are set correctly.

**I didn't receive an email notification when a patron requested a librarian.**

Check that your email is listed and active in **Staff Contacts**. Also check your spam folder. If using Gmail, make sure the App Password is still valid.

**A patron is waiting but I can't claim the session.**

Another librarian may have already claimed it. Refresh the live chat queue page — claimed sessions show the librarian's name. You will also receive an automatic email confirming who claimed it.

**How do I change the bot's name from LLORA?**

Go to **AI Settings** and update the **Assistant Name** field. The change takes effect immediately.

**Can I see who a patron is?**

Patrons are identified by a randomly generated display name (e.g. "Blue Owl 42") to protect their privacy. However, when a patron requests a librarian, they are asked to provide their patron type (Student, Faculty, Alumni, Visitor) and additional details — this information is visible in the live chat session.

**The bot gave a wrong answer about library hours. How do I fix it?**

Go to **Library Info**, find the FAQ item for library hours, and update the answer. Changes take effect immediately.

**How do I add a new FAQ button to the widget?**

Go to **Library Info → Add FAQ**, fill in the label, question, and answer, then click Save. The new button appears in the widget immediately.

---

*LLORA Librarian Manual — Lorma Colleges Library — May 2026*
