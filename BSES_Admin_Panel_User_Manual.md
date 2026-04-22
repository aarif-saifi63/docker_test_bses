# BSES Rajdhani Power Limited
# Chatbot Admin Panel — User Manual

**Version:** 1.0
**Prepared for:** BSES Rajdhani Power Limited
**Document Type:** User Manual

---

## Table of Contents

1. [Introduction](#1-introduction)
2. [Accessing the Admin Panel](#2-accessing-the-admin-panel)
3. [Navigation Overview](#3-navigation-overview)
4. [Dashboard](#4-dashboard)
5. [MIS Reports](#5-mis-reports)
6. [Chatbot Menu](#6-chatbot-menu)
7. [API Keys](#7-api-keys)
8. [Advertisement](#8-advertisement)
9. [Feedback](#9-feedback)
10. [Polls](#10-polls)
11. [Intent Management](#11-intent-management)
12. [Menu Management](#12-menu-management)
13. [Analytics](#13-analytics)
14. [Roles](#14-roles)
15. [User Management](#15-user-management)
16. [Subsidiary Master](#16-subsidiary-master)
17. [Language Management](#17-language-management)
18. [Utter Messages](#18-utter-messages)
19. [Fallback Management](#19-fallback-management)

---

## 1. Introduction

This document is a comprehensive user manual for the **BSES Rajdhani Power Limited Chatbot Admin Panel**. The admin panel enables authorized staff to monitor chatbot activity, manage bot content, configure menus, control user access, and maintain all aspects of the BSES E-Mitra chatbot operations.

The chatbot serves customers across multiple BSES divisions in both **English** and **Hindi**, supporting Registered Consumers as well as New Consumers.

---

## 2. Accessing the Admin Panel

1. Open a web browser and navigate to the Admin Panel URL provided by your system administrator.
2. Enter your **Email** and **Password** credentials.
3. Click **Login** to access the panel.

> **Note:** Your access to sections within the admin panel depends on the Role and Permissions assigned to your account. Contact your system administrator if you are unable to access a required section.

---

## 3. Navigation Overview

The left-hand sidebar provides navigation to all sections of the admin panel:

| Section | Purpose |
|---|---|
| Dashboard | Overview of chatbot activity and key metrics |
| MIS Reports | Detailed reports with graphs and export options |
| Chatbot Menu | Analytics by chatbot submenu option |
| API Keys | Manage external BSES API integrations |
| Advertisement | Create and manage chatbot advertisements |
| Feedback | Manage chatbot feedback questions |
| Polls | Create and manage user polls in the chatbot |
| Intent | Manage NLU intent examples and train the model |
| Menu | Manage chatbot menu and submenu structure |
| Analytics | View poll, feedback, and advertisement analytics |
| Roles | Create and manage access roles |
| User Management | Create and manage admin panel users |
| Subsidiary Master | View complete menu structure per subsidiary |
| Language | Manage chatbot languages |
| Utter Message | Edit chatbot response messages |
| Fallback | Configure fallback messages |

The logged-in user's name is displayed in the top-right corner of the screen.

---

## 4. Dashboard

The Dashboard is the home screen of the admin panel. It provides a real-time overview of chatbot performance and interaction logs.

### 4.1 Key Metric Cards

At the top of the dashboard, five summary cards display important counts for the selected period:

| Card | Description |
|---|---|
| No Supply Complaint Registered | Total no-supply complaints registered via the chatbot |
| Complaints Resolved | Total complaints resolved |
| Payment Initiation Menu Selection | Number of times the payment menu was selected |
| Opted for E-Bill | Users who opted for e-bill (shown as fraction, e.g. 7/13) |
| Duplicate Bill Requested | Number of duplicate bill requests made |

### 4.2 Chat Interactions

Below the metric cards is the **Chat Interactions** section, which displays chatbot session logs.

**Available Filters:**

| Filter | Description |
|---|---|
| Date Range | Displays data for the selected date range |
| Hourly / Daily / Monthly | Toggle to change the view granularity |
| Select Division | Filter by BSES division |
| CA Number | Filter by Consumer Account number |
| Tel. No. | Filter by telephone number |
| Select Source | Filter by source channel |
| Start Hour / End Hour | Filter by time of day |
| Apply Filters | Click to apply selected filters |

**Summary Statistics (displayed below filters):**

| Stat | Description |
|---|---|
| Total Sessions | Total number of chatbot sessions in the selected period |
| Chat Completed | Sessions that were completed vs total |
| Avg. Time | Average session duration |
| Peak Interaction | Time slot with highest chatbot usage |

### 4.3 Chat Logs

Each chat session is displayed as a card showing:
- **User Input** — The message sent by the user
- **System Response** — The bot's reply
- **Quick Reply Buttons** — Options presented to the user (e.g. Registered Consumer / New Consumer)

**Viewing the Full Conversation:**

Click the **View Full Log** button on any chat card to open the **Full Interaction Log** popup. This shows the complete conversation including:
- Interaction number and User ID
- Timestamp of the session
- All user messages, system responses, and buttons shown

Use the **Pagination** controls (First / Previous / Next / Last) to browse through sessions.

---

## 5. MIS Reports

The MIS Reports section provides detailed analytical reports on chatbot interactions with graphical visualizations and data export capabilities.

### 5.1 Filters

The same filters from the Dashboard are available here:
- Date range, Hourly / Daily / Monthly toggle
- Division, CA Number, Tel. No., Source, Start Hour, End Hour
- Click **Apply Filters** to refresh the data

### 5.2 Interaction Graph

- A **bar chart** displays the number of chatbot interactions per hour of the day
- The **Peak Hour** is displayed above the chart (e.g. 12:00 – 14:00)
- Click **Export to Excel** to download the interaction graph data

### 5.3 Chat Statistics

Two **donut charts** provide session breakdowns:

**Chart 1 — Session Completion:**
- Completed sessions
- Left (incomplete) sessions
- Total sessions
- English sessions count
- Hindi sessions count

**Chart 2 — User Type:**
- New Users
- Registered Users

The **Avg. Duration** is displayed at the top of this section.

Click **Export to Excel** to download the statistics data.

### 5.4 Total Interaction Logs

- Lists all chat sessions with User Input and System Response preview
- Click **View Full Log** to see the complete conversation
- Use pagination to browse through all sessions

### 5.5 Bottom Metric Cards

Additional metric cards are displayed at the bottom with a **View** button each:
- **No Supply Complaint Registered**
- **Complaints Resolved**
- **Visually Impaired Analysis Resolved**

Click **View** on any card to see detailed records.

---

## 6. Chatbot Menu

The Chatbot Menu section (Menu Analysis) allows the admin to view chatbot interaction logs filtered by a specific chatbot menu option.

### 6.1 Filters

Same filters as Dashboard and MIS Reports are available. An **Export** button in the top-right allows downloading the filtered data.

### 6.2 Submenus Dropdown

Select a chatbot submenu from the dropdown to view its interaction data. Available submenus include:

- New Connection Application
- New Connection Status
- Streetlight Complaint
- Connect Virtually
- Visually Impaired
- Change Language
- FAQs
- Branches Nearby

### 6.3 Submenu Analytics

After selecting a submenu, four summary banners are displayed:

| Banner | Color | Description |
|---|---|---|
| User Type | Yellow | Count of New vs Registered users who used this menu |
| Selected | Orange | Total number of users who selected this menu option |
| Completed | Green | Sessions that completed successfully |
| Incomplete | Red | Sessions that did not complete |

Below the banners, chat log cards are shown for the selected submenu with the **View Full Log** option and pagination.

---

## 7. API Keys

The API Keys section displays all external BSES APIs integrated into the chatbot. Admins can monitor API usage and update API configurations if endpoints or headers change.

### 7.1 API Keys Table

| Column | Description |
|---|---|
| Main Option | The chatbot menu this API belongs to |
| API Name | Name/description of the API |
| API URL | The API endpoint URL |
| Hit Count | Number of times this API has been called |
| API Headers | Headers sent with each API request |
| Actions | Edit / View / Delete |

**Currently integrated APIs include:**
- Prepaid Meter – Check Balance / Recharge
- Register Complaint
- Select Account CA Number
- Branches Nearby
- Consumption History
- Duplicate Bill
- Visually Impaired
- Bill History
- New Connection Status

### 7.2 Monitoring API Usage

- Use the **date range filter** to view API hit counts over a specific period
- Click **Generate CSV** to export the API usage data

### 7.3 Editing an API

If an API endpoint URL or headers change in the future:

1. Click the **Edit** (pencil) icon next to the API entry
2. The Edit API panel opens on the right side with the following editable fields:
   - **API Name**
   - **API URL** — Update the new endpoint URL
   - **Content Type**
   - **API Headers** — Update key-value header pairs
3. Click **Save** to apply the changes

> **Note:** Only update API details when officially informed of changes by the technical team. Incorrect API configurations will cause the related chatbot feature to stop working.

---

## 8. Advertisement

The Advertisement section allows admins to create, manage, and schedule promotional content that is displayed to users within the chatbot.

### 8.1 Viewing Advertisements

The main page displays all existing advertisements as cards, each showing:
- Thumbnail preview
- Name and Type
- Target Divisions
- Created date and time
- Duration (Start → End date and time)
- Active / Inactive status badge
- **View File** link to preview the attached media
- **Edit** and **Delete** options

### 8.2 Creating a New Advertisement

Click **+ Add Advertisement** in the top-right corner. Fill in the following fields:

| Field | Description |
|---|---|
| Name | A descriptive title for the advertisement |
| Type | When the advertisement is displayed in the chatbot (see types below) |
| Submenus | Which chatbot submenu(s) to attach the advertisement to |
| Divisions | Target specific user divisions (e.g. JANAK PURI, SAKET, ALAKNANDA, R.K. PURAM) |
| Start Time | Date and time when the advertisement becomes active |
| End Time | Date and time when the advertisement automatically becomes inactive |
| Active | Toggle to manually enable or disable the advertisement |
| Thumbnail | Upload an image (PNG, JPG, JPEG), video, or document as the visual |
| Attachment | Upload a supporting file (PDF, DOC, DOCX, image, or video) |

**Advertisement Types:**

| Type | When it Appears |
|---|---|
| on_chatbot_launch | Displayed when the chatbot is first opened by the user |
| on_menu_ad | Displayed when the user selects a menu option |
| after_submenu_ad | Displayed after the user selects a submenu option |
| after_feedback_ad | Displayed after the user completes the feedback flow |

Click **Save** to create the advertisement.

### 8.3 Editing or Deleting an Advertisement

- Click **Edit** on the advertisement card to modify its details
- Click **Delete** to permanently remove the advertisement

> **Note:** The system automatically deactivates the advertisement once the End Time is reached. No manual action is required.

---

## 9. Feedback

The Feedback section allows admins to manage the feedback questions that the chatbot presents to users after completing a menu option.

### 9.1 How Feedback Works in the Chatbot

After a user completes a chatbot service (e.g. bill payment, complaint registration), the bot prompts the user to provide feedback. If the user attempts to skip by selecting "No", the system requires the user to complete the feedback before proceeding.

### 9.2 Viewing Feedback Questions

- Use the **English** and **Hindi** tabs to view feedback questions in each language
- Each question shows its answer options (if applicable)
- Edit and Delete icons are available on each question

**Default feedback questions include:**
1. How difficult was it to use this chatbot? *(options: Very High / High / Low / Very Low / No Difficulty – Easy to Use)*
2. How satisfied are you with this chatbot? *(options: Very Satisfied / Satisfied / Unsatisfied)*
3. Please provide your suggestions/comments about the chatbot *(open text — no options)*

### 9.3 Adding a New Feedback Question

At the bottom of the page, use the **Add New Question** form:

| Field | Description |
|---|---|
| Question | Enter the question text |
| Options (comma separated) | Enter answer choices separated by commas (e.g. Yes, No, Maybe). Leave blank for open-text questions. |

Click **Add Question** to save.

### 9.4 Editing or Deleting a Question

- Click the **Edit** (pencil) icon on any question to modify it
- Click the **Delete** (trash) icon to remove it

> **Note:** Feedback questions should be maintained in both English and Hindi to ensure a consistent experience for all users.

---

## 10. Polls

The Poll Management section allows admins to create time-bound surveys that are displayed to chatbot users based on their division.

### 10.1 Viewing Polls

The main page lists all polls as cards, each showing:
- Poll title
- Active / Inactive status badge
- Start and End date/time
- Type (Division Poll)
- Target divisions
- **Edit** and **Delete** options

### 10.2 Creating a New Poll

Click **+ Create Poll** in the top-right corner. Fill in the following fields:

| Field | Description |
|---|---|
| Title | Name/title of the poll |
| Divisions | Select one or more target divisions (multi-select) |
| Start Time | Date and time when the poll becomes active |
| End Time | Date and time when the poll automatically becomes inactive |
| Active | Toggle to manually enable or disable the poll |

**Adding Questions to the Poll:**

Each poll can have one or more questions. For each question:

| Field | Description |
|---|---|
| Question | Enter the question text |
| Type | Select the response type: **Text** (open answer) or **Star Rating** (5-star rating scale) |

- Click **+ Add Question** to add more questions
- Click the **Delete** (trash) icon to remove a question

Click **Create Poll** to save.

### 10.3 Editing or Deleting a Poll

- Click **Edit** on the poll card to modify its details and questions
- Click **Delete** to permanently remove the poll

> **Note:** Similar to advertisements, polls are automatically deactivated by the system once the End Time is reached.

---

## 11. Intent Management

The Intent Management section is used to manage the NLU (Natural Language Understanding) training data for the Rasa chatbot model. Intents define how the bot recognizes what a user is trying to say.

### 11.1 Viewing Intents

The intent list displays all intents used by the Rasa NLU model in a table with the following columns:

| Column | Description |
|---|---|
| ID | Serial number |
| Intent Name | Technical name of the intent (e.g. `duplicate_bill_rajdhani_hindi`) |
| Chatbot Menu | The menu option this intent is linked to |
| Examples | Sample phrases the bot uses to recognize this intent |
| Actions | Edit icon |

- Use the **Search** bar to find a specific intent by name
- Click **Export** to download the full intent list
- The **Last Trained** timestamp is shown next to the Train Model button

### 11.2 Editing an Intent (Adding Examples)

1. Click the **Edit** icon next to the intent
2. The **Edit Intent** modal opens showing:
   - **Intent Name** — displayed for reference (not editable)
   - **Examples** — existing examples shown as removable tags/chips
3. Add new example phrases to help the bot better recognize this intent
4. Remove outdated or incorrect examples by clicking the × on the tag
5. Click **Update** to save changes

### 11.3 Training the Model

After making changes to any intent examples:

1. Click the **Train Model** button in the top-right corner
2. Wait for the training process to complete
3. Once training is successful, the bot will recognize the updated examples

> **Important:** Changes to intent examples do NOT take effect in the chatbot until the model is retrained. Always click **Train Model** after making changes.

---

## 12. Menu Management

The Menu Management section allows admins to view all chatbot menu options available to users, organized by language and user type (Registered or New Consumer). From this section, admins can create new menus with submenus and configure their intents and training examples. After saving, the new menu option with its submenu will appear in the chatbot once the model is retrained.

### 12.1 Viewing Menus

**Filtering by Subsidiary and User Type:**

Use the dropdown in the top-right corner to switch the view by subsidiary, user type, and language. Available options include:

| Dropdown Option | Description |
|---|---|
| BSES Rajdhani Registered English | Shows English menus for registered consumers |
| BSES Rajdhani New Hindi | Shows Hindi menus for new consumers |
| *(other combinations)* | Other subsidiary / user type / language combinations |

**Table Columns:**

| Column | Description |
|---|---|
| Menu Title | Main menu group name (shown in English or Hindi depending on the selected view) |
| Language | Language of the menu (English / Hindi) |
| Visible | Active / Inactive status badge |
| Submenus | Number of submenus under this menu |
| Actions | Edit, Delete, and additional action icons |

**Currently configured menus (BSES Rajdhani Registered English):**

| Menu Title | Submenus |
|---|---|
| Meter & Connection Services | 5 |
| Complaints & Support Services | 4 |
| Billing & Payment Services | 5 |
| Accessibility & Language Preference | 3 |
| Location & FAQ Services | 2 |

**Currently configured menus (BSES Rajdhani New Hindi):**

| Menu Title | Submenus |
|---|---|
| मीटर और कनेक्शन सेवाएं | 2 |
| शिकायत और सहायता सेवाएं | 2 |
| सुलभता सेवा और भाषा चुनें | 3 |
| स्थान और सामान्य प्रश्न सेवाएं | 2 |

The **Last Trained Bot** information is displayed at the top of the page (e.g. *20260122-125535-pale-expertise at 22 Jan 2026, 06:50 pm*), along with the **Train Model** button.

### 12.2 Expanding a Menu to View Submenus

Click the expand (▾) arrow on any menu row to expand it and view all its submenus. For each submenu the following is shown:

- **Submenu Title** — Name of the submenu
- **Language and Active status** badge
- **Number of intents** linked to this submenu
- **Intent Name** — The technical Rasa intent identifier (e.g. `new_connection_application_brpl_hindi`)
- **Examples** — A few sample training phrases shown inline (e.g. "नया कनेक्शन BRPL")
- **Show X more** link — Click to view all training examples for that intent

### 12.3 Creating a New Menu

Creating a menu is a **two-step process**.

---

#### Step 1 — Menu Details

Click **+ Create Menu** in the top-right corner. The **Create Menu** modal opens with the following fields:

| Field | Description |
|---|---|
| Rajdhani User | Select the subsidiary and user type (e.g. BSES Rajdhani New Hindi). This determines which users will see the new menu |
| Language | Auto-populated based on the selected Rajdhani User — cannot be changed manually |
| Menu Title | Enter the display name for the new menu (e.g. "Main Menu") |
| Menu Icon | Upload an icon image for the menu (PNG / JPEG / JPG / SVG format) |
| Active Status | Toggle to set the menu as Active or Inactive when created |

Click **Next** to proceed to Step 2, or **Cancel** to discard.

---

#### Step 2 — Configure Submenus & Intents

This step allows you to add one or more submenus under the new menu and configure the NLU intents for each submenu.

**For each Submenu:**

| Field | Description |
|---|---|
| Submenu Title | Name of the submenu option shown in the chatbot |
| Active Status | Toggle to set the submenu as Active or Inactive |
| Submenu Icon | Upload an icon for the submenu (PNG / JPEG / JPG / SVG format) |

**For each Intent under the Submenu:**

| Field | Description |
|---|---|
| Resource Type | Select the action type: **Static Utter** or **Dynamic Action** (see below) |
| Utters | Add the chatbot response messages for this submenu (only for Static Utter) |
| Example Links | Add training example phrases that the NLU model will use to recognise user input for this intent |

**Action Types Explained:**

| Resource Type | Description |
|---|---|
| **Static Utter** | No code changes required. The admin defines the bot's response message directly in the admin panel. The chatbot displays this message when the intent is recognized. |
| **Dynamic Action** | Requires a corresponding action to be added in the Rasa backend code by the development team. Use this when the chatbot response involves logic, API calls, or dynamic data (e.g. fetching bill details). |

- Click **+ Add Another Intent** to attach additional intents to the same submenu
- Click **+ Add New Submenu** to add another submenu under the same menu
- Click **Back** to return to Step 1
- Click **Save Menu** to save the new menu, all its submenus, and their intents

> After saving, the new menu option with its submenu will appear in the chatbot **only after clicking Train Model**.

### 12.4 Editing and Deleting Menus

- **Admin-created menus** (new menus added from the admin panel) can be **edited and deleted** using the action icons in the Actions column
- **Pre-existing system menus** are locked and **cannot be edited or deleted**

> **Important:** After creating or modifying any menu or submenu, always click **Train Model** to retrain the Rasa NLU model. The changes will only take effect in the chatbot after successful training.

---

## 13. Analytics

The Analytics section (titled **Analytics Dashboard**) provides insights into how users are interacting with Polls, Feedback, and Advertisements in the chatbot. It is divided into three tabs:

- **Poll Analytics**
- **Feedback Analytics**
- **Advertisement Tracker**

Click a tab to switch between the three views.

---

### 13.1 Poll Analytics

The **Poll Analytics** tab shows how many users responded to polls and what their answers were.

**Filters:**

| Filter | Description |
|---|---|
| Daily / Weekly / Monthly | Toggle to change the time granularity of the data |
| Start Date / End Date | Set a custom date range |
| Apply | Click to apply the selected filters |

**Summary Cards:**

| Card | Description |
|---|---|
| Total Polls | Total number of polls created |
| Active Polls | Polls currently active and visible to users |
| Inactive Polls | Polls that are inactive or expired |
| Total Responses | Total number of user responses received across all polls |

**Poll Response Trend Over Time:**

A line chart showing the number of poll responses received per day over the selected date range.

**Poll Question Analytics:**

Below the trend chart, each poll question is shown as a separate card:

- **Text questions** — Display the user's text response(s) and Total Responses count
- **Star Rating questions** — Display a bar chart of rating distribution, the **Average Rating** (e.g. ⭐ 4.0 ⭐), and Total Responses count

Click **Export to Excel** in the top-right to download all poll analytics data.

---

### 13.2 Feedback Analytics

The **Feedback Analytics** tab shows how many users submitted feedback and their responses to each feedback question.

**Filters:**

| Filter | Description |
|---|---|
| Daily / Weekly / Monthly | Toggle to change the time granularity |
| Language | Filter responses by language (English / Hindi) |
| Start Date / End Date | Set a custom date range |
| Apply | Click to apply the selected filters |

**Summary Cards:**

| Card | Description |
|---|---|
| Total Feedbacks | Total number of feedback submissions received |
| Total Questions | Number of feedback questions configured in the system |
| Most Feedbacks On | The date with the highest number of feedback submissions (with count) |
| Least Feedbacks On | The date with the lowest number of feedback submissions (with count) |

**Feedback Trend Over Time:**

A line chart showing the number of feedback submissions received per day over the selected date range.

**Question Analytics:**

Below the trend chart, each feedback question is displayed as a separate card with a bar chart showing the distribution of user responses and the **Total Responses** count. Questions are shown in the language selected in the filter (e.g. Hindi questions are shown when Hindi is selected).

Click **Export to Excel** in the top-right to download all feedback analytics data.

---

### 13.3 Advertisement Tracker

The **Advertisement Tracker** tab shows detailed engagement data for a specific advertisement over a selected date range.

**Filters:**

| Filter | Description |
|---|---|
| Select Advertisement | Choose the advertisement to analyse from the dropdown |
| Start Date | Set the start of the reporting period |
| End Date | Set the end of the reporting period |
| Fetch Analytics | Click to load the analytics data for the selected advertisement and date range |

**Insights Summary Cards:**

Once analytics are fetched, four metric cards are displayed under **Insights for "[Advertisement Name]"**:

| Card | Description |
|---|---|
| Divisions Involved | Number of BSES divisions in which this advertisement was shown |
| Top Division | The division with the highest engagement for this advertisement |
| Unique CA Numbers | Number of unique Consumer Account numbers that saw this advertisement |
| Total Count | Total number of times this advertisement was displayed to users |

**Tracker Logs:**

A detailed log table below the summary cards shows every individual impression of the advertisement with the following columns:

| Column | Description |
|---|---|
| User Type | Whether the user was a new or registered consumer |
| CA Number | Consumer Account Number of the user (if available) |
| Division | The user's BSES division (if available) |
| Tel No | The user's telephone number (if available) |
| Timestamp | The exact date and time the advertisement was shown |

Click **Export to Excel** to download the tracker log data.

---

## 14. Roles

The Role Management section allows admins to create and manage custom access roles that control what sections and actions a user can access within the admin panel.

### 14.1 Viewing Roles

The main page displays a table with three columns:

| Column | Description |
|---|---|
| Role Name | The name of the role (e.g. Super Admin, Admin, Supervisor) |
| Permissions | All permissions assigned to the role, displayed as blue badge tags |
| Actions | Edit (pencil) and Delete (trash) icons |

**Pre-configured system roles:**

| Role | Description |
|---|---|
| Super Admin | Full access to all permissions across the admin panel |
| Admin | Broad access including dashboard, MIS reports, advertisements, intents, languages, utter messages, and fallback management |
| Supervisor | Limited access — user creation, API key management, and advertisement updates |
| Developer | Similar to Admin — full feature access including analytics, advertisements, intents, and language management |
| Analyst | Core access — user management, role management, polls, feedback, menus, and API keys |

The list uses **infinite scroll** — additional roles load automatically as you scroll down. A **"No more roles"** message is shown at the bottom when all roles have been loaded.

### 14.2 Creating a New Role

1. Click **+ Add Role** in the top-right corner of the page
2. The **Create Role** modal opens with the following fields:

| Field | Description |
|---|---|
| Role Name | Enter a descriptive name for the role (e.g. Viewer, Content Manager, Report Manager) |
| Permissions | A scrollable checklist of all available permissions in the system |

3. Select individual permissions using their checkboxes, or click **Check All** to select every permission at once
   - The **Check All** button toggles to **Uncheck All** when all permissions are selected — click again to deselect all
4. Click **Save** to create the role, or **Cancel** to discard

> **Note:** `dashboard-read` and `mis-report-read` are always pre-selected and locked — they cannot be unchecked. Every role requires these two base permissions as a minimum.

### 14.3 Permission Naming Convention

Permissions follow a `resource-action` naming pattern:

| Example Permission | Meaning |
|---|---|
| `users-create` | Can create new users |
| `users-read` | Can view the user list |
| `users-update` | Can edit existing users |
| `users-delete` | Can delete users |
| `roles-create` | Can create new roles |
| `advertisement-read` | Can view advertisements |
| `intent-update` | Can edit intent examples |
| `language-delete` | Can delete a language |
| `utter-read` | Can view utter messages |
| `fallback-update` | Can edit fallback messages |
| `api-key-read` | Can view API keys |
| `dashboard-read` | Can access the Dashboard *(always required)* |
| `mis-report-read` | Can access MIS Reports *(always required)* |

### 14.4 Editing a Role

1. Click the **Edit** (pencil) icon in the Actions column for the role you want to modify
2. The **Edit Role** modal opens — the same form as Create Role, pre-filled with the role's current name and permissions
3. Update the Role Name or toggle permissions as needed
4. Click **Save** to apply the changes

### 14.5 Deleting a Role

1. Click the **Delete** (trash) icon in the Actions column for the role
2. Confirm the deletion when prompted

> **Important:** Deleting a role will affect all users currently assigned to that role. Before deleting, reassign those users to another role in the User Management section.

---

## 15. User Management

The User Management section allows admins to create and manage user accounts for the admin panel, with fine-grained control over each user's access via roles and individual permissions.

### 15.1 Viewing Users

The user list is displayed as a table with the following columns:

| Column | Description |
|---|---|
| Name | User's display name |
| Email | User's login email address |
| Role | Role badge assigned to the user (e.g. Super Admin, Admin, Developer) |
| Permissions | Two sections: Role Permissions (inherited from role) and User Permissions (individually assigned extras) |
| Actions | Edit and Delete icons |

### 15.2 Creating a New User

Click **+ Add User** in the top-right corner. Fill in the following fields:

| Field | Description |
|---|---|
| Name | User's full name |
| Email | Login email address |
| Password | Set the user's login password |
| Confirm Password | Re-enter the password to confirm |
| Role | Select a role from the dropdown (e.g. Super Admin, Admin, Developer) |
| Role Permissions | Read-only display of the permissions included in the selected role |
| User Permissions | Additional checkboxes to grant specific extra permissions beyond the role |

Click **Add User** to create the account.

### 15.3 Permission System

User access is determined by two layers:

1. **Role Permissions** — Base set of permissions inherited from the assigned role
2. **User Permissions** — Additional permissions granted specifically to this individual user

The user's final access = **Role Permissions + User Permissions**

### 15.4 Editing or Deleting a User

- Click the **Edit** (pencil) icon to update the user's details, role, or permissions
- Click the **Delete** (trash) icon to remove the user's account

> **Note:** Only Super Admins or users with User Management permission can create, edit, or delete users.

---

## 16. Subsidiary Master

The Subsidiary Master section provides a comprehensive read-only view of the chatbot's complete menu structure, organized by subsidiary, user type, and language.

### 16.1 Filtering the View

Use the **dropdown** in the top-right corner to select the view combination, for example:
- BSES Rajdhani – Registered – English
- BSES Rajdhani – New Consumer – Hindi

### 16.2 Menu Structure View

The menu list shows all main menus with the following details:

| Column | Description |
|---|---|
| Menu Title | Main menu group name |
| Language | Language of the menu |
| Visible | Active / Inactive status |
| Submenus | Number of submenus |

**Current Menus (BSES Rajdhani Registered English):**

| Menu Title | Submenus |
|---|---|
| Meter & Connection Services | 5 |
| Complaints & Support Services | 4 |
| Billing & Payment Services | 5 |
| Accessibility & Language Preference | 3 |
| Location & FAQ Services | 2 |

### 16.3 Expanded Submenu View

Click the expand arrow (▾) on any menu to view:
- All submenus under that menu
- Each submenu's associated **intents** and **training example phrases**
- This is useful for reviewing existing training data before making changes in Intent Management

> **Note:** This section is **view-only**. To make changes to menus or intents, use the Menu Management or Intent Management sections.

---

## 17. Language Management

The Language Management section controls which languages are available to users in the chatbot.

### 17.1 Viewing Languages

The language list displays a table with the following columns:

| Column | Description |
|---|---|
| # | Serial number |
| Name | Language name (e.g. हिंदी, English) |
| Code | Language code (e.g. `hi`, `en`) |
| Visible | **Yes** (green) if the language is active and visible to chatbot users |
| Actions | Edit and Delete icons |

The **Last Trained Bot** timestamp is displayed at the top, showing the model version and date of the last training.

### 17.2 Adding a New Language

Click **+ Add Language**. Fill in the following fields:

| Field | Description |
|---|---|
| Language Name | Enter a display name |
| Language Name (dropdown) | Select the language — only **English** and **Hindi** are supported |
| Visibility | Toggle on to make the language visible in the chatbot |

Click **Save** to add the language.

### 17.3 Editing a Language

Click the **Edit** icon on a language row to update its display name or visibility setting.

### 17.4 Enabling or Disabling a Language

- To **disable** a language, edit it and turn off the **Visibility** toggle. Users will no longer see that language option in the chatbot.
- To **re-enable** a language, turn the Visibility toggle back on.

### 17.5 Training the Model

> **Important:** After adding, editing, or changing the visibility of any language, click **Train Model** to retrain the Rasa model. The change will only take effect in the chatbot after successful training.

---

## 18. Utter Messages

The Utter Messages section allows admins to view and edit all response messages that the chatbot displays to users, without requiring any code changes.

### 18.1 Viewing Utter Messages

The message list displays a table with the following columns:

| Column | Description |
|---|---|
| Message Type | Category of the message (e.g. Intro, General_thankyou, New_connection_application) |
| Flow/Chat Menu Option | The action/flow this message belongs to (e.g. `action_register_consumer_options_english`) |
| User Type | Who sees this message (New/Registered (both) or Registered only) |
| Language | **EN** (English) or **HI** (Hindi) badge |
| Text | Truncated preview of the message text |
| Action | Edit button |

Use the **Search** bar to find a specific message. Use **Pagination** (Previous / Next) to browse all messages.

### 18.2 Editing an Utter Message

1. Click the **Edit** button on the message row
2. The **Edit Utter Message** modal opens with the following fields:
   - **Message Type** — Read-only (for reference)
   - **Action Name** — Read-only (for reference)
   - **Class Name** — Read-only (User Type, for reference)
   - **Language** — Read-only (for reference)
   - **Text** — **Editable** — Update the message that the chatbot displays to users
3. Click **Save** to apply the changes

> **Note:** Changes to utter messages take effect in the chatbot **immediately** after saving. No model retraining is required.

---

## 19. Fallback Management

The Fallback Management section allows admins to configure the messages displayed to users when the chatbot cannot understand their input.

### 19.1 What is a Fallback?

A fallback message is displayed when the user's input does not match any recognized intent or expected response. There are two types of fallback:

| Type | Description |
|---|---|
| Global Fallback | Applied across the entire chatbot when the bot cannot understand the user |
| Sub-Menu Fallback | Applied when the user is inside a specific submenu and types something unexpected |

### 19.2 Global Fallback Messages

The **Fallback #1** card displays two messages:

| Message | Description |
|---|---|
| Initial Message | Shown on the **1st and 2nd** unrecognized input (e.g. *"Sorry, I wasn't understanding that. Can you rephrase again?"*) |
| Final Message | Shown after **3 consecutive** unrecognized inputs — provides support contact details including Toll-Free number, WhatsApp, Email, and Website |

**To edit the global fallback messages:**

1. Click the **Edit** button on the Fallback #1 card
2. Update the Initial Message or Final Message text
3. Save the changes

Click **Refresh All** in the top-right to reload the fallback configuration.

### 19.3 Sub-Menu Fallback

The **Sub-Menu Fallback** section lists specific fallback messages for each chatbot submenu.

**Table Columns:**

| Column | Description |
|---|---|
| # | Serial number |
| Sub-Menu Name | The chatbot submenu this fallback applies to |
| Fallback Message | The message displayed when the user input is not recognized within this submenu |
| Actions | Edit and Delete icons |

Use the **Search** bar to find a specific sub-menu fallback entry.

**Adding a New Sub-Menu Fallback:**

1. Click **+ Add Sub-Menu Fallback**
2. Fill in the following fields:

| Field | Description |
|---|---|
| Sub-Menu Name | Name of the chatbot submenu/category |
| Sub-Menu Intent Name | Technical intent identifier (e.g. `faq_billing`, `faq_connection`) |
| Fallback Message | The message text to display when the user input is not recognized |
| User Type | Select which user type this fallback applies to |
| Language | Select the language (English / Hindi) |

3. Click **Save Changes**

**Editing or Deleting a Sub-Menu Fallback:**

- Click the **Edit** (pencil) icon to update the sub-menu fallback message
- Click the **Delete** (trash) icon to remove it

---

## Appendix A: When to Train the Model

The following actions require clicking **Train Model** for changes to take effect in the chatbot:

| Action | Requires Training? |
|---|---|
| Add/update intent examples | Yes |
| Add/edit a menu or submenu | Yes |
| Add/edit a language | Yes |
| Edit an utter message | No — takes effect immediately |
| Edit a fallback message | No — takes effect immediately |
| Create/edit advertisement | No — takes effect immediately |
| Create/edit poll | No — takes effect immediately |
| Create/edit feedback questions | No — takes effect immediately |
| Update API keys | No — takes effect immediately |

---

## Appendix B: Glossary

| Term | Definition |
|---|---|
| Intent | A category of user input that the bot is trained to recognize (e.g. "duplicate bill request") |
| Utter Message | A predefined text response that the bot sends to the user |
| Fallback | A default message shown when the bot cannot understand the user |
| NLU | Natural Language Understanding — the AI component that interprets user messages |
| Rasa | The open-source AI framework powering the BSES chatbot |
| Training | The process of teaching the Rasa model using updated intents and examples |
| Division | A geographic service area of BSES (e.g. JANAK PURI, SAKET, ALAKNANDA, R.K. PURAM) |
| CA Number | Consumer Account Number — a unique identifier for a BSES customer |
| Subsidiary | A BSES entity (e.g. BSES Rajdhani Power Limited — BRPL) |
| Static Utter | A submenu action where the bot response is defined directly in the admin panel |
| Dynamic Action | A submenu action where the bot response requires backend code implementation |

---

*End of Document*

*For technical support, contact your system administrator.*
