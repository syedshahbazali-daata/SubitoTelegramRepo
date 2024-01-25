import telebot  # pip install pyTelegramBotAPI pandas requests-html xextract
import pandas as pd  # pip install pandas
import csv
import time
import threading
from requests_html import HTMLSession  # pip install requests-html
from xextract import String  # pip install xextract
import json


def get_file_data(file_name):
    with open(file_name, "r", encoding="utf-8") as txt_file:
        data_file = txt_file.read().strip().split("\n")
    return data_file


with open("bot-configuration.json", "r") as file:
    data = json.load(file)
token = data["token"]

bot = telebot.TeleBot(token, parse_mode='HTML')

# markup contains 3 menu buttons (user, admin, help)
markup = telebot.types.InlineKeyboardMarkup()
markup.row_width = 2
markup.add(telebot.types.InlineKeyboardButton("User", callback_data="user"),
           telebot.types.InlineKeyboardButton("Admin", callback_data="admin"),
           telebot.types.InlineKeyboardButton("Help", callback_data="help"))

user_menu_markup = telebot.types.InlineKeyboardMarkup()
user_menu_markup.row_width = 2
user_menu_markup.add(telebot.types.InlineKeyboardButton("Track a Listing", callback_data="tracker_callback"),
                     telebot.types.InlineKeyboardButton("Your Tacking Listing", callback_data="your_listing_callback"),
                     )


# on clicking the menu buttons, the callback_data is sent to the bot

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    if call.data == "user":
        # reply to the user with send_welcome function
        send_welcome_user(call.message)

    elif call.data == "tracker_callback":
        tracker_callback(call.message)

    elif call.data == "your_listing_callback":
        your_tracking_listing(call.message)

    elif call.data == "delete_tracker":
        df = pd.read_csv("data.csv")

        # get the chat_id of the user
        chat_id = call.message.chat.id
        # update row where chat_id = chat_id and make keyword, category, location to empty
        df.loc[df['chat_id'] == chat_id, 'keyword'] = "NA"
        df.loc[df['chat_id'] == chat_id, 'url'] = "NA"
        df.loc[df['chat_id'] == chat_id, 'location'] = "NA"
        df.to_csv("data.csv", index=False)

        bot.send_message(call.message.chat.id, "Tracker Deleted")


    elif call.data == "admin":
        admin_panel(call.message)
    elif call.data == "help":

        instructions = """<b>Instructions:</b>\nIf you are a user, you can track a listing in a specific category and location. You will receive a notification when a new listing is found.\n\nIf you are an admin, you can add/delete users and see the list of users."""
        bot.send_message(call.message.chat.id, instructions)

    elif call.data == "add_user":
        add_user_callback(call.message)
    elif call.data == "delete_user":
        delete_user_callback(call.message)
    elif call.data == "users_list":
        users_list_callback(call.message)


@bot.message_handler(commands=['start'])
def send_welcome(message):
    # reply to the user with the markup
    bot.reply_to(message, r"Howdy, Welcome to Subito.it Bot", reply_markup=markup)


# User Panel


def send_welcome_user(message):
    df = pd.read_csv("data.csv")
    chat_ids = df.values.tolist()
    chat_ids = [str(i[0]) for i in chat_ids]
    print(chat_ids)

    if str(message.chat.id) in chat_ids:
        bot.send_message(message.chat.id, "Welcome back\nChoose an option", reply_markup=user_menu_markup)
        return

    bot.send_message(message.chat.id, "Insert your email")
    bot.register_next_step_handler(message, login)


def login(message):
    df = pd.read_csv("data.csv")

    # convert all emails to lowercase
    df["email"] = df["email"].str.lower()

    enter_email = str(message.text).lower().strip()
    users = df.values.tolist()
    users = [str(i[1]).lower() for i in users]
    print(users, message.text)

    if enter_email not in users:
        bot.reply_to(message, "User not found, Contact Admin to register")
        return



    df.loc[df['email'] == enter_email, 'chat_id'] = str(message.chat.id)
    print(df)
    df.to_csv("data.csv", index=False)



    bot.send_message(message.chat.id, f"Welcome {enter_email}\nChoose an option", reply_markup=user_menu_markup)


def tracker_callback(message):
    bot.send_message(message.chat.id, "Please insert the Vehicle Keyword: ")

    bot.register_next_step_handler(message, track_vehicle_1)


def track_vehicle_1(message):
    bot.send_message(message.chat.id, "Please insert the Vehicle Location: ")

    df = pd.read_csv("data.csv")
    # update row where chat_id = chat_id and make keyword, category, location to empty
    df.loc[df['chat_id'] == message.chat.id, 'keyword'] = message.text
    df.to_csv("data.csv", index=False)
    print(df)

    bot.register_next_step_handler(message, track_vehicle_2)


def track_vehicle_2(message):
    bot.send_message(message.chat.id, "Please insert the Url: ")
    df = pd.read_csv("data.csv")
    # update row where chat_id = chat_id and make keyword, category, location to empty
    df.loc[df['chat_id'] == message.chat.id, 'location'] = message.text
    df.to_csv("data.csv", index=False)
    print(df)


    bot.register_next_step_handler(message, track_vehicle_3)


def track_vehicle_3(message):
    df = pd.read_csv("data.csv")
    # update row where chat_id = chat_id and make keyword, category, location to empty
    df.loc[df['chat_id'] == message.chat.id, 'url'] = message.text
    df.to_csv("data.csv", index=False)
    bot.send_message(message.chat.id, "Tracker Added Successfully")
    print(df)


def your_tracking_listing(message):
    df = pd.read_csv("data.csv")

    # get the chat_id of the user
    chat_id = message.chat.id
    # get the keyword of the user
    user_selected_keyword = df[df["chat_id"] == chat_id]["keyword"].values[0]
    user_selected_url = df[df["chat_id"] == chat_id]["url"].values[0]
    user_selected_location = df[df["chat_id"] == chat_id]["location"].values[0]

    old_selected_data = f"""<b>Keyword:</b> {user_selected_keyword}\n<b>Url:</b> {user_selected_url}\n<b>Location:</b> {user_selected_location}"""

    # delete button
    delete_button = telebot.types.InlineKeyboardMarkup()
    delete_button.row_width = 1
    delete_button.add(telebot.types.InlineKeyboardButton("Delete tracker", callback_data="delete_tracker"))
    bot.send_message(message.chat.id, f"{old_selected_data}\n\n", reply_markup=delete_button)


def scraper():
    while True:


        print("Checking for new vehicles")
        df = pd.read_csv("data.csv")
        already_done = get_file_data("already-done.txt")
        for index, single_row in df.iterrows():
            if "www.subito.it" not in str(single_row["url"]):  # skip if url is not subito.it
                continue
            bot.send_message(single_row["chat_id"], "Checking for new vehicles")
            session = HTMLSession()
            res = session.get(single_row["url"])
            page_source = str(res.text)

            vehicle_names = String(xpath='//div/a//h2').parse_html(page_source)
            vehicle_links = String(xpath='//div/a//h2/../../../../..', attr='href').parse_html(page_source)

            for vehicle_name, vehicle_link in zip(vehicle_names, vehicle_links):
                record = f"{vehicle_link}:{single_row['chat_id']}"
                if record in already_done:
                    continue


                bot.send_message(single_row["chat_id"],
                                 f"Vehicle found: {vehicle_name} at {single_row['location']}")

                with open("already-done.txt", "a", encoding="utf-8") as txt_file:
                    txt_file.write(record + "\n")





        time.sleep(60*60)


# Admin Panel
# Admin Panel
ADMIN_LOGGED = False


def logout_session():
    print("logout session")
    global ADMIN_LOGGED
    if ADMIN_LOGGED:
        time.sleep(60 * 30)
        ADMIN_LOGGED = False


admin_menu_markup = telebot.types.InlineKeyboardMarkup()
admin_menu_markup.row_width = 3
admin_menu_markup.add(telebot.types.InlineKeyboardButton("Add User", callback_data="add_user"),
                        telebot.types.InlineKeyboardButton("Delete User", callback_data="delete_user"),
                        telebot.types.InlineKeyboardButton("Users List", callback_data="users_list"),
                        )




def admin_panel(message):
    password = "admin"
    user_id = message.from_user.id
    if ADMIN_LOGGED:
        bot.reply_to(message, "Admin already logged")


        bot.send_message(message.chat.id, "Choose an option", reply_markup=admin_menu_markup)

        return
    bot.reply_to(message, "Insert password to Login")
    bot.register_next_step_handler(message, admin_panel_password)


def admin_panel_password(message):
    global ADMIN_LOGGED
    if message.text == "admin":
        bot.reply_to(message, "Welcome Admin")
        bot.send_message(message.chat.id, "Choose an option", reply_markup=admin_menu_markup)

        ADMIN_LOGGED = True
        t = threading.Thread(target=logout_session, args=())
        t.start()

    else:
        bot.reply_to(message, "Wrong password")



def add_user_callback(message):
    bot.reply_to(message, "Please insert user email to add")
    bot.register_next_step_handler(message, add_user)

def delete_user_callback(message):
    bot.reply_to(message, "Please insert user email to delete")
    bot.register_next_step_handler(message, delete_user)

def users_list_callback(message):
    users = pd.read_csv("data.csv")
    users = users.values.tolist()
    users = [i[1] for i in users]
    users = "\n".join(users)
    bot.send_message(message.chat.id, "Users List: \n" + users)

def add_user(message):
    user_email = message.text

    users_emails = pd.read_csv("data.csv", usecols=["email"])
    users_emails = users_emails.values.tolist()
    users_emails = [i[0] for i in users_emails]
    print(users_emails)

    if user_email in users_emails:
        bot.reply_to(message, "User already in the list")
        return

    with open("data.csv", "a", newline='', encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["NA", user_email, "NA", "NA", "NA"])
    bot.reply_to(message, "User added")


def delete_user(message):
    user_email = message.text

    users_emails = pd.read_csv("data.csv", usecols=["email"])
    users_emails = users_emails.values.tolist()
    users_emails = [i[0] for i in users_emails]
    print(users_emails)

    if user_email not in users_emails:
        bot.reply_to(message, "User not in the list")
        return

    with open("data.csv", "r", newline='', encoding="utf-8") as file:
        reader = csv.reader(file)
        lines = list(reader)

    with open("data.csv", "w", newline='', encoding="utf-8") as file:
        writer = csv.writer(file)
        for line in lines:
            if line[1] != user_email:
                writer.writerow(line)
    bot.reply_to(message, "User deleted")



threading.Thread(target=scraper).start()
threading.Thread(target=bot.polling).start()
