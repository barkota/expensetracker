# bot.py
import os
import re
import logging
from datetime import datetime
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes,
)

import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pytesseract
from PIL import Image

# --- Configuration and Setup ---
load_dotenv() # Load environment variables from .env file

<<<<<<< HEAD
=======
# Set Tesseract path. Note the corrected path separator.
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

>>>>>>> c5204e0e08e9a29dfb87b63bfbefc052334e801e
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GOOGLE_SHEET_NAME = os.getenv("GOOGLE_SHEET_NAME")

# Set up logging to see errors
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- Google Sheets Integration ---
def get_google_sheet():
    """Connects to Google Sheets and returns the worksheet."""
    scope = ["https://spreadsheets.google.com/feeds", 'https://www.googleapis.com/auth/spreadsheets',
             "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
    client = gspread.authorize(creds)
    sheet = client.open(GOOGLE_SHEET_NAME).sheet1
    return sheet

# --- OCR and Parsing Logic ---
def process_image_with_ocr(image_path):
    """Uses Tesseract to extract text from an image."""
    try:
        return pytesseract.image_to_string(Image.open(image_path))
    except Exception as e:
        logger.error(f"OCR Error: {e}")
        return None

# In your bot.py file, replace your parse_expense_data function with this one.

def parse_expense_data(text):
    """
    Parses text to find the transaction amount, source, and date.
    """
    amount = None
    source = "Unknown"
    transaction_date = None

    # Pattern for CBE date format (e.g., 05-Sep-2025)
    cbe_date_match = re.search(r'(\d{2}-[a-zA-Z]{3}-\d{4})', text)
    if cbe_date_match:
        date_str = cbe_date_match.group(1)
        try:
            transaction_date = datetime.strptime(date_str, "%d-%b-%Y")
        except ValueError:
            logger.error(f"Could not parse CBE date: {date_str}")
    
    # Pattern for Telebirr date format (e.g., 2025/08/07)
    telebirr_date_match = re.search(r'(\d{4}/\d{2}/\d{2})', text)
    if telebirr_date_match:
        date_str = telebirr_date_match.group(1)
        try:
            transaction_date = datetime.strptime(date_str, "%Y/%m/%d")
        except ValueError:
            logger.error(f"Could not parse Telebirr date: {date_str}")

    # --- Amount and source parsing logic ---
    cbe_amount_match = re.search(r'ETB\s*([\d,]+\.\d{2})', text, re.IGNORECASE)
    telebirr_amount_match = re.search(r'(\S?\s*[\d,]+\.\d{2})\s*\(ETB\)', text, re.IGNORECASE)

    if cbe_amount_match:
        amount_str = cbe_amount_match.group(1).replace(',', '')
        source = "CBE"
        amount = float(amount_str)
    elif telebirr_amount_match:
        amount_str = telebirr_amount_match.group(1).replace(' ', '').replace(',', '').replace('—', '-')
        source = "Telebirr"
        try:
            amount = float(amount_str)
        except ValueError:
            return None # Fail gracefully if amount is invalid
    
    if amount is None:
        return None # Return None if no amount is found

    return {"amount": amount, "source": source, "date": transaction_date}


# --- Telegram Bot Handlers ---
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for the /start command."""
    await update.message.reply_text("Hello! Send me a screenshot of your transaction, and I'll log it for you.")

# In your bot.py file, replace the existing handle_image function with this one.

# In your bot.py file, replace your handle_image function with this one.

async def handle_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handler for when an image is received.
    """
    message = update.message
    if not message.photo:
        await message.reply_text("Please send an image file.")
        return

    await message.reply_text("Processing your screenshot... ⏳")

    try:
        photo_file = await message.photo[-1].get_file()
        file_path = f"{photo_file.file_id}.jpg"
        await photo_file.download_to_drive(file_path)

        extracted_text = process_image_with_ocr(file_path)
        logger.info(f"OCR Extracted Text:\n---\n{extracted_text}\n---")
        
        if not extracted_text:
            await message.reply_text("❌ Error: Could not read any text from the image. Is it clear?")
            return

        expense_data = parse_expense_data(extracted_text)
        
        if expense_data:
            # Store the extracted data in the user's context
            context.user_data['pending_expense'] = {
                'amount': expense_data['amount'],
                'source': expense_data['source'],
                'date': expense_data['date']
            }
            
            # If no date was found in the image, ask the user to input it
            if not expense_data['date']:
                keyboard = [
                    [InlineKeyboardButton("Today", callback_data="date_today")],
                    [InlineKeyboardButton("Enter Manually", callback_data="date_manual")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await message.reply_text("I couldn't find a date in the screenshot. Is this expense for today?", reply_markup=reply_markup)
            else:
                # If a date was found, proceed to ask for category
                categories = ["Food", "Transport", "Shopping", "Entertainment", "Bills", "Other"]
                keyboard = [[InlineKeyboardButton(cat, callback_data=f"category_{cat}")] for cat in categories]
                reply_markup = InlineKeyboardMarkup(keyboard)

                await message.reply_text(
                    f"I found an amount of {expense_data['amount']:.2f} ETB. Please select a category:",
                    reply_markup=reply_markup
                )
        else:
            await message.reply_text("❌ Error: Couldn't find a valid amount in the screenshot. Please try again.")
            logger.info(f"Failed to parse text:\n---\n{extracted_text}\n---")

    except Exception as e:
        logger.error(f"An error occurred in handle_image: {e}")
        await message.reply_text("Sorry, a critical error occurred. Please try again later.")
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)
            

# In your bot.py file, add this new handler.

async def handle_date_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the user's date selection (Today or Manually)."""
    query = update.callback_query
    await query.answer()
    
    selected_option = query.data
    
    if selected_option == "date_today":
        context.user_data['pending_expense']['date'] = datetime.now()
        
        # Proceed to category selection
        categories = ["Food", "Transport", "Shopping", "Entertainment", "Bills", "Other"]
        keyboard = [[InlineKeyboardButton(cat, callback_data=f"category_{cat}")] for cat in categories]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            "Expense date set to today. Now, please select a category:",
            reply_markup=reply_markup
        )
    
    elif selected_option == "date_manual":
        # Set a state to await the user's date input
        context.user_data['state'] = 'awaiting_manual_date'
        await query.edit_message_text("Please reply with the date in YYYY-MM-DD format (e.g., 2025-09-07).")


async def category_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the user's category selection."""
    query = update.callback_query
    await query.answer()

    selected_category = query.data.replace("category_", "")
    
    # Store the selected category in the user's context
    context.user_data['pending_expense']['category'] = selected_category
    
    await query.edit_message_text(
        f"You selected '{selected_category}'. Now, please reply with a short description for this expense."
    )


# In your bot.py file, add this new handler.

async def handle_text_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """A single handler for all text input (date and description)."""
    user_state = context.user_data.get('state')
    user_text = update.message.text
    
    if user_state == 'awaiting_manual_date':
        try:
            parsed_date = datetime.strptime(user_text, "%Y-%m-%d")
            context.user_data['pending_expense']['date'] = parsed_date
            
            # Clear state and proceed to category selection
            context.user_data.pop('state', None)
            
            categories = ["Food", "Transport", "Shopping", "Entertainment", "Bills", "Other"]
            keyboard = [[InlineKeyboardButton(cat, callback_data=f"category_{cat}")] for cat in categories]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                "Thank you! Now please select a category:",
                reply_markup=reply_markup
            )
            
        except ValueError:
            await update.message.reply_text("❌ Invalid date format. Please enter the date in YYYY-MM-DD format (e.g., 2025-09-07).")
    
    elif 'pending_expense' in context.user_data and 'category' in context.user_data['pending_expense']:
        # This part handles the description input
        description = user_text
        expense_data = context.user_data['pending_expense']
        expense_data['description'] = description

        try:
            sheet = get_google_sheet()
            
            # Format the date without time for Google Sheets
            date_for_sheet = expense_data['date'].strftime("%Y-%m-%d")

            row = [
                date_for_sheet,
                expense_data['amount'],
                expense_data['category'],
                expense_data['description'],
                expense_data['source']
            ]
            sheet.append_row(row)

            await update.message.reply_text(
                f"✅ Success! Logged new expense:\n\n"
                f"📅 **Date:** {date_for_sheet}\n"
                f"💰 **Amount:** {expense_data['amount']:.2f} ETB\n"
                f"🏷️ **Category:** {expense_data['category']}\n"
                f"📝 **Description:** {expense_data['description']}\n"
                f"🏦 **Source:** {expense_data['source']}",
                parse_mode='Markdown'
            )
        except Exception as e:
            logger.error(f"An error occurred while logging to Google Sheets: {e}")
            await update.message.reply_text("Sorry, a critical error occurred while logging. Please try again.")

        context.user_data.clear()
    
    else:
        # Fallback for unexpected text input
        await update.message.reply_text("I'm not sure what to do with that. Please send a screenshot of a transaction.")


# In your bot.py file, replace your existing handle_description_input with this one.

async def handle_text_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """A single handler for all text input (date and description)."""
    user_state = context.user_data.get('state')
    user_text = update.message.text
    
    if user_state == 'awaiting_manual_date':
        try:
            parsed_date = datetime.strptime(user_text, "%Y-%m-%d")
            context.user_data['pending_expense']['date'] = parsed_date
            
            # Clear state and proceed to category selection
            context.user_data.pop('state', None)
            
            categories = ["Food", "Transport", "Shopping", "Entertainment", "Bills", "Other"]
            keyboard = [[InlineKeyboardButton(cat, callback_data=f"category_{cat}")] for cat in categories]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                "Thank you! Now please select a category:",
                reply_markup=reply_markup
            )
            
        except ValueError:
            await update.message.reply_text("❌ Invalid date format. Please enter the date in YYYY-MM-DD format (e.g., 2025-09-07).")
    
    elif 'pending_expense' in context.user_data and 'category' in context.user_data['pending_expense']:
        # This part handles the description input
        description = user_text
        expense_data = context.user_data['pending_expense']
        expense_data['description'] = description

        try:
            sheet = get_google_sheet()
            
            # Format the date without time for Google Sheets
            date_for_sheet = expense_data['date'].strftime("%Y-%m-%d")

            row = [
                date_for_sheet,
                expense_data['amount'],
                expense_data['category'],
                expense_data['description'],
                expense_data['source']
            ]
            sheet.append_row(row)

            await update.message.reply_text(
                f"✅ Success! Logged new expense:\n\n"
                f"📅 **Date:** {date_for_sheet}\n"
                f"💰 **Amount:** {expense_data['amount']:.2f} ETB\n"
                f"🏷️ **Category:** {expense_data['category']}\n"
                f"📝 **Description:** {expense_data['description']}\n"
                f"🏦 **Source:** {expense_data['source']}",
                parse_mode='Markdown'
            )
        except Exception as e:
            logger.error(f"An error occurred while logging to Google Sheets: {e}")
            await update.message.reply_text("Sorry, a critical error occurred while logging. Please try again.")

        context.user_data.clear()
    
    else:
        # Fallback for unexpected text input
        await update.message.reply_text("I'm not sure what to do with that. Please send a screenshot of a transaction.")

# In your bot.py file, replace the existing main function with this one.

# In your bot.py file, replace your main function with this one.

def main():
    """Starts the Telegram bot."""
    logger.info("Starting bot...")
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    # Register handlers
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(MessageHandler(filters.PHOTO, handle_image))
    # New handler for date-related buttons
    app.add_handler(CallbackQueryHandler(handle_date_callback, pattern="^date_"))
    # The category handler remains the same
    app.add_handler(CallbackQueryHandler(category_callback_handler, pattern="^category_"))
    # A single handler for all text inputs
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_input))

    logger.info("Bot is polling...")
    app.run_polling()

if __name__ == "__main__":
    main()