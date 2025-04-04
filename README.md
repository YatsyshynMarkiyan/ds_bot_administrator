# Discord Moderation Bot - Detailed Project Description 🚀

## Project Overview
This project is a Discord moderation bot designed to maintain order in a server by implementing several features:

* Banned words detection and automatic message deletion.
* Spam detection and message purging.
* Warnings system with auto-muting after reaching a threshold.
* Administrator commands for managing banned words and clearing messages.
* Automatic role management, including a "Muted" role.

---

## Features & Functionalities
 
#### Banned Words Detection
* The bot maintains a database of banned words.
* If a user sends a message containing a banned word, the bot:
    * Deletes the message immediately.
    * Sends a warning to the user.
    * Logs the event in the console for debugging.
#### Spam Detection
* The bot monitors the frequency of messages per user.
* If a user sends too many messages in a short interval, the bot:
    * Deletes spam messages automatically.
    * Issues a warning to the user.
    * Prevents further spam by tracking message frequency.
#### Warnings System & Auto-Mute
#### Each violation (banned words or spam) adds a warning to the user.
* If a user reaches 5 warnings, they are:
    * Automatically muted for 5 minutes.
    * Warnings are reset immediately upon mute.
    * The bot handles permissions to prevent muted users from sending messages.
#### Role Management
* The bot creates a "Muted" role automatically if it doesn’t exist.
* This role is configured to block users from sending messages in all channels.
* After 5 minutes, the bot removes the "Muted" role, allowing the user to chat again.
#### Admin Commands
The bot provides several commands for administrators to manage the server:

Command	 | Description
:--------|------------:
!addword \<word> |	Adds a new banned word to the database.
!removeword \<word>	| Removes a word from the banned words list.
!listwords |	Displays all banned words in the database.
!warnings |	Shows the current number of warnings for the user.
!clear \<amount> |	Deletes a specified number of messages from a channel.

#### Error Handling & Stability
The bot catches and logs errors to prevent crashes.
Errors like missing permissions are handled gracefully.
If the bot shuts down unexpectedly, it logs the event.
Technical Implementation
1. Database Management (SQLite)
Stores banned words and user warnings.
Uses SQL queries to insert, update, and retrieve data.
Ensures data persistence across bot restarts.
2. Discord Bot Commands
Uses discord.py and the commands extension.
Implements role management, message tracking, and command processing.
3. Async Programming (asyncio)
The bot uses async functions to handle tasks efficiently.
Implements timeouts, delayed actions, and parallel processing.
4. Error Handling
try-except blocks ensure the bot doesn’t crash.
Provides clear error messages in the console.

---

## Demo screens

![](screens/banned-word-detection.png)
![](screens/bot-databse.png)
![](screens/clear-chat.png)
![](screens/listwords.png)
![](screens/permission-check.png)
![](screens/reactiojn-spam.png)
![](screens/spams-detection.png)
![](screens/warnings.png)

---

## How It Works - Step-by-Step
#### 🏁 Startup Process
* The bot connects to Discord and loads all required permissions.
* It checks if the "Muted" role exists and creates it if necessary.
* It fetches banned words from the database.
* The bot prints a "Ready" message when everything is initialized.
#### 📩 Message Handling
* Every message sent in the server is checked for banned words.
* If a banned word is found, the bot deletes the message and warns the user.
* If the user reaches 5 warnings, the bot mutes them for 5 minutes.
🚫 Spam Detection
* The bot tracks message timestamps per user.
* If a user sends too many messages within a short time, they are flagged for spam.
* The bot deletes spam messages and adds a warning.
#### 🔨 Administrator Controls
* Admins can add or remove banned words using commands.
* Admins can clear messages if needed.
T* he bot ensures only authorized users can modify the banned word list.

---

## Why This Bot is Useful?
* Keeps servers safe by blocking offensive words.
* Prevents spam from overwhelming chat.
* Automates moderation, reducing admin workload.
* Maintains order by warning and muting rule-breakers.
## Future Improvements
* Logging system to track user violations.
* Custom mute durations based on severity.
* Integration with external moderation APIs.

---

## Final Thoughts
This Discord moderation bot is a powerful tool for managing a server efficiently. It automates moderation tasks, protects the chat from spam and banned words, and ensures a clean and friendly environment.

Let me know if you need further enhancements! 🚀

This version is clean, well-organized, and easy to read! Would you like to add or modify any details?

---

# Discord Moderation Bot