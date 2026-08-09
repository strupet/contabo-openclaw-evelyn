---
name: gog-cli
description: Google Workspace CLI (gog) — command reference for Gmail, Calendar, Drive, Sheets, Docs, Tasks, Contacts, Meet.
---

# gog — Google Workspace CLI

Fast, script-friendly CLI for Google Workspace. All commands output structured JSON with `--json` or stable TSV with `--plain`.

## Global Flags

```
--account <email>   Account to use (or set GOG_ACCOUNT)
--client <name>     OAuth client (default: "default")
--json              Structured JSON output
--plain             Stable TSV output (no colors)
--force             Skip confirmations
--verbose           Verbose logging
```

## Runtime Notes

- In AlphaClaw-managed deployments, gog state lives under `$OPENCLAW_STATE_DIR` (typically `/data/.openclaw`).
- If a direct shell `gog ...` command falls back to `/root/.config/gogcli` or `/root/.openclaw`, rerun it with `XDG_CONFIG_HOME="${OPENCLAW_STATE_DIR:-$OPENCLAW_HOME/.openclaw}"` so gog uses the managed state dir.
- Always pass `--account <email>` (and `--client <name>` if not "default") so gog targets the correct account.

## Connected Accounts

| Email | Client | Services |
| ----- | ------ | -------- |
| evelyn.angerer@gmail.com | personal | calendar, contacts, gmail, docs, sheets, drive, tasks, meet |

## Gmail

```bash
# Search threads (returns thread IDs + snippets)
gog gmail search 'newer_than:7d' --max 10
gog gmail search 'from:alice@example.com subject:invoice' --max 20

# Search individual messages (add --include-body to fetch bodies)
gog gmail messages search 'newer_than:7d' --max 10 --include-body

# Read a thread and optionally download attachments
gog gmail thread get <threadId>
gog gmail thread get <threadId> --download --out-dir ./attachments

# Read a single message
gog gmail get <messageId>

# Modify labels on a thread
gog gmail thread modify <threadId> --add STARRED --remove INBOX

# Send email (plain text)
gog gmail send --to recipient@example.com --subject "Subject" --body "Body text"

# Send email (HTML)
gog gmail send --to recipient@example.com --subject "Subject" --body "Plain fallback" --body-html "<p>Hello</p>"

# Reply to a message (with quoted original)
gog gmail send --reply-to-message-id <messageId> --quote --to recipient@example.com --subject "Re: Subject" --body "Reply text"

# Send with body from file or stdin
gog gmail send --to recipient@example.com --subject "Subject" --body-file ./message.txt
gog gmail send --to recipient@example.com --subject "Subject" --body-file -

# Labels
gog gmail labels list
gog gmail labels get INBOX --json
gog gmail labels create "My Label"
gog gmail labels delete <labelIdOrName>

# Drafts
gog gmail drafts list
gog gmail drafts create --to recipient@example.com --subject "Draft" --body "Body"
gog gmail drafts update <draftId> --subject "Updated" --body "New body"
gog gmail drafts send <draftId>

# Batch operations
gog gmail batch modify <messageId1> <messageId2> --add STARRED --remove INBOX
gog gmail batch delete <messageId1> <messageId2>

# Filters
gog gmail filters list
gog gmail filters create --from 'noreply@example.com' --add-label 'Notifications'
gog gmail filters delete <filterId>

# Vacation / auto-reply
gog gmail vacation get
gog gmail vacation enable --subject "Out of office" --message "I'm away"
gog gmail vacation disable

# History (for incremental sync)
gog gmail history --since <historyId>
```

Output: use `--json` for structured output, `--plain` for TSV.

## Calendar

```bash
# List calendars
gog calendar calendars

# Today's events
gog calendar events <calendarId> --today
gog calendar events <calendarId> --tomorrow
gog calendar events <calendarId> --week
gog calendar events <calendarId> --days 3

# Events from all calendars
gog calendar events --all --today

# Date range
gog calendar events <calendarId> --from 2025-01-15T00:00:00Z --to 2025-01-22T00:00:00Z

# Search events
gog calendar search "meeting" --today
gog calendar search "standup" --days 30

# Get single event
gog calendar event <calendarId> <eventId>

# Create event
gog calendar create <calendarId> --summary "Meeting" --from 2025-01-15T10:00:00Z --to 2025-01-15T11:00:00Z
gog calendar create <calendarId> --summary "Team Sync" --from 2025-01-15T14:00:00Z --to 2025-01-15T15:00:00Z --attendees "alice@example.com,bob@example.com" --location "Zoom"

# Recurrence + reminders
gog calendar create <calendarId> --summary "Weekly" --from 2025-01-15T09:00:00Z --to 2025-01-15T09:30:00Z --rrule "RRULE:FREQ=WEEKLY" --reminder "popup:15m"

# Update event
gog calendar update <calendarId> <eventId> --summary "Updated" --from 2025-01-15T11:00:00Z --to 2025-01-15T12:00:00Z

# Add attendees without replacing existing
gog calendar update <calendarId> <eventId> --add-attendee "alice@example.com"

# Send notifications
gog calendar create <calendarId> --summary "Sync" --from ... --to ... --send-updates all
gog calendar update <calendarId> <eventId> --send-updates externalOnly

# Delete event
gog calendar delete <calendarId> <eventId>

# RSVP to invitation
gog calendar respond <calendarId> <eventId> --status accepted
gog calendar respond <calendarId> <eventId> --status declined
gog calendar respond <calendarId> <eventId> --status tentative

# Free/busy check
gog calendar freebusy --calendars "primary,work@example.com" --from 2025-01-15T00:00:00Z --to 2025-01-16T00:00:00Z

# Conflict detection
gog calendar conflicts --calendars "primary" --today

# Special event types
gog calendar create primary --event-type focus-time --from ... --to ...
gog calendar create primary --event-type out-of-office --from ... --to ... --all-day
```

JSON output includes `startDayOfWeek`, `endDayOfWeek`, `timezone`, and `startLocal`/`endLocal` fields.
Use `primary` as calendarId for the user's default calendar.

## Drive

```bash
# List files (default: all accessible files including shared drives)
gog drive ls --max 20
gog drive ls --parent <folderId> --max 20
gog drive ls --no-all-drives

# Search files
gog drive search "invoice" --max 20
gog drive search "mimeType = 'application/pdf'" --raw-query

# Get file metadata
gog drive get <fileId>
gog drive url <fileId>

# Download file
gog drive download <fileId> --out ./downloaded.bin

# Export Google Workspace files
gog drive download <fileId> --format pdf --out ./exported.pdf
gog drive download <fileId> --format docx --out ./doc.docx

# Upload file
gog drive upload ./path/to/file --parent <folderId>
gog drive upload ./file.docx --convert
gog drive upload ./file --replace <fileId>

# Copy file
gog drive copy <fileId> "Copy Name"

# Organize
gog drive mkdir "New Folder"
gog drive mkdir "New Folder" --parent <parentFolderId>
gog drive rename <fileId> "New Name"
gog drive move <fileId> --parent <destinationFolderId>
gog drive delete <fileId>
gog drive delete <fileId> --permanent

# Permissions
gog drive permissions <fileId>
gog drive share <fileId> --to user --email user@example.com --role reader
gog drive share <fileId> --to user --email user@example.com --role writer
gog drive unshare <fileId> --permission-id <permissionId>

# Shared drives
gog drive drives --max 100
```

## Sheets

```bash
# Spreadsheet metadata (sheets list, properties)
gog sheets metadata <spreadsheetId>

# Read cell range
gog sheets get <spreadsheetId> 'Sheet1!A1:B10'

# Write cells (pipe-delimited rows, comma-separated columns)
gog sheets update <spreadsheetId> 'A1' 'val1|val2,val3|val4'
gog sheets update <spreadsheetId> 'A1' --values-json '[["a","b"],["c","d"]]'

# Append rows
gog sheets append <spreadsheetId> 'Sheet1!A:C' 'new|row|data'

# Clear range
gog sheets clear <spreadsheetId> 'Sheet1!A1:B10'

# Create spreadsheet
gog sheets create "My Spreadsheet" --sheets "Sheet1,Sheet2"

# Copy spreadsheet
gog sheets copy <spreadsheetId> "Copy Name"

# Export
gog sheets export <spreadsheetId> --format pdf --out ./sheet.pdf
gog sheets export <spreadsheetId> --format xlsx --out ./sheet.xlsx

# Format cells
gog sheets format <spreadsheetId> 'Sheet1!A1:B2' --format-json '{"textFormat":{"bold":true}}' --format-fields 'userEnteredFormat.textFormat.bold'

# Insert rows/columns
gog sheets insert <spreadsheetId> "Sheet1" rows 2 --count 3
gog sheets insert <spreadsheetId> "Sheet1" cols 3 --after

# Cell notes and hyperlinks
gog sheets notes <spreadsheetId> 'Sheet1!A1:B10'
gog sheets links <spreadsheetId> 'Sheet1!A1:B10'
```

Write format: rows separated by `,` and columns by `|`. Use `--values-json` for complex data.
`--copy-validation-from` copies data validation from a reference range when updating/appending.

## Docs

```bash
# Document info
gog docs info <docId>

# Read document text
gog docs cat <docId>
gog docs cat <docId> --max-bytes 10000
gog docs cat <docId> --tab "Notes"
gog docs cat <docId> --all-tabs

# List tabs
gog docs list-tabs <docId>

# Create document
gog docs create "My Doc"
gog docs create "My Doc" --file ./doc.md

# Copy document
gog docs copy <docId> "My Doc Copy"

# Export
gog docs export <docId> --format pdf --out ./doc.pdf
gog docs export <docId> --format docx --out ./doc.docx
gog docs export <docId> --format txt --out ./doc.txt

# Update document content (markdown)
gog docs update <docId> --format markdown --content-file ./doc.md
gog docs write <docId> --replace --markdown --file ./doc.md

# Find and replace
gog docs find-replace <docId> "old text" "new text"

# Sed-style editing (sedmat) with markdown formatting
gog docs sed <docId> 's/hello/**hello**/'          # bold
gog docs sed <docId> 's/hello/*hello*/'             # italic
gog docs sed <docId> 's/hello/`hello`/'             # monospace
gog docs sed <docId> 's/hello/__hello__/'           # underline
gog docs sed <docId> 's/Google/[Google](https://google.com)/'  # link
gog docs sed <docId> 's/{{LOGO}}/![](https://example.com/logo.png)/'  # image

# Tables via sedmat
gog docs sed <docId> 's/{{TABLE}}/|3x4|/'           # create 3-row, 4-col table
gog docs sed <docId> 's/|1|[A1]/**Name**/'          # set cell A1
```

## Tasks

```bash
# List task lists
gog tasks lists

# List tasks in a list
gog tasks list <tasklistId> --max 50

# Get single task
gog tasks get <tasklistId> <taskId>

# Create task list
gog tasks lists create "My List"

# Add task
gog tasks add <tasklistId> --title "Task title"
gog tasks add <tasklistId> --title "Weekly sync" --due 2025-02-01 --repeat weekly --repeat-count 4

# Update task
gog tasks update <tasklistId> <taskId> --title "Updated title"

# Complete / uncomplete task
gog tasks done <tasklistId> <taskId>
gog tasks undo <tasklistId> <taskId>

# Delete task / clear completed
gog tasks delete <tasklistId> <taskId>
gog tasks clear <tasklistId>
```

Due dates are date-only; time components may be ignored by Google Tasks.

## Contacts

```bash
# List personal contacts
gog contacts list --max 50

# Search contacts
gog contacts search "Ada" --max 50

# Get contact by resource name or email
gog contacts get people/<resourceName>
gog contacts get user@example.com

# Create contact
gog contacts create --given "John" --family "Doe" --email "john@example.com" --phone "+1234567890"

# Update contact
gog contacts update people/<resourceName> --given "Jane" --email "jane@example.com" --notes "Updated"

# Delete contact
gog contacts delete people/<resourceName>

# Other contacts (people you've interacted with)
gog contacts other list --max 50
gog contacts other search "John" --max 50

# Workspace directory (Google Workspace only)
gog contacts directory list --max 50
gog contacts directory search "Jane" --max 50
```

## Meet

```bash
# List meeting spaces
gog meet spaces list
```
