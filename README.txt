CALENDAR NUKE TOOL
==================

Overview
--------
This tool allows Google Workspace Admins to search for and delete ("nuke") malicious or unwanted calendar events across their domain. It is useful for removing phishing invites or spam events from multiple users' calendars simultaneously.

Features:
-   Search by Keyword, Organizer Email, and Date Range.
-   Target specific groups via configuration.
-   Multi-threaded scanning for speed.
-   "Nuke" functionality to delete selected events.

Prerequisites
-------------
1.  Python 3.x installed.
2.  A Google Cloud Project with the following APIs enabled:
    -   Google Calendar API
    -   Admin SDK API

3.  **Service Account Setup (CRITICAL)**:
    -   Create a Service Account in your Google Cloud Project.
    -   Enable **Domain-Wide Delegation** for this Service Account.
    -   Download the JSON key file.
    -   In the Google Workspace Admin Console (Security > Controls > API Controls > Domain-wide Delegation), grant the Service Account Client ID the following scopes:
        -   `https://www.googleapis.com/auth/calendar`
        -   `https://www.googleapis.com/auth/admin.directory.user.readonly`

Installation
------------
1.  Install dependencies:
    `pip install -r requirements.txt`

2.  Place your Service Account JSON file in this folder.
    (Default name: `service_account.json`)

Configuration
-------------
1.  Copy `config.example.json` to a new file named `config.json`.
2.  Edit `config.json` with your specific details:
    
    -   `service_account_file`: The filename of your JSON key (e.g., "service_account.json").
    -   `delegated_user`: The email address of a Super Admin user in your Workspace. The Service Account will "impersonate" this user to perform actions.
    -   `target_groups`: Define the buttons that appear in the UI.
        
        Example:
        "target_groups": [
            { "name": "Staff", "domain": "staff.school.edu" },
            { "name": "Students", "domain": "students.school.edu" }
        ]

Usage
-----
Run the tool using the following command:

    python calendar_nuke.pyw

1.  Select your "Target Group".
2.  Enter search criteria (Keyword or Organizer is required).
3.  Click "SCAN DOMAIN FOR EVENTS".
4.  Review the "Found Events" list. Uncheck any you do NOT want to delete.
5.  Click "NUKE SELECTED EVENTS" to delete them.

Security Warning
----------------
*   **DO NOT COMMIT** `service_account.json` or `config.json` to GitHub or any public repository.
*   These files contain sensitive credentials that allow access to your domain's data.
