import asyncio
import random
from datetime import datetime, timedelta
from Grabber import application, user_collection
from telegram.ext import CommandHandler

# Command handler for /rocket
async def rocket(update, context):
    user_id = update.effective_user.id

    try:
        amount = int(context.args[0])
        stop_at = int(context.args[1])
    except (IndexError, ValueError):
        await update.message.reply_text("Invalid usage, please use /rocket <amount> <stop_at>")
        return

    if amount < 0:
        await update.message.reply_text("Amount must be positive.")
        return

    user_data = await user_collection.find_one({'id': user_id})
    if not user_data:
        await update.message.reply_text("User data not found.")
        return

    balance_amount = user_data.get('balance', 0)
    max_bet = balance_amount * 0.07  # 7% of balance

    if amount > max_bet:
        await update.message.reply_text(f"You can bet up to Ŧ{max_bet} only.")
        return

    if balance_amount < amount:
        await update.message.reply_text("Insufficient balance to place the bet.")
        return

    # Send rocket started message
    await update.message.reply_photo(photo="https://telegra.ph/file/1e84c4b6f9bec6c0fcb8a.jpg", caption="Rocket started! 🚀")

    # Simulate rocket journey
    current_position = 0
    while current_position < stop_at:
        await asyncio.sleep(1)
        current_position += random.randint(1, 100)

    # Check if rocket stopped at the specified position
    if current_position == stop_at:
        # User wins
        await user_collection.update_one(
            {'id': user_id},
            {'$inc': {'balance': amount, 'user_xp': 5}}
        )
        await update.message.reply_text(f"The rocket stopped at {stop_at}.\nYou won Ŧ{amount}!")
    else:
        # User loses
        await user_collection.update_one(
            {'id': user_id},
            {'$inc': {'balance': -amount, 'user_xp': -2}}
        )
        await update.message.reply_text(f"The rocket stopped at {current_position}.\nYou lost Ŧ{amount}.")

    # Notify user about the balance change
    new_balance = await user_collection.find_one({'id': user_id}, projection={'balance': 1})
    await update.message.reply_text(f"Balance: Ŧ{new_balance.get('balance')}")

# Command handler for /ptrade
async def ptrade(update, context):
    user_id = update.effective_user.id

    try:
        amount = int(context.args[0])
        guess = context.args[1].lower()  # Assuming the second argument is "up" or "down"
    except (IndexError, ValueError):
        await update.message.reply_text("Invalid usage, please use /ptrade <amount> <up/down>")
        return

    if amount < 0:
        await update.message.reply_text("Amount must be positive.")
        return

    user_data = await user_collection.find_one({'id': user_id})
    if not user_data:
        await update.message.reply_text("User data not found.")
        return

    balance_amount = user_data.get('balance', 0)
    max_bet = balance_amount * 0.07  # 7% of balance

    if amount > max_bet:
        await update.message.reply_text(f"You can bet up to Ŧ{max_bet} only.")
        return

    if balance_amount < amount:
        await update.message.reply_text("Insufficient balance to place the bet.")
        return

    # Generate a random result ("up" or "down")
    result = random.choice(["up", "down"])

    if result == guess:
        # User wins
        await user_collection.update_one(
            {'id': user_id},
            {'$inc': {'balance': amount, 'user_xp': 5}}
        )
        await update.message.reply_text(f"Randomly chosen: {result}\nYou won Ŧ{amount}!")
    else:
        # User loses
        await user_collection.update_one(
            {'id': user_id},
            {'$inc': {'balance': -amount, 'user_xp': -2}}
        )
        await update.message.reply_text(f"Randomly chosen: {result}\nYou lost Ŧ{amount}.")

    # Notify user about the balance change
    new_balance = await user_collection.find_one({'id': user_id}, projection={'balance': 1})
    await update.message.reply_text(f"Balance: Ŧ{new_balance.get('balance')}")

# Add command handlers
application.add_handler(CommandHandler("rocket", rocket))
application.add_handler(CommandHandler("ptrade", ptrade))
