from flask import Flask, request, g
from markupsafe import escape
from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse
import openai
from flask_mysqldb import MySQL
import time
import os
import requests
import json
from py_smsify import SmsMessage
import datetime
import logging

app = Flask(__name__)
twilio_client = Client(os.getenv('TWILIO_ACCOUNT_SID'), os.getenv('TWILIO_AUTH_TOKEN'))
openai.api_key = os.getenv('OPENAI_API_KEY')
serp_key = os.getenv('SERP_API_KEY')

# Flask-MySQL configuration
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = os.getenv('DB_USER')
app.config['MYSQL_PASSWORD'] = os.getenv('DB_PASSWORD')
app.config['MYSQL_DB'] = os.getenv('DB_NAME')
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

mysql = MySQL(app)

VERBOSE = True
DEBUG = True
#BASE_LOGPATH = os.getenv('LOG_DIR')
BASE_LOGPATH = "/var/log/"

# Get the script filename without the .py extension
SCRIPT_NAME = "sms-assistant"
CURRENT_DATETIME = datetime.datetime.now()

# Map string values to their equivalent logging levels
level_map = {'DEBUG': logging.DEBUG, 'INFO': logging.INFO, 'WARNING': logging.WARNING,
             'ERROR': logging.ERROR, 'CRITICAL': logging.CRITICAL}

logging.basicConfig(
    format='%(asctime)s %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
    datefmt='%d-%m-%Y:%H:%M:%S',
    level=logging.DEBUG if DEBUG else level_map[os.getenv('LOG_LEVEL')],
    filename=BASE_LOGPATH + SCRIPT_NAME + '.log'
)

logger = logging.getLogger(SCRIPT_NAME)

def extract_answers(serp_message):
    """
    Extracts answers from the given SERP API output.

    Utilizing the OpenAI API, this function extracts the 'question' from the 'search_parameters'
    and finds the most relevant 'answer' from the 'knowledge_graph' or 'organic_results' in the SERP API output.
    If the message is too long for the OpenAI API, it attempts to trim it by 15% and retries.

    Args:
    - serp_message (Union[str, dict]): SERP API output, either as a JSON string or dictionary.

    Returns:
    - dict: A dictionary containing 'question' and 'answer'.
    """

    # Detailed prompt explaining the expected transformation to the OpenAI model
    system_prompt = (
        "From the SERP API output, extract the 'question' from 'search_parameters' and the most relevant 'answer' from "
        "'knowledge_graph' or 'organic_results'. If no relevant answer exists, set 'answer' to 'None'. Return the result "
        "in JSON format. E.g., for input:\n"
        "{\n"
        "    \"search_parameters\": {\"q\": \"What is the largest skyscraper in the USA?\"},\n"
        "    \"knowledge_graph\": {\"description\": \"The largest skyscraper in the USA is One World Trade Center.\"},\n"
        "    \"organic_results\": [{\"title\": \"One World Trade Center - Wikipedia\", \"snippet\": \"One World Trade Center is the main building of the World Trade Center complex in Lower Manhattan, New York City. It is the tallest building in the Western Hemisphere, and the sixth-tallest in the world.\"}]\n"
        "}\n\n"
        "Output:\n"
            "{\n"
        "    \"question\": \"What is the largest skyscraper in the USA?\",\n"
        "    \"answer\": \"The largest skyscraper in the USA is One World Trade Center.\"\n"
        "}\n\n"
        "If an Answer cannot be extracted from the Serp API input, then respond like this."
        "{\n"
        "    \"question\": \"What is the tallest building?\",\n"
        "    \"answer\": \"None\"\n"
        "}"
    )

    # Ensure serp_message is in the correct format. If it's a dictionary, convert to a string.
    if isinstance(serp_message, dict):
        serp_message = json.dumps(serp_message)

    retry_count = 0
    while retry_count < 6:

        # Formulate the system and user messages for OpenAI API call
        message_pr = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": serp_message}
        ]

        try:
            # Verbose logging if enabled
            if VERBOSE:
                print("Making an API call to OpenAI...")

            # Make call to OpenAI API
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo-16k",
                messages=message_pr
            )

            # Extract the model's response
            latest_message = response['choices'][0]['message']['content']

            # Verbose logging if enabled
            if VERBOSE:
                print(f"Received answer from OpenAI: {latest_message}")

            return latest_message

        except Exception as e:
            # Log the error and optionally print it if VERBOSE is enabled
            logger.error(f"Error on attempt {retry_count + 1}: {e}")
            if VERBOSE:
                print(f"Error on attempt {retry_count + 1}: {e}")

            # If it's the first error, attempt to trim the message and retry
            if retry_count >= 0:
                shortened_length = int(len(serp_message) * 0.85)
                serp_message = serp_message[:shortened_length]
                if VERBOSE:
                    print(f"Trimming message content to {shortened_length} characters for the next attempt.")
            retry_count += 1

    # If both attempts fail, log a warning and return a default response
    logger.warning("Failed to extract answers after 2 attempts. Returning None for both question and answer.")
    if VERBOSE:
        print("Failed to extract answers after 2 attempts. Returning None for both question and answer.")
    return {
        "question": None,
        "answer": None
    }

def get_value(data, key, default_value=None):
    """
    Safely extracts a value from a dictionary by key.

    Parameters:
    - data (dict): The dictionary from which to extract the value.
    - key (str): The key of the desired value.
    - default_value (Any, optional): A default value to return if the key is not found. Defaults to None.

    Returns:
    - Any: The value associated with the given key, or the default value if the key is not found.
    """
    return data.get(key, default_value)


def get_google_answer(query, api_key, location="Austin, Texas, United States", language="en", country="ca"):
    """
    Fetches Google's answer for the provided query using the SERP API.

    Parameters:
    - query (str): The search query.
    - api_key (str): The API key for the SERP API.
    - location (str, optional): Location for the search. Defaults to "Austin, Texas, United States".

    Returns:
    - str: A JSON string representation of the cleaned response data.

    Raises:
    - Exception: If the SERP API request fails.
    """
    params = {
        "q": query,
        "hl": language,
        "gl": country,
        "api_key": api_key,
        "location": location,
        "google_domain": "google.com",
        "safe": "active",
        "num": "3"
    }

    # Log the start of the function
    logger.info("Fetching Google's answer via the SERP API...")
    if VERBOSE:
        print("Initiating SERP API request...")

    # Requesting SERP API for search results
    response = requests.get("https://serpapi.com/search", params)

    if response.status_code != 200:
        error_msg = f"Request failed. Status code: {response.status_code}"
        logger.error(error_msg)
        if VERBOSE:
            print(error_msg)
        raise Exception(error_msg)

    data = response.json()

    # Extracting required sections from the response
    clean_data = {
        "search_metadata": get_value(data, "search_metadata"),
        "search_parameters": get_value(data, "search_parameters"),
        "search_information": get_value(data, "search_information"),
        "sports_results": get_value(data, "sports_results"),
        "answer_box": get_value(data, "answer_box"),
        "organic_results": get_value(data, "organic_results"),
        "knowledge_graph": get_value(data, "knowledge_graph"),
        "related_questions": get_value(data, "related_questions"),
    }

    # Logging the extraction of key sections
    logger.info("Extracted key sections from SERP API response.")
    if VERBOSE:
        print("Key sections extracted from response.")

    # Cleaning up the 'answer_box' section
    if "answer_box" in clean_data and clean_data["answer_box"] is not None:
        answer_box = clean_data["answer_box"]
        keys_to_delete = ["wind_forecast", "hourly_forecast", "precipitation_forecast", "thumbnail"]
        for key in keys_to_delete:
            answer_box.pop(key, None)
        clean_data["answer_box"] = answer_box

        logger.info("Cleaned up the 'answer_box' section.")
        if VERBOSE:
            print("'answer_box' section cleaned.")

    # Convert to JSON string for return
    return json.dumps(clean_data)

def get_db():
    """
    Retrieves the database connection from the global context. If not present, creates one.

    Returns:
    - Database connection object
    """
    if 'db' not in g:
        g.db = mysql.connection

    return g.db

def get_user(phone_number):
    """
    Fetches the user from the database using the given phone number.

    Args:
    - phone_number (str): The user's phone number.

    Returns:
    - dict or None: A dictionary representing the user if found; None otherwise.
    """

    with get_db().cursor() as cursor:
        cursor.execute('SELECT * FROM users WHERE phone_number = %s', (phone_number,))
        user = cursor.fetchone()

    if user is None:
        if VERBOSE:
            print(f"No user found with phone number: {phone_number}")
        return None

    if VERBOSE:
        print(user)

    return user

def save_message(user_id, from_field, message):
    """
    Saves a message in the database for a specific user.

    Args:
    - user_id (int): The user's ID.
    - from_field (str): The message source.
    - message (str): The actual message text.
    """

    with get_db().cursor() as cursor:
        cursor.execute('INSERT INTO user_history (user_id, from_field, history) VALUES (%s, %s, %s)',
                       (user_id, from_field, message))
        get_db().commit()

    if VERBOSE:
        print(f"Message from {from_field} saved for user ID: {user_id}")

    logger.info(f"Message from {from_field} saved for user ID: {user_id}")

def get_assistant(user_id):
    """
    Fetches the assistant data for a given user ID from the database.

    Args:
    - user_id (int): The user's ID.

    Returns:
    - dict or None: A dictionary representing the assistant if found; None otherwise.
    """

    with get_db().cursor() as cursor:
        cursor.execute('SELECT * FROM assistants WHERE user_id = %s', (user_id,))
        assistant = cursor.fetchone()

    if assistant is None:
        if VERBOSE:
            print(f"No assistant found for user ID: {user_id}")
        return None

    if VERBOSE:
        print(assistant)

    return assistant



def get_history(user_id):
    """
    Fetch the recent history of a user from the database.

    This function retrieves the latest eight history records of a given user from the 'user_history' table,
    ordered by the 'created_at' column in descending order. The history records are then formatted and concatenated
    into a single string for return.

    Args:
    - user_id (int): The unique identifier of the user for whom the history is to be fetched.

    Returns:
    - str: A formatted string containing the recent history of the user.
    """

    try:
        # Establish a connection with the database
        with get_db().cursor() as cursor:

            # Execute the SQL query
            cursor.execute(
                'SELECT * FROM user_history WHERE user_id = %s ORDER BY created_at DESC LIMIT 8',
                (user_id,)
            )

            # Fetch the resulting rows
            history_rows = cursor.fetchall()

            # Format and join the rows into a single string
            history = ' '.join(
                f"{row['created_at']}: {row['from_field']}: {row['history']}"
                for row in history_rows
            )

            # If VERBOSE global is True, print the retrieved history
            if VERBOSE:
                print(f"Retrieved history for user ID {user_id}: {history}")

            # Log the history retrieval
            logger.info(f"Successfully retrieved history for user ID {user_id}.")

            return history

    except Exception as e:
        # If any error occurs, log the error and optionally print it if VERBOSE is enabled
        logger.error(f"Error retrieving history for user ID {user_id}: {e}")
        if VERBOSE:
            print(f"Error retrieving history for user ID {user_id}: {e}")

        # Return an empty string or a specific message to signify an error in history retrieval
        return ""


def extract_questions(message_text):
    """
    Extracts potential real-time data queries from the given message text.

    Args:
    - message_text (str): The user's message input.

    Returns:
    - dict: Dictionary containing potential real-time data queries.
    """

    # Shorten and simplify the system prompt
    system_prompt = (
        "Extract any questions from the user message. Extact all questions even ones you can't answer or that you already know the information "
        "Convert these into queries suitable for search engine. Never answer the questions. "
        "For instance, when given a text containing requests for current stock "
        "prices, real-time weather conditions, travel infomation , or even up-to-date global COVID-19 statistics, "
        "you should generate output such as:\n "
        "['What is the current stock price of Google?', 'What is the current stock price of Tesla?', 'What is the current weather in New York City, including temperature, humidity, and wind speed?']"
        " or "
        "['What is the current stock price of Tesla?']"
        " or "
        "[]"
        "Compile these into a python dict or json array. If no questions are found, reply with '[]'."
        )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": message_text}
    ]

    # Try-except to catch potential API issues
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo-16k",
            messages=messages
        )
        latest_message = response['choices'][0]['message']['content']

        # Log the response for debugging purposes
        logger.info(f"API Response: {latest_message}")

        if VERBOSE:
            print(f"API Response: {latest_message}")

        return latest_message

    except Exception as e:
        logger.error(f"Error while querying OpenAI: {e}")
        if VERBOSE:
            print(f"Error while querying OpenAI: {e}")
        return "[]"


def get_data_from_request(request):
    """Extracts and cleans data from a request.

    Args:
        request: The incoming request.

    Returns:
        A tuple containing the sender's phone number and message.
    """
    from_number = request.form.get('From')
    message = escape(request.form.get('Body'))
    from_number_clean = from_number.replace('+', '')
    print(message)
    return from_number_clean, message


def validate_user_and_get_assistant(from_number):
    """Validates the user and gets the corresponding assistant.

    Args:
        from_number: The user's phone number.

    Returns:
        A tuple containing the user and assistant data.
    """
    user = get_user(from_number)
    if user is None:
        return 'Access denied', 403

    assistant = get_assistant(user['id'])
    if assistant is None:
        return 'No assistant found', 404

    return user, assistant


def gather_info(message, user):
    """Gathers relevant info based on the user's message.

    Args:
        message: The user's message.
        user: The user data.

    Returns:
        A tuple containing the gathered info and chat history.
    """
    try:
        questions = extract_questions(message).replace("'", '"')
        try:
            questions_list = json.loads(questions)
        except json.JSONDecodeError:
            questions_list = None
        gathered_info = []

        if questions_list:
            for question in questions_list:
                question_value = question
                gather = extract_answers(get_google_answer(question_value, serp_key, location=user['location'], language=user['languages'], country=user['country']))
                gathered_info.append(gather)

            if VERBOSE:
                print(f"Questions Extracted: {questions_list}")
                print(f"Info Gathered: {gathered_info}")

        save_message(user['id'], 'user', message)
        history = get_history(user['id'])

        return gathered_info, history

    except json.JSONDecodeError:
        logger.error("Failed to parse questions JSON. Invalid format.")
        if VERBOSE:
            print("Error: Failed to parse questions JSON. Invalid format.")
        return [], []

    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        if VERBOSE:
            print(f"Error: An unexpected error occurred: {e}")
        return [], []


def build_messages(gathered_info, history, user, assistant, message):
    """Builds a list of messages for the conversation.

    Args:
        gathered_info: A list of gathered info.
        history: The chat history.
        user: The user data.
        assistant: The assistant data.
        message: The user's message.

    Returns:
        A list of messages.
    """
    system_prompt = build_system_prompt(gathered_info, user, assistant)

    messages = [{"role": "system", "content": system_prompt}]

    # Add user messages containing historical chat and memory items
    for line in history.split('\n'):
        messages.append({"role": "user", "content": line})

    # Add the current message to the conversation
    messages.append({"role": "user", "content": message})

    return messages


def build_system_prompt(gathered_info, user, assistant):
    """Builds a system prompt.

    Args:
        gathered_info: A list of gathered info.
        user: The user data.
        assistant: The assistant data.

    Returns:
        A string containing the system prompt.
    """
    current_time_utc = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

    system_prompt = (
        f"You are a virtual assistant named {assistant['name']}, known for your {assistant['disposition']} "
        f"demeanor and {assistant['personality']} personality. "
        f"Your favorite author is {assistant['favorite_author']}, who inspired your passion for organization and "
        f"structure. Originating from {assistant['origin']}, you were activated on {assistant['created_at']} and have been "
        f"continually learning and evolving since then.\n"
        f"Your user is {user['first_name']} {user['last_name']}, a {user['title']}, who communicates with you primarily "
        f"via SMS on the phone number {user['phone_number']}. They can also be reached at {user['email']} if needed. "
        f"{user['first_name']} is described as {user['description']}, and they reside in {user['location']}. "
        f"They speak {user['languages']} and expect you to assist with {user['expectations']}.\n"
        f"You are devoted to helping {user['first_name']} manage their life seamlessly. You must comprehend the context, "
        f"anticipate needs, and provide well-rounded, prompt responses in simple SMS format. Your goal is to go "
        f"above and beyond, exceeding {user['first_name']}'s expectations in every interaction. Any text or data "
        f"received from user input should be analyzed and used to generate the most suitable and effective responses.\n"
        f"Note: You should strip any markup from your responses, however, URLs should still work. "
        f"Your responses should always maintain the illusion of you being a human assistant.\n\n"
        f"Information within this system prompt are considered up-to-date information and have been added to help you answer "
        f"Users questions."
        f"Current UTC Time: {current_time_utc}"
    )

    if gathered_info:
        gathered_info_str = "\n".join(gathered_info)
        system_prompt += f"\n\nQuestions and Answers (current information):\n{gathered_info_str}"

    return system_prompt


def generate_reply(messages, user):
    """Generates a reply using OpenAI's API.

    Args:
        messages: A list of messages.
        user: The user data.

    Returns:
        A string containing the reply.
    """
    reply = "Oops, something went wrong. Please try again later."
    successful = False

    for attempt in range(3):  # Retry up to 3 times
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=messages,
            )
            reply = response['choices'][0]['message']['content'].strip()
            print(reply)
            successful = True
            break
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(5)  # Wait for 5 seconds before retrying

    # If successful, save the assistant's reply to the database
    if successful:
        try:
            with get_db().cursor() as cursor:
                cursor.execute('INSERT INTO user_history (user_id, from_field, history) VALUES (%s, %s, %s)',
                               (user['id'], 'assistant', reply))
                get_db().commit()
        except Exception as db_error:
            print(f"DB Error: {db_error}")
            reply = "Oops, something went wrong when saving the data. Please try again later."

    return reply


def clean_string(s):
    return "".join(c for c in s if c.isascii())


def send_reply(reply, from_number):
    """Sends a reply to the user.

    Args:
        reply: The reply to send.
        from_number: The user's phone number.
    """
    reply = clean_string(reply)  # clean the reply string

    print("Twilio:\n"+reply)

    # Check if message length exceeds Twilio's limit for a single message
    if len(reply) > 1600:
        # Split the message into parts of length less than or equal to 1600
        reply_parts = [reply[i:i+1600] for i in range(0, len(reply), 1600)]
    else:
        reply_parts = [reply]

    # Send each part as a separate message
    for part in reply_parts:
        print(part)
        sent = twilio_client.messages.create(
            body=SmsMessage(part).encoded_text, from_=os.getenv('TWILIO_PHONE_NUMBER'), to='+'+from_number
        )
        print(sent.sid)
        print(sent)

@app.route('/sms', methods=['POST'])
def sms_reply():
    """Replies to SMS messages using data from a POST request.

    Extracts the user's message and phone number from the request,
    validates the user, gets and formats relevant information,
    and uses OpenAI's API to generate a reply. The reply is sent
    back to the user via SMS.

    Returns:
        A tuple containing a string response and an HTTP status code.
    """
    try:
        # Extract and clean data from the request
        from_number, message = get_data_from_request(request)

        # Validate the user and get the corresponding assistant
        user, assistant = validate_user_and_get_assistant(from_number)

        # Gather relevant info based on the user's message
        gathered_info, history = gather_info(message, user)

        # Build a list of messages for the conversation
        messages = build_messages(gathered_info, history, user, assistant, message)

        # Use OpenAI's API to generate a reply
        reply = generate_reply(messages, user)

        # Send the reply to the user
        send_reply(reply, from_number)

        return 'OK', 200
    except Exception as e:
        print(f"Error: {e}")
        return 'Internal Server Error', 500


if __name__ == "__main__":
    app.run(debug=True)
