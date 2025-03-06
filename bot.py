import discord
from discord.ext import commands
from discord.ext.commands import has_permissions
import sqlite3
import asyncio
import re

# Database setup
db = sqlite3.connect("banned_words.db")
cursor = db.cursor()
cursor.execute("""
    CREATE TABLE IF NOT EXISTS banned_words (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        word TEXT UNIQUE
    )
""")

# Create table for user warnings
cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_warnings (
        user_id INTEGER PRIMARY KEY,
        warnings_count INTEGER DEFAULT 0
    )
""")

db.commit()

# Define the bot and the command prefix
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.guilds = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Spam detection settings
SPAM_INTERVAL = 10  # Time interval in seconds
SPAM_THRESHOLD = 5  # Number of messages within the interval to be considered spam
user_message_log = {}

# Warning system
user_warnings = {}
WARNING_LIMIT = 3  # Number of warnings before temporary mute

# Event: When the bot is ready
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    
    for guild in bot.guilds:
        print(f"[DEBUG] Checking 'Muted' role in {guild.name} ({guild.id})")
        await ensure_muted_role(guild)

async def ensure_muted_role(guild):
    """Ensure the Muted role exists and has correct permissions."""
    mute_role = discord.utils.get(guild.roles, name="Muted")
    
    if mute_role:
        print(f"[DEBUG] 'Muted' role already exists in {guild.name} ({guild.id})")
    else:
        try:
            print(f"[DEBUG] Creating 'Muted' role in {guild.name} ({guild.id})")
            mute_role = await guild.create_role(
                name="Muted",
                reason="To mute users with excessive warnings"
            )

            for channel in guild.channels:
                await channel.set_permissions(mute_role, send_messages=False)

            print(f"[DEBUG] Successfully created 'Muted' role in {guild.name} ({guild.id})")
        except discord.errors.Forbidden:
            print(f"[ERROR] Missing permissions to create 'Muted' role in {guild.name} ({guild.id})")
        except Exception as e:
            print(f"[ERROR] Unexpected error while creating 'Muted' role: {e}")

    return mute_role

# Event: On message
@bot.event
async def on_message(message):
    """Check messages for banned words and handle spam."""
    try:
        if message.author.bot:
            return

        # Skip banned word checks for specific commands
        if message.content.startswith("!addword") or message.content.startswith("!removeword"):
            await bot.process_commands(message)
            return

        # Fetch banned words from the database
        banned_words = fetch_banned_words()

        # Check if the message contains any banned words
        for word in banned_words:
            if re.search(rf"\b{re.escape(word)}\b", message.content.lower()):
                print(f"[DEBUG] Banned word detected: '{word}' in message from user {message.author.id}")
                await message.delete()
                add_warning(message.author, message.guild)  # Add a warning with guild context
                response = await message.channel.send(
                    f"{message.author.mention}, your message contained the banned word: `{word}`. A warning has been added.",
                    delete_after=5
                )
                return

        # Spam detection
        user_id = message.author.id
        current_time = asyncio.get_event_loop().time()

        if user_id not in user_message_log:
            user_message_log[user_id] = []

        user_message_log[user_id].append((message.id, current_time))

        # Remove messages outside the spam interval
        user_message_log[user_id] = [
            (msg_id, timestamp) for msg_id, timestamp in user_message_log[user_id] if current_time - timestamp <= SPAM_INTERVAL
        ]

        if len(user_message_log[user_id]) > SPAM_THRESHOLD:
            # Delete all spam messages from the user
            for msg_id, _ in user_message_log[user_id]:
                msg = await message.channel.fetch_message(msg_id)
                await msg.delete()

            # Add a warning to the user
            add_warning(message.author, message.guild)  # Add a warning with guild context

            # Notify the user
            await message.channel.send(f"{message.author.mention}, please stop spamming. A warning has been added to your record.", delete_after=5)

            # Clear the log for this user to reset tracking
            user_message_log[user_id] = []

        # Allow commands to be processed
        await bot.process_commands(message)
    except discord.errors.Forbidden:
        print(f"Missing permissions to delete message in channel {message.channel.name}.")
    except Exception as e:
        print(f"An error occurred: {e}")

async def mute_user(user, guild):
    if not guild:
        print(f"[ERROR] Guild not found for user {user.id}.")
        return

    mute_role = await ensure_muted_role(guild)  # Ensure the "Muted" role exists

    try:
        member = guild.get_member(user.id)
        if not member:
            print(f"[WARNING] Member {user.id} not found in cache, fetching from API...")
            member = await guild.fetch_member(user.id)

        if not member:
            print(f"[ERROR] Member {user.id} not found in {guild.id}.")
            return

        print(f"[DEBUG] Muting user {user.id} in {guild.name}.")
        await member.add_roles(mute_role, reason="Reached 5 warnings")

        # ✅ Immediately reset warnings when the user is muted
        reset_user_warnings(user.id)
        print(f"[DEBUG] Warnings reset for user {user.id} after mute.")

        print(f"[DEBUG] User {user.id} has been muted for 5 minutes.")

        # Wait for 5 minutes
        await asyncio.sleep(300)

        # Remove "Muted" role after 5 minutes
        await member.remove_roles(mute_role, reason="Mute duration ended")
        print(f"[DEBUG] User {user.id} has been unmuted.")

    except discord.errors.Forbidden:
        print(f"[ERROR] Missing permissions to mute/unmute user {user.id}.")
    except Exception as e:
        print(f"[ERROR] An error occurred while muting user {user.id}: {e}")


# Helper function: Fetch banned words from the database
def fetch_banned_words():
    cursor.execute("SELECT word FROM banned_words")
    words = [row[0].lower() for row in cursor.fetchall()]
    print(f"Banned words fetched: {words}")
    return words

def add_warning(user, guild):
    add_warning_to_user(user.id)  # Add a warning to the database
    current_warnings = get_user_warnings(user.id)  # Retrieve the current number of warnings

    print(f"[DEBUG] Warning added: User {user.id}, Total warnings: {current_warnings}")  # Log warnings

    # If warnings >= 5, call the mute function
    if current_warnings >= 5:
        print(f"[DEBUG] User {user.id} reached 5 warnings. Preparing to mute.")
        asyncio.create_task(mute_user(user, guild))

def reset_user_warnings(user_id):
    cursor.execute("UPDATE user_warnings SET warnings_count = 0 WHERE user_id = ?", (user_id,))
    db.commit()
    print(f"[DEBUG] Warnings reset for user {user_id}.")  # Confirmation of warning reset

# Helper function: Fetch warnings count from the database
def get_user_warnings(user_id):
    cursor.execute("SELECT warnings_count FROM user_warnings WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    return result[0] if result else 0

# Helper function: Add warning to the user in the database
def add_warning_to_user(user_id):
    current_warnings = get_user_warnings(user_id)
    if current_warnings == 0:
        cursor.execute("INSERT INTO user_warnings (user_id, warnings_count) VALUES (?, ?)", (user_id, 1))
    else:
        cursor.execute("UPDATE user_warnings SET warnings_count = warnings_count + 1 WHERE user_id = ?", (user_id,))
    db.commit()

# Command: Show warnings
@bot.command(name="warnings")
async def show_warnings(ctx):
    """Show the current warnings for the user who invoked the command."""
    try:
        user_id = ctx.author.id
        warnings_count = get_user_warnings(user_id)

        response = await ctx.send(f"{ctx.author.mention}, you have {warnings_count} warning(s).")
        await asyncio.sleep(10)
        await response.delete()
    except Exception as e:
        print(f"[ERROR] An error occurred in 'warnings' command: {e}")

# Command: Clear messages
@bot.command(name="clear")
@commands.has_permissions(administrator=True)
async def clear(ctx, amount: int):
    """Clear a specified number of messages from the channel."""
    if amount <= 0:
        await ctx.send("Please specify a valid number of messages to delete.", delete_after=5)
        return

    deleted = await ctx.channel.purge(limit=amount)
    confirmation = await ctx.send(f"Deleted {len(deleted)} messages.")
    await asyncio.sleep(10)
    await confirmation.delete()

# Command: Add a banned word
@bot.command(name="addword")
@commands.has_permissions(administrator=True)
async def add_banned_word(ctx, *, word):
    """Add a word to the banned words list."""
    try:
        # Fetch banned words from the database
        banned_words = fetch_banned_words()
        if word.lower() in banned_words:
            # If the word is already in the database, send a message
            response = await ctx.send(f"The word `{word}` is already in the banned words list.")
            await asyncio.sleep(7)
            await response.delete()
            return

        # Insert the word into the database
        cursor.execute("INSERT INTO banned_words (word) VALUES (?)", (word.lower(),))
        db.commit()
        response = await ctx.send(f"Added `{word}` to the banned words list.")
        await asyncio.sleep(7)
        await response.delete()

    except sqlite3.IntegrityError:
        # Handle unique constraint violation (unlikely due to prior check)
        response = await ctx.send(f"The word `{word}` is already in the banned words list.")
        await asyncio.sleep(7)
        await response.delete()
    except Exception as e:
        # Handle other errors
        response = await ctx.send(f"An error occurred: {str(e)}")
        await asyncio.sleep(7)
        await response.delete()

# Command: Remove a banned word
@bot.command(name="removeword")
@commands.has_permissions(administrator=True)
async def remove_banned_word(ctx, *, word):
    """Remove a word from the banned words list."""
    try:
        # Fetch banned words from the database
        banned_words = fetch_banned_words()
        if word.lower() not in banned_words:
            # If the word is not in the database, notify the user
            response = await ctx.send(f"The word `{word}` is not in the banned words list and cannot be removed.")
            await asyncio.sleep(7)
            await response.delete()
            return

        # Remove the word from the database
        cursor.execute("DELETE FROM banned_words WHERE word = ?", (word.lower(),))
        db.commit()
        response = await ctx.send(f"Removed `{word}` from the banned words list.")
        await asyncio.sleep(7)
        await response.delete()

    except Exception as e:
        # Handle any other errors
        response = await ctx.send(f"An error occurred: {str(e)}")
        await asyncio.sleep(7)
        await response.delete()

# Command: List banned words
@bot.command(name="listwords")
async def list_banned_words(ctx):
    """List all banned words."""
    banned_words = fetch_banned_words()
    if not banned_words:
        response = await ctx.send("No banned words currently.")
        await asyncio.sleep(10)
        await response.delete()
        return

    response = await ctx.send(f"Banned words: {', '.join(banned_words)}")
    await asyncio.sleep(10)
    await response.delete()

# Global check to notify non-admin users
@bot.check
async def is_admin_or_exempt(ctx):
    """Check if the user is an administrator or exempt from restrictions."""
    if ctx.command.name in ["listwords", "warnings"]:
        return True  # These commands are allowed for all users
    
    if ctx.author.guild_permissions.administrator:
        return True

    # Notify the user if they don't have admin permissions
    await ctx.send("You don't have permission to use this command. Only administrators can perform this action.", delete_after=5)
    return False

# Error handler for missing permissions
@bot.event
async def on_command_error(ctx, error):
    """Handle errors related to missing permissions."""
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("You don't have the required permissions to use this command.", delete_after=5)
    elif isinstance(error, commands.CheckFailure):
        await ctx.send("You are not allowed to use this command.", delete_after=5)
    else:
        raise error

# Error handling: Missing permissions
@clear.error
@add_banned_word.error
@remove_banned_word.error
async def missing_permissions_error(ctx, error):
    """Handle missing permissions errors for specific commands."""
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("You don't have permission to use this command.", delete_after=5)


TOKEN = "YOUR_API_TOKEN"  # Replace with your bot's token

# Main function to handle bot start         
async def main():
    """Start the bot and handle shutdown properly."""
    async with bot:
        try:
            await bot.start(TOKEN)
        finally:
            print("Shutting down the bot.")

asyncio.run(main())
