import random
import json
import asyncio
from datetime import date

from telegram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# Load menu data from a JSON file (contains menu categories and items)
with open('list_menu.json', 'r', encoding='utf-8') as file:
    menu_data = json.load(file)

# Global counter used to determine which type of menu to generate
menu_counter = 0
# Cached daily menu for the current day to avoid regenerating it multiple times
daily_menu = None
# Stores the date when the menu was last generated
last_generated_date = None

# List of Telegram chat IDs subscribed to receive the daily menu broadcast
subscribers = [
    1095342///,
    1351121///
]


async def send_item(bot: Bot, chat_id: int, label: str, item: dict):
    """
    Sends a menu item as a photo with a caption to a specific Telegram chat.

    Parameters:
        bot (Bot): The Telegram Bot instance used for sending messages.
        chat_id (int): The recipient's chat ID.
        label (str): A label for the menu item (e.g., "🥖 Appetizer", "🍖 Main course").
        item (dict): A dictionary with the menu item details including:
                     - 'name': Name of the dish.
                     - 'info': Description or ingredients of the dish.
                     - 'calories': Calorie count of the dish.
                     - 'image': File path to the image representing the dish.

    Returns:
        None
    """
    # Construct the caption using the item details
    caption = (
        f"{label}: {item['name']}\n"
        f"Состав: {item['info']}\n"
        f"Калорийность: {item['calories']}"
    )
    # Open the image file in binary mode and send it as a photo with the caption
    with open(item['image'], 'rb') as photo:
        await bot.send_photo(chat_id=chat_id, photo=photo, caption=caption)


def create_daily_menu(menu_info: dict):
    """
    Creates a daily menu based on the provided menu information.
    The selection of items is determined by a global counter to introduce variety.

    Parameters:
        menu_info (dict): Dictionary containing lists of menu items for various categories,
                          e.g., "appetizers", "proteins", "fiber", "carbohydrates", "sauces".

    Returns:
        list: A list of tuples where each tuple consists of:
              - A string label for the menu item.
              - A dictionary with the menu item details.
    """
    global menu_counter
    menu_counter += 1

    # Every 21st iteration, select a random appetizer item as a cheat meal and reset the counter.
    if menu_counter % 21 == 0:
        appetizers_item = random.choice(menu_info["appetizers"])
        menu_counter = 0  # Reset the counter
        return [("🥪 Читмил", appetizers_item)]
    else:
        # For iterations not divisible by 21:
        # If the counter is not a multiple of 4, select a protein and a salad item.
        if menu_counter % 4 != 0:
            meat_item = random.choice(menu_info["proteins"])
            salad_item = random.choice(menu_info["fiber"])
            return [
                ("🍖 Мясное", meat_item),
                ("🥗 Салат", salad_item),
            ]
        else:
            # If the counter is a multiple of 4, select a carbohydrate (garnish) and a sauce.
            garnish_item = random.choice(menu_info["carbohydrates"])
            if garnish_item["name"] == "Борщ":
                # If the garnish is 'Борщ' (Borscht), then select 'Сметана' (Sour Cream) as the sauce.
                sauce_item = next(
                    (s for s in menu_info["sauces"] if s["name"] == "Сметана"),
                    None
                )
                if not sauce_item:
                    raise ValueError(
                        "Сметана не найдена в списке соусов!")  # "Sour Cream not found in the list of sauces!"
            else:
                sauce_item = random.choice(menu_info["sauces"])
            return [
                ("🥔 Гарнир", garnish_item),
                ("🍯 Соус", sauce_item),
            ]


def generate_daily_menu_if_needed(menu_info: dict):
    """
    Generates and returns the daily menu if it has
    not yet been generated for the current day.
    If the menu was already generated today, returns the cached menu.

    Parameters:
        menu_info (dict): Dictionary containing menu categories
        and their respective items.

    Returns:
        list: The daily menu as a list of tuples (label, menu item).
    """
    global daily_menu, last_generated_date
    today = date.today()

    # If today's menu exists, return it without regenerating.
    if last_generated_date == today and daily_menu is not None:
        return daily_menu

    # Generate a new daily menu and update the cache with today's date.
    daily_menu = create_daily_menu(menu_info)
    last_generated_date = today
    return daily_menu


async def broadcast_daily_menu(bot: Bot):
    """
    Retrieves today's daily menu and broadcasts it to
    all subscribed users via Telegram.

    Parameters:
        bot (Bot): The Telegram Bot instance used for sending messages.

    Returns:
        None
    """
    # Get the daily menu, generating it if necessary
    menu_for_today = generate_daily_menu_if_needed(menu_data)
    # Iterate over each subscriber and send all menu items
    for chat_id in subscribers:
        for label, item in menu_for_today:
            await send_item(bot, chat_id, label, item)


async def main():
    """
    Main entry point for the asynchronous execution
    of the Telegram bot.
    It initializes the bot, schedules the daily menu broadcast,
    and keeps the script running.

    The broadcast is scheduled to run daily at 10:00.
    """
    # Initialize the Telegram bot with the provided token
    bot = Bot(token='Your Token')

    # Create an asynchronous scheduler for periodic tasks
    scheduler = AsyncIOScheduler()
    # Schedule the broadcast_daily_menu function to run daily at 10:00
    scheduler.add_job(broadcast_daily_menu, 'cron', hour=10, minute=00, args=[bot])
    scheduler.start()

    # Keep the script running indefinitely
    while True:
        await asyncio.sleep(1)


if __name__ == '__main__':
    asyncio.run(main())
