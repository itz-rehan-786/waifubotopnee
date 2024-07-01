from telegram.ext import Updater, CommandHandler, CallbackContext
from Grabber import application, user_collection
from telegram import Update
from datetime import datetime, timedelta
import asyncio
import math

# Dictionary to store last payment times
last_payment_times = {}

last_loan_times = {}

async def balance(update, context):
    user_id = update.effective_user.id
    user_data = await user_collection.find_one({'id': user_id}, projection={'balance': 1, 'saved_amount': 1, 'loan_amount': 1, 'potion_amount': 1, 'potion_expiry': 1})

    if user_data:
        balance_amount = user_data.get('balance', 0)
        saved_amount = user_data.get('saved_amount', 0)
        loan_amount = user_data.get('loan_amount', 0)
        potion_amount = user_data.get('potion_amount', 0)
        potion_expiry = user_data.get('potion_expiry')

        formatted_balance = "<code>Ŧ{:,.0f}</code>".format(balance_amount)
        formatted_saved = "<code>Ŧ{:,.0f}</code>".format(saved_amount)
        formatted_loan = "<code>Ŧ{:,.0f}</code>".format(loan_amount)

        balance_message = (
            f"🔹 <b>Your Current Balance:</b> {formatted_balance}\n"
            f"🔸 <b>Amount Saved:</b> {formatted_saved}\n"
            f"🔻 <b>Loan Amount:</b> {formatted_loan}\n"
            f"🔹 <b>Potion Amount:</b> {potion_amount}\n"
        )

        if potion_expiry:
            time_remaining = potion_expiry - datetime.now()
            balance_message += f"⏳ <b>Potion Time Remaining:</b> {time_remaining}\n"

        await update.message.reply_text(balance_message, parse_mode='HTML')
    else:
        balance_message = "You haven't added any character yet. Please add a character to unlock all features."
        await update.message.reply_text(balance_message, parse_mode='HTML')

async def save(update, context):
    try:
        amount = int(context.args[0])
        if amount <= 0:
            raise ValueError("Amount must be greater than zero.")
    except (IndexError, ValueError):
        await update.message.reply_text("Invalid amount. Please provide a positive integer.")
        return

    user_id = update.effective_user.id
    user_data = await user_collection.find_one({'id': user_id}, projection={'balance': 1})

    if user_data:
        balance_amount = user_data.get('balance', 0)

        if amount > balance_amount:
            await update.message.reply_text("Insufficient balance to save this amount.")
            return

        new_balance = balance_amount - amount

        # Update user balance and saved amount
        await user_collection.update_one({'id': user_id}, {'$set': {'balance': new_balance}, '$inc': {'saved_amount': amount}})

        await update.message.reply_text(f"You saved Ŧ{amount} in your bank account.")
    else:
        await update.message.reply_text("User data not found.")


async def withdraw(update, context):
    try:
        amount = int(context.args[0])
        if amount <= 0:
            raise ValueError("Amount must be greater than zero.")
        if amount > 1182581151717:  # Set the withdrawal limit here
            await update.message.reply_text("Withdrawal amount exceeds the limit is 1182581151717.")
            return
    except (IndexError, ValueError):
        await update.message.reply_text("Invalid amount. Please provide a positive integer.")
        return

    

    user_id = update.effective_user.id
    user_data = await user_collection.find_one({'id': user_id}, projection={'balance': 1, 'saved_amount': 1})

    if user_data:
        saved_amount = user_data.get('saved_amount', 0)

        if amount > saved_amount:
            await update.message.reply_text("Insufficient saved amount to withdraw.")
            return

        new_saved_amount = saved_amount - amount

        # Update user balance and saved amount
        await user_collection.update_one({'id': user_id}, {'$inc': {'balance': amount, 'saved_amount': -amount}})

        await update.message.reply_text(f"You withdrew `Ŧ{amount}` from your bank account.")
    else:
        await update.message.reply_text("User data not found.")

async def loan(update, context):
    try:
        loan_amount = int(context.args[0])
        if loan_amount <= 0 or loan_amount > 10000000000000:
            raise ValueError("Amount must be between 1 and 10000000000000.")
    except (IndexError, ValueError):
        await update.message.reply_text("Invalid loan amount. Please provide a limit amount is 10000000000000.")
        return

    user_id = update.effective_user.id
    user_data = await user_collection.find_one({'id': user_id}, projection={'balance': 1, 'loan_amount': 1})

    if user_data:
        if 'loan_amount' in user_data and user_data['loan_amount'] > 0:
            await update.message.reply_text("You still have an existing loan. Please repay it before taking a new one.")
            return

        current_time = datetime.now()
        loan_due_date = current_time + timedelta(days=10)

        new_balance = user_data.get('balance', 0) + loan_amount
        await user_collection.update_one(
            {'id': user_id},
            {'$set': {'balance': new_balance, 'loan_amount': loan_amount, 'loan_due_date': loan_due_date}}
        )

        await update.message.reply_text(f"You successfully took a loan of Ŧ{loan_amount}. You must repay it within 10 days to avoid a penalty.")
        log_message = f"Loan: +{loan_amount} tokens | User ID: {user_id} | Time: {current_time.strftime('%Y-%m-%d %H:%M:%S')}"
        await context.bot.send_message(926282726, log_message)  # Send log to specified user ID via DM
    else:
        await update.message.reply_text("User data not found.")



async def repay(update, context):
    try:
        repayment_amount = int(context.args[0])
        if repayment_amount <= 0:
            raise ValueError("Amount must be greater than zero.")
    except (IndexError, ValueError):
        await update.message.reply_text("Invalid repayment amount. Please provide a positive integer.")
        return

    user_id = update.effective_user.id
    user_data = await user_collection.find_one({'id': user_id}, projection={'balance': 1, 'loan_amount': 1, 'loan_due_date': 1})

    if user_data:
        loan_amount = user_data.get('loan_amount', 0)
        loan_due_date = user_data.get('loan_due_date')
        current_time = datetime.now()

        if repayment_amount > loan_amount:
            await update.message.reply_text("Repayment amount cannot exceed the loan amount.")
            return

        if current_time > loan_due_date:
            overdue_hours = (current_time - loan_due_date).total_seconds() / 3600
            penalty = math.ceil(overdue_hours) * (loan_amount * 0.05)
            repayment_amount += penalty
            await update.message.reply_text(f"You have a penalty of Ŧ{penalty:.2f} due to late repayment.")

        new_loan_amount = loan_amount - repayment_amount
        new_balance = user_data.get('balance', 0) - repayment_amount

        await user_collection.update_one({'id': user_id}, {'$set': {'loan_amount': new_loan_amount, 'balance': new_balance}})

        await update.message.reply_text(f"You successfully repaid `✓{repayment_amount}` of your loan.")
    else:
        await update.message.reply_text("User data not found.")
      

async def mpay(update, context):
    sender_id = update.effective_user.id

    # Check if the command was a reply
    if not update.message.reply_to_message:
        await update.message.reply_text("Please reply to a user to /pay.")
        return

    # Extract the recipient's user ID
    recipient_id = update.message.reply_to_message.from_user.id

    # Prevent user from paying themselves
    if sender_id == recipient_id:
        await update.message.reply_text("You can't pay yourself.")
        return

    # Parse the amount from the command
    try:
        amount = int(context.args[0])
        if amount <= 0:
            raise ValueError("Amount must be greater than zero.")
        if amount > 10000000000:
            raise ValueError("You can't pay more than 10000000000 Tokens at once.")
    except (IndexError, ValueError):
        await update.message.reply_text("You can only pay up to 10000000000 tokens.")
        return

    # Check if the sender has enough balance
    sender_balance = await user_collection.find_one({'id': sender_id}, projection={'balance': 1})
    if not sender_balance or sender_balance.get('balance', 0) < amount:
        await update.message.reply_text("Insufficient balance to make the payment.")
        return

    # Check last payment time and cooldown
    last_payment_time = last_payment_times.get(sender_id)
    if last_payment_time:
        time_since_last_payment = datetime.now() - last_payment_time
        if time_since_last_payment < timedelta(minutes=10):
            cooldown_time = timedelta(minutes=10) - time_since_last_payment
            formatted_cooldown = format_timedelta(cooldown_time)
            await update.message.reply_text(f"Cooldown! You can pay again in {formatted_cooldown}.")
            return

   

    # Perform the payment
    await user_collection.update_one({'id': sender_id}, {'$inc': {'balance': -amount}})
    await user_collection.update_one({'id': recipient_id}, {'$inc': {'balance': amount}})

    # Update last payment time
    last_payment_times[sender_id] = datetime.now()

    # Fetch updated sender balance
    updated_sender_balance = await user_collection.find_one({'id': sender_id}, projection={'balance': 1})

    # Reply with payment success and updated balance
    await update.message.reply_text(
        f"Payment Successful! You Paid Ŧ{amount} Tokens to {update.message.reply_to_message.from_user.username}."
    )


async def roll(update, context):
    user_id = update.effective_user.id
    try:
        amount = int(context.args[0])
        choice = context.args[1].upper()  # Assuming the second argument is ODD or EVEN
    except (IndexError, ValueError):
        await update.message.reply_text("Invalid usage, please use /roll <amount> <ODD/EVEN>")
        return

    if amount < 0:
        await update.message.reply_text("Amount must be positive.")
        return

    user_data = await user_collection.find_one({'id': user_id})
    if not user_data:
        await update.message.reply_text("User data not found.")
        return

    balance_amount = user_data.get('balance', 0)
    if amount < balance_amount * 0.07:
        await update.message.reply_text("You can bet more than 7% of your balance.")
        return

    if balance_amount < amount:
        await update.message.reply_text("Insufficient balance to place the bet.")
        return

    # Send the dice emoji
    dice_message = await context.bot.send_dice(update.effective_chat.id, "ðŸŽ²")

    # Extract the dice value
    dice_value = dice_message.dice.value

    # Check if the dice roll is odd or even
    dice_result = "ODD" if dice_value % 2 != 0 else "EVEN"

    xp_change = 0  # Initialize XP change

    if choice == dice_result:
        # User wins, update balance and add XP
        xp_change = 50
        await user_collection.update_one(
            {'id': user_id},
            {'$inc': {'balance': amount, 'user_xp': xp_change}}
        )
        await update.message.reply_text(f"Dice roll: {dice_value}\nYou won! Your balance increased by {amount * 2}.")
    else:
        # User loses, deduct bet amount from balance and subtract XP
        xp_change = -1
        await user_collection.update_one(
            {'id': user_id},
            {'$inc': {'balance': -amount, 'user_xp': xp_change}}
        )
        await update.message.reply_text(f"Dice roll: {dice_value}\nYou lost! {amount} deducted from your balance.")

    # Notify user about XP change
    await update.message.reply_text(f"XP change: {xp_change}")



from html import escape

async def mtop(update: Update, context: CallbackContext):
    try:
        top_users = await user_collection.find({}, projection={'id': 1, 'first_name': 1, 'balance': 1}).sort('balance', -1).limit(10).to_list(10)
        top_users_message = "Top 10 Users With Highest Tokens\n\n"
        for i, user in enumerate(top_users, start=1):
            first_name = escape(user.get('first_name', 'Unknown'))
            user_id = user.get('id', 'Unknown')
            balance_amount = "{:,.0f}".format(user.get('balance', 0))
            top_users_message += f"{i}. <a href='tg://user?id={user_id}'>{first_name}</a>, Ŧ{balance_amount}\n"
        photo_url = 'https://graph.org/file/bd7e29f90404fee76e514.jpg'
        await update.message.reply_photo(photo=photo_url, caption=top_users_message, parse_mode='HTML')
    except Exception as e:
        await update.message.reply_text(f"An error occurred: {str(e)}")



async def daily_reward(update, context):
    user_id = update.effective_user.id

    # Check if the user already claimed the daily reward today
    user_data = await user_collection.find_one({'id': user_id}, projection={'last_daily_reward': 1, 'balance': 1})

    if user_data:
        last_claimed_date = user_data.get('last_daily_reward')

        if last_claimed_date and last_claimed_date.date() == datetime.utcnow().date():
            time_since_last_claim = datetime.utcnow() - last_claimed_date
            time_until_next_claim = timedelta(days=1) - time_since_last_claim
            formatted_time_until_next_claim = format_timedelta(time_until_next_claim)
            await update.message.reply_text(f"You already claimed your today's reward. Come back Tomorrow!\nTime Until Next Claim: `{formatted_time_until_next_claim}`.")
            return

    await user_collection.update_one(
        {'id': user_id},
        {'$inc': {'balance': 30000}, '$set': {'last_daily_reward': datetime.utcnow()}}
    )

    await update.message.reply_text("bro come back Congratulations! You claimed  Ŧ30.KTokens")


def format_timedelta(td: timedelta) -> str:
    seconds = td.total_seconds()
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return "{:02}h {:02}m {:02}s".format(int(hours), int(minutes), int(seconds))


from datetime import datetime, timedelta

import random
from datetime import datetime, timedelta

from telegram.ext import CommandHandler
from Grabber import application, user_collection
from telegram import Update


async def sbet(update, context):
    try:
        amount = int(context.args[0])
        choice = context.args[1].upper()  # Convert the choice to uppercase for consistency
        if amount <= 0:
            raise ValueError("Amount must be greater than zero.")
        if choice not in ['H', 'T']:
            raise ValueError("Invalid choice. Use 'H' for Head or 'T' for Tail.")
    except (IndexError, ValueError):
        await update.message.reply_text("Use /sbet <amount> <H or T>")
        return
    
    user_id = update.effective_user.id
    user_data = await user_collection.find_one({'id': user_id}, projection={'balance': 1, 'potion_amount': 1, 'potion_expiry': 1})

    if not user_data:
        await update.message.reply_text("User data not found.")
        return
    
    # Check if the user has any potions and if they are still valid
    potion_amount = user_data.get('potion_amount', 0)
    potion_expiry = user_data.get('potion_expiry')

    if potion_amount <= 0 or (potion_expiry and potion_expiry < datetime.now()):
        await update.message.reply_text("ʏᴏᴜ ᴅᴏɴᴛ ʜᴀᴠᴇ ᴀɴ ᴀɴʏ ᴘᴏᴛɪᴏɴ ғɪʀsᴛ ʙᴜʏ ᴀ ᴘᴏᴛɪᴏɴ ᴛᴏ ᴜsᴇ sʙᴇᴛ /buy_potion <quantity>.")
        return

    user_balance = user_data.get('balance', 0)
    if user_balance < amount:
        await update.message.reply_text("Insufficient balance to make the bet.")
        return

    # Coin landing randomly on head or tail
    coin_landing = random.choice(["H", "T"])
    
    if choice == coin_landing:
        won_amount = 2 * amount
        await user_collection.update_one({'id': user_id}, {'$inc': {'balance': won_amount}})
        message = f"You chose {'Head' if choice == 'H' else 'Tail'} and won `Ŧ{won_amount:,.0f}`.\nCoin landed on {coin_landing}."
    else:
        await user_collection.update_one({'id': user_id}, {'$inc': {'balance': -amount}})
        message = f"You chose {'Head' if choice == 'H' else 'Tail'} and lost `Ŧ{amount:,.0f}`.\nCoin landed on {coin_landing}."

    await update.message.reply_text(message)
    await update.message.reply_photo(
        photo='https://graph.org/file/67e87de8ab7ed5ce6d57f.jpg',
        caption="Here is the coin toss result."
    )


from telegram import Update
from telegram.ext import CommandHandler
import random
import asyncio
from Grabber import application, user_collection

# Dictionary to store user's items
user_data = {
    'Sword': 36,
    'Choco': 15,
    'exp': 10  # Initial exp set to 10
}

# List of monster names
monster_names = [
    "Goblin", "Orc", "Troll", "Dragon", "Skeleton", "Witch", "Vampire", "Werewolf",
    "Cyclops", "Minotaur", "Banshee", "Ghost", "Zombie", "Specter", "Manticore",
    "Hydra", "Siren", "Basilisk", "Chimera", "Kraken", "Phoenix", "Yeti", "Griffin",
    "Cerberus", "Harpy", "Wendigo", "Behemoth", "Cthulhu", "Medusa", "Gorgon",
    "Necromancer", "Warlock", "Lich", "Demon", "Djinn", "Fairy"
]

# Command handler for /sbag
async def sbag(update: Update, context):
    if user_data['exp'] >= 10:
        item_list_message = "Your Item List:\n"
        for item, quantity in user_data.items():
            item_list_message += f"ðŸ—¡ {item}: {quantity}\n"
        await update.message.reply_text(item_list_message)
    else:
        await update.message.reply_text("You don't have enough exp to see sbag.")

# Command handler for /shunt
async def shunt(update: Update, context):
    user_id = update.effective_user.id
    current_time = datetime.now()

    # Check if the user is on cooldown
    if user_id in last_shunt_time:
        time_since_last_shunt = current_time - last_shunt_time[user_id]
        cooldown_remaining = timedelta(seconds=30) - time_since_last_shunt
        if cooldown_remaining > timedelta(seconds=0):
            await update.message.reply_text(f"Please wait {cooldown_remaining.seconds} seconds before using shunt again.")
            return

# Command handler for /shunt
async def shunt(update: Update, context):
    user_id = update.effective_user.id
    current_time = datetime.now()

    # Check if the user is on cooldown
    if user_id in last_shunt_time:
        time_since_last_shunt = current_time - last_shunt_time[user_id]
        cooldown_remaining = timedelta(seconds=30) - time_since_last_shunt
        if cooldown_remaining > timedelta(seconds=0):
            await update.message.reply_text(f"Please wait {cooldown_remaining.seconds} seconds before using shunt again.")
            return
async def shunt(update: Update, context):
    monster_name = random.choice(monster_names)
    rank = random.choice(['F', 'E', 'D', 'C', 'B', 'A', 'S'])
    event = f"You found an [ {rank} ] Rank {monster_name} Dungeon."
    if 'F' in event:
        result_message = "You lostðŸ’€.\nAnd Goblin Fucked your BeastðŸ’€."
    else:
        won_tokens = random.randint(1000, 10000)
        user_data['exp'] += random.randint(10, 30)  # Adding random exp between 10 to 30
        result_message = f"You won the fight! You got these items:\n\nGold: {won_tokens}"
    await update.message.reply_text(
        f"Ë¹pick\n\n{event}\n\n{result_message}"
    )


async def xp(update, context):
    user_id = update.effective_user.id
    user_data = await user_collection.find_one({'id': user_id})

    if not user_data:
        await update.message.reply_text("User data not found.")
        return

    xp = user_data.get('user_xp', 0)

    # Check if XP is non-negative
    if xp < 0:
        await update.message.reply_text("Invalid XP value.")
        return

    # Calculate level based on XP
    level = math.floor(math.sqrt(xp / 100)) + 1

    if level > 100:
        level = 100

    ranks = {1: "E", 10: "D", 30: "C", 50: "B", 70: "A", 90: "S"}
    rank = next((rank for xp_limit, rank in ranks.items() if level <= xp_limit), None)

    message = f"Your current level is `{level}`\nand your rank is `{rank}`."

    await update.message.reply_text(message)

async def quiz(update, context):
    # Ask the quiz question
    await update.message.reply_text("Who is Naruto's shadow?")

async def check_answer(update, context):
    user_answer = update.message.text.lower()
    correct_answer = "developer"

    if user_answer == correct_answer:
        user_id = update.effective_user.id
        # Add a potion to the user's inventory
        await user_collection.update_one({'id': user_id}, {'$inc': {'potion_amount': 1}})
        await update.message.reply_text("Congratulations! You answered correctly and received a potion.")
    else:
        await update.message.reply_text("Sorry, that's not the correct answer.")



async def topxp(update, context):
    # Retrieve the top 10 users with the highest XP
    top_users = await user_collection.find({}, projection={'id': 1, 'first_name': 1, 'last_name': 1, 'user_xp': 1}).sort('user_xp', -1).limit(10).to_list(10)

    # Create a message with the top users
    top_users_message = "Top 10 Users With Highest XP\n\n"
    for i, user in enumerate(top_users, start=1):
        first_name = user.get('first_name', 'Unknown')
        last_name = user.get('last_name', '')
        user_id = user.get('id', 'Unknown')

        # Concatenate first_name and last_name if last_name is available
        full_name = f"{first_name} {last_name}" if last_name else first_name

        # Add user XP to the message
        xp_amount = user.get('user_xp', 0)
        top_users_message += f"{i}. <a href='tg://user?id={user_id}'>{full_name}</a>, XP: {xp_amount}\n"

    # Send the photo and include the top_users_message in the caption
    photo_path = 'https://graph.org/file/4b831c8ba1d609911e021.jpg'
    await update.message.reply_photo(photo=photo_path, caption=top_users_message, parse_mode='HTML')




import asyncio
from telegram.ext import CommandHandler
from Grabber import application, user_collection
from telegram import Update
import random
from datetime import datetime, timedelta

# Dictionary to store last propose times
last_propose_times = {}

async def propose(update, context):
    # Check if the user has 20000 tokens
    user_id = update.effective_user.id
    user_balance = await user_collection.find_one({'id': user_id}, projection={'balance': 1})

    if not user_balance or user_balance.get('balance', 0) < 20000:
        await update.message.reply_text("You need at least 20000 tokens to propose.")
        return

    # Check last propose time and cooldown
    last_propose_time = last_propose_times.get(user_id)
    if last_propose_time:
        time_since_last_propose = datetime.now() - last_propose_time
        if time_since_last_propose < timedelta(minutes=5):
            remaining_cooldown = timedelta(minutes=5) - time_since_last_propose
            remaining_cooldown_minutes = remaining_cooldown.total_seconds() // 60
            remaining_cooldown_seconds = remaining_cooldown.total_seconds() % 60
            await update.message.reply_text(f"Cooldown! Please wait {int(remaining_cooldown_minutes)}m {int(remaining_cooldown_seconds)}s before proposing again.")
            return

    # Deduct the propose fee of 10000 tokens
    await user_collection.update_one({'id': user_id}, {'$inc': {'balance': -10000}})

    # Send the proposal message with a photo path
    proposal_message = "ғɪɴᴀʟʟʏ ᴛʜᴇ ᴛɪᴍᴇ ᴛᴏ ᴘʀᴏᴘᴏsᴇ 🥰"
    photo_path = 'https://te.legra.ph/file/4d0f83726fe8cd637d3ff.jpg'  # Replace with your photo path
    await update.message.reply_photo(photo=photo_path, caption=proposal_message)
    
    await asyncio.sleep(2)  # 2-second delay

    # Send the proposal text
    await update.message.reply_text("ᴘʀᴏᴘᴏsɪɴɢ.....🥀")

    await asyncio.sleep(2)  # 2-second delay

    # Generate a random result (80% chance of rejection, 40% chance of acceptance)
    if random.random() < 0.6:
        rejection_message = "fuck she is rejected your married proposal and run away 😂"
        rejection_photo_path = 'https://graph.org/file/48c147582d2742105e6ec.jpg'  # Replace with rejection photo path
        await update.message.reply_photo(photo=rejection_photo_path, caption=rejection_message)
    else:
        await update.message.reply_text("Congratulations! She accepted you.🤩")

    # Update last propose time
    last_propose_times[user_id] = datetime.now()

async def buy_potion(update, context):
    try:
        amount = int(context.args[0])
        if amount <= 0:
            raise ValueError("Amount must be greater than zero.")
    except (IndexError, ValueError):
        await update.message.reply_text("Invalid amount. Please provide a positive integer.")
        return

    user_id = update.effective_user.id
    user_data = await user_collection.find_one({'id': user_id}, projection={'balance': 1, 'potion_amount': 1})

    if user_data:
        balance_amount = user_data.get('balance', 0)

        if amount * 99981681515 > balance_amount:
            await update.message.reply_text("Insufficient balance to buy this amount of potion.")
            return

        new_balance = balance_amount - amount * 9981681515

        # Update user balance and potion amount
        await user_collection.update_one({'id': user_id}, {'$set': {'balance': new_balance}, '$inc': {'potion_amount': amount}})

        await update.message.reply_text(f"You bought {amount} potion(s).")
    else:
        await update.message.reply_text("User data not found.")

# Function to display available potions in the shop
async def shop(update, context):
    shop_message = "Welcome to the Potion Shop!\n"
    shop_message += "Available Potions:\n"
    shop_message += "1. Naruto Potion - Ŧ99,816,815.15\n"
    shop_message += "This potion lasts for one day.\n"
    await update.message.reply_text(shop_message)



# Add the CommandHandler to the application
application.add_handler(CommandHandler("propose", propose, block=False))
application.add_handler(CommandHandler("xfight", shunt, block=False)) 

application.add_handler(CommandHandler("buy_potion", buy_potion, block=False))
application.add_handler(CommandHandler("shop", shop, block=False))
application.add_handler(CommandHandler("roll", roll, block=False))
application.add_handler(CommandHandler("topxp", topxp, block=False))
application.add_handler(CommandHandler("xp", xp))
application.add_handler(CommandHandler("sbet", sbet))
application.add_handler(CommandHandler("claim", daily_reward, block=False))
application.add_handler(CommandHandler("xbag", sbag, block=False)) 
application.add_handler(CommandHandler("bal", balance))
application.add_handler(CommandHandler("pay", mpay,))
application.add_handler(CommandHandler("tops", mtop, block=False))
application.add_handler(CommandHandler("loan", loan))
application.add_handler(CommandHandler("save", save))
application.add_handler(CommandHandler("repay", repay))
application.add_handler(CommandHandler("withdraw", withdraw))
application.add_handler(CommandHandler("quiz", quiz, block=False))
