import discord
import os
import json
import pygetwindow as gw
from PIL import Image
import time
import pyautogui
from ahk import AHK
import ctypes
import asyncio
import aiohttp
from io import BytesIO

# Initialize AHK for automation
ahk = AHK()

# Set up intents
intents = discord.Intents.default()
intents.message_content = True

bot_dir = os.path.join("C:", os.sep, "Steve's Silly Bot")
config_path = os.path.join(bot_dir, "config.json")

# Function to load or ask for the token
def load_token():
    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            config = json.load(f)
            if "token" in config:
                return config["token"]

    # Prompt for token if not found in config.json
    token = input("Please enter your Discord bot token: ")
    config = {"token": token}
    save_config(config)  # Save config with token initially
    return token

# Function to save config to config.json
def save_config(updated_data):
    # Load existing config if it exists
    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            config = json.load(f)
    else:
        config = {}

    # Update the config with new data
    config.update(updated_data)

    # Save the merged config back to the file
    with open(config_path, "w") as f:
        json.dump(config, f, indent=4)

# Function to get the screen resolution using ctypes
def get_screen_resolution():
    user32 = ctypes.windll.user32
    screen_width = user32.GetSystemMetrics(0)  # Get screen width
    screen_height = user32.GetSystemMetrics(1)  # Get screen height
    return screen_width, screen_height

# Function to adjust coordinates based on screen resolution
def adjust_coordinates(x, y, screen_width, screen_height):
    adjusted_x = int(x * screen_width / 1920)  # Assuming 1920x1080 is the base resolution
    adjusted_y = int(y * screen_height / 1080)
    return adjusted_x, adjusted_y

# Function to calculate accurate positions multiple times
def calculate_accurate_positions(base_positions, screen_width, screen_height, iterations=10):
    results = {key: [] for key in base_positions.keys()}
    
    for _ in range(iterations):
        for key, (x, y) in base_positions.items():
            adjusted_x, adjusted_y = adjust_coordinates(x, y, screen_width, screen_height)
            results[key].append((adjusted_x, adjusted_y))
    
    # Average the calculated positions for accuracy
    averaged_positions = {
        key: (
            sum(pos[0] for pos in positions) // len(positions),  # Average x
            sum(pos[1] for pos in positions) // len(positions)   # Average y
        )
        for key, positions in results.items()
    }
    return averaged_positions

# Function to update positions dynamically based on resolution
def update_positions_on_startup():
    screen_width, screen_height = get_screen_resolution()

    # Default positions for 1920x1080 resolution
    default_positions = {
        "inventory": (45, 540),
        "inventory_2": (1242, 339),
        "storage": (38, 401),
        "daily_quest_first": (55, 596),
        "daily_quest_second": (1236, 337),
        "screenshot_position": (884, 166),
        "aura_first": (56, 415),
        "aura_second": (879, 365),
        "aura_third": (825, 436),
        "aura_fourth": (673, 635),
        "statistics_start": (8, 842),
        "statistics_end": (226, 1071),
        "buy_storage_first": (38, 401),
        "buy_storage_second": (632, 771),
        "buy_storage_screenshot_start": (489, 742),
        "buy_storage_screenshot_end": (759, 787),
        "inventory_3" : (992,371),
        "inventory_4" : (859,424),
        "inventory_5" : (653,576),
        "inventorygear_1" : (942,336),
        "inventorygear_2" : (987,376),
        "inventorylgear_3" : (698,497),
        "inventorylgear_4" : (854,434),
        "inventorylgear_5" : (706,488),
        "inventoryrgear_3" : (539,493),
        'inventoryrgear_5' : (706,488)
    }

    # Calculate accurate positions multiple times for precision
    adjusted_positions = calculate_accurate_positions(default_positions, screen_width, screen_height)

    # Add adjusted regions for screenshots
    adjusted_positions["statistics_region"] = (
        adjusted_positions["statistics_start"][0],
        adjusted_positions["statistics_start"][1],
        adjusted_positions["statistics_end"][0] - adjusted_positions["statistics_start"][0],
        adjusted_positions["statistics_end"][1] - adjusted_positions["statistics_start"][1]
    )

    adjusted_positions["buy_storage_region"] = (
        adjusted_positions["buy_storage_screenshot_start"][0],
        adjusted_positions["buy_storage_screenshot_start"][1],
        adjusted_positions["buy_storage_screenshot_end"][0] - adjusted_positions["buy_storage_screenshot_start"][0],
        adjusted_positions["buy_storage_screenshot_end"][1] - adjusted_positions["buy_storage_screenshot_start"][1]
    )

    # Save these adjusted positions to config.json
    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            config = json.load(f)
    else:
        config = {}

    config["coordinates"] = adjusted_positions
    save_config(config)

    return adjusted_positions

# Load or initialize coordinates based on screen resolution
def load_or_initialize_coordinates():
    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            config = json.load(f)
            if "coordinates" in config:
                return config["coordinates"]

    # Update positions on startup if not already available
    return update_positions_on_startup()

# Function to check if Roblox is running
def is_roblox_open():
    windows = gw.getWindowsWithTitle("Roblox")
    for window in windows:
        if "Roblox" in window.title:
            return window
    return None

# Function to take a screenshot
def take_screenshot(filename, region=None):
    roblox_window = is_roblox_open()
    if not roblox_window:
        return None  # Return None if Roblox is not open

    # Ensure Roblox is in windowed mode and bring it to focus
    roblox_window.activate()
    time.sleep(0.5)

    if region:
        screenshot = pyautogui.screenshot(region=region)
    else:
        screenshot = pyautogui.screenshot()
    screenshot.save(filename)
    return filename

# Function to press the first button again to close it
def close_button():
    button_coords = load_or_initialize_coordinates()  # Load coordinates
    ahk.mouse_move(*button_coords["inventory"], speed=10)
    ahk.click()
    time.sleep(1)

# Initialize coordinates at startup
coordinates = update_positions_on_startup()

# Create bot instance
bot = discord.Bot(intents=intents)

# Screenshot Command
@bot.slash_command(name="screenshot", description="Take a screenshot of inventory, storage, or daily quest.")
async def screenshot(ctx: discord.ApplicationContext, option: str):
    await ctx.defer()  # Defer interaction

    valid_options = ["inventory", "storage", "daily_quest"]
    if option.lower() not in valid_options:
        await ctx.respond(f"Invalid option. Please choose one of the following: {', '.join(valid_options)}")
        return

    button_coords = load_or_initialize_coordinates()

    if option.lower() == "inventory":
        ahk.mouse_move(*button_coords["inventory"], speed=10)
        ahk.click()
        ahk.mouse_move(*button_coords["inventory_2"], speed=10)
        ahk.click()
        time.sleep(1)
        filename = take_screenshot("inventory_screenshot.png")
    elif option.lower() == "storage":
        ahk.mouse_move(*button_coords["storage"], speed=10)
        ahk.click()
        time.sleep(1)
        filename = take_screenshot("storage_screenshot.png")
    elif option.lower() == "daily_quest":
        ahk.mouse_move(*button_coords["daily_quest_first"], speed=10)
        ahk.click()
        time.sleep(1)
        ahk.mouse_move(*button_coords["daily_quest_second"], speed=10)
        ahk.click()
        time.sleep(1)
        filename = take_screenshot("daily_quest_screenshot.png")

    if filename is None:
        await ctx.respond("Roblox is not open or not in focus. Please open Roblox in windowed mode.")
        return

    close_button()  # Close the first button again
    await ctx.respond(file=discord.File(filename), content=f"Screenshot successfully taken")
    os.remove(filename)  # Clean up

# Equip Aura Command
@bot.slash_command(name="equip_aura", description="Equip an aura by name.")
async def equip_aura(ctx: discord.ApplicationContext, aura_name: str):
    await ctx.defer()

    button_coords = load_or_initialize_coordinates()
    ahk.mouse_move(*button_coords["aura_first"], speed=10)
    ahk.click()
    time.sleep(1)
    ahk.mouse_move(*button_coords["aura_second"], speed=10)
    ahk.click()
    time.sleep(1)
    pyautogui.write(aura_name)
    time.sleep(1)
    ahk.mouse_move(*button_coords["aura_third"], speed=10)
    ahk.click()
    time.sleep(1)
    ahk.mouse_move(*button_coords["aura_fourth"], speed=10)
    ahk.click()
    time.sleep(1)
    ahk.mouse_move(*button_coords["inventory"], speed=10)
    ahk.click()
    await ctx.respond(f"Aura '{aura_name}' has been equipped.")

@bot.slash_command(name="useitem", description="Use Potions Items Etc")
async def use(ctx: discord.ApplicationContext, item_name: str):
    await ctx.defer()
    try:  # Missing try block
        if any(char.isdigit() for char in item_name):
            await ctx.respond("Item name must not contain digits. Please try again.", ephemeral=True)
            return
        
        button_coords = load_or_initialize_coordinates()
        ahk.mouse_move(*button_coords["inventory"], speed=10)  # Removed extra space in key name
        ahk.click()
        time.sleep(1)
        ahk.mouse_move(*button_coords['inventory_2'], speed=10)
        ahk.click()
        time.sleep(1)
        ahk.mouse_move(*button_coords['inventory_3'], speed=10)
        ahk.click()
        time.sleep(1)
        pyautogui.write(item_name)
        time.sleep(1)
        ahk.mouse_move(*button_coords['inventory_4'], speed=10)
        ahk.click()
        time.sleep(1)
        ahk.mouse_move(*button_coords['inventory_5'], speed=10)
        ahk.click()
        time.sleep(1)
        ahk.mouse_move(*button_coords['inventory'], speed=10)
        # Send success response
        await ctx.respond(f"Item '{item_name}' has been used.")
    except KeyError as e:
        # Handle missing keys in button_coords
        await ctx.respond(f"Error: Missing button coordinate {str(e)} in configuration.", ephemeral=True)
    except Exception as e:
        # Handle any other unexpected errors
        await ctx.respond(f"An error occurred: please contact the discord members for assistance. {e}", ephemeral=True)


# equip left gear command below. 
@bot.slash_command(name="equipleftgear", description="Equip gear to the left gear slots.")
async def equipleftgear(ctx: discord.ApplicationContext, gear_name: str):
    """Command to equip gear to the left gear slots."""
    await ctx.defer()
    try:
        # load coords
        button_coords = load_or_initialize_coordinates()

        # Validate gear_name checking if there is digits or not
        if not gear_name.strip():
            await ctx.respond("Please provide a valid gear name.", ephemeral=True)
            return

        # Sequence of actions
       
        ahk.mouse_move(*button_coords["inventory"], speed=10)
        ahk.click()
        time.sleep(1)

       
        ahk.mouse_move(*button_coords["inventorygear_1"], speed=10)
        ahk.click()
        time.sleep(1)

       
        ahk.mouse_move(*button_coords["inventorygear_2"], speed=10)
        ahk.click()
        time.sleep(1)

       
        pyautogui.write(gear_name.strip())
        time.sleep(1)

        
        ahk.mouse_move(*button_coords["inventorylgear_3"], speed=10)
        ahk.click()
        time.sleep(1)

        
        ahk.mouse_move(*button_coords["inventorylgear_4"], speed=10)
        ahk.click()
        time.sleep(1)

        
        ahk.mouse_move(*button_coords["inventorylgear_5"], speed=10)
        ahk.click()
        time.sleep(1)

       
        ahk.mouse_move(*button_coords["inventory"], speed=10)
        ahk.click()

        # Send success response
        await ctx.respond(f"Successfully equipped '{gear_name}' to the left gear slots.")
    except KeyError as e:
        # Handle missing keys in button_coords
        await ctx.respond(f"Error: Missing button coordinate {str(e)} in configuration.", ephemeral=True)
    except Exception as e:
        # Handle any other unexpected errors
        await ctx.respond(f"An error occurred: {e}", ephemeral=True)

# Statistics command below

@bot.slash_command(name="statistics", description="Take a screenshot of the statistics region.")
async def statistics(ctx: discord.ApplicationContext):
    """Slash command to capture and send a screenshot using statistics_start and statistics_end."""
    await ctx.defer()  

    try:
        # Load or initialize coordinates
        coordinates = load_or_initialize_coordinates()

        # Extract statistics_start and statistics_end
        if "statistics_start" not in coordinates or "statistics_end" not in coordinates:
            raise ValueError("Statistics start or end coordinates not found in configuration.")

        x1, y1 = coordinates["statistics_start"]
        x2, y2 = coordinates["statistics_end"]

        # Calculate region 
        region = (x1, y1, x2 - x1, y2 - y1)

        # Take a screenshot of the specified region
        screenshot = pyautogui.screenshot(region=region)

        # Save the screenshot to a BytesIO object
        img_buffer = BytesIO()
        screenshot.save(img_buffer, format="PNG")
        img_buffer.seek(0)

        # Send the screenshot back to the user
        file = discord.File(fp=img_buffer, filename="statistics.png")
        await ctx.respond("Here is the statistics screenshot:", file=file)
    except Exception as e:
         
        await ctx.respond(f"An error occurred: {e}", ephemeral=True)

# Buy Storage Command
@bot.slash_command(name="buy_storage", description="Buy more storage and capture screenshots before and after.")
async def buy_storage(ctx: discord.ApplicationContext):
    await ctx.defer()  # Defer interaction

    button_coords = load_or_initialize_coordinates()

    # Move to the first position and click
    ahk.mouse_move(*button_coords["buy_storage_first"], speed=10)
    ahk.click()
    time.sleep(1)

    # Take screenshot before the second click
    before_filename = take_screenshot("before_buy_storage.png", region=button_coords["buy_storage_region"])
    if before_filename is None:
        await ctx.respond("Roblox is not open or not in focus. Please open Roblox in windowed mode.")
        return

    # Move to the second position and click
    ahk.mouse_move(*button_coords["buy_storage_second"], speed=10)
    ahk.click()
    time.sleep(1)

    # Take screenshot after the second click
    after_filename = take_screenshot("after_buy_storage.png", region=button_coords["buy_storage_region"])
    if after_filename is None:
        await ctx.respond("Roblox is not open or not in focus. Please open Roblox in windowed mode.")
        return

    await ctx.respond(
        files=[discord.File(before_filename, filename="Before_Buying.png"), 
               discord.File(after_filename, filename="After_Buying.png")],
        content="**Before Purchasing**\n**After Purchasing**"
    )
    # Clean up files
    os.remove(before_filename)
    os.remove(after_filename)

# Bot ready event
@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}!')


@bot.event
async def on_disconnect():
    print("Bot disconnected. Attempting to reconnect...")


async def reconnect_bot():
    token = load_token()
    for attempt in range(5):  # Retry up to 5 times
        try:
            await bot.login(token)
            await bot.connect()
            return  # Exit if successfully connected
        except discord.errors.LoginFailure:
            print("Error: Improper token has been passed. Please provide a valid token.")
            token = input("Please enter your Discord bot token: ")

            # Save only the new token to the config file
            save_config({"token": token})
        except Exception as e:
            print(f"Error: {e}. Retrying in {2**attempt} seconds...")
            await asyncio.sleep(2**attempt)

    print("Failed to reconnect after multiple attempts. Exiting...")
    await bot.close()

# Run the bot
if __name__ == "__main__":
    try:
        asyncio.run(reconnect_bot())
    except KeyboardInterrupt:
        print("Shutting down...")
    finally:
        asyncio.run(bot.close())

