import json
import markovify
import re
import time
import os

from slack import WebClient
from slack import RTMClient


BOT_TOKEN = os.environ["SLACK_BOT_TOKEN"]

MESSAGE_QUERY = "from:bin.le.code"
MESSAGE_PAGE_SIZE = 100
DEBUG = True

MESSAGE_DB_FILE = '.message_db.json'


def _load_db():
    """
    Reads 'database' from a JSON file on disk.
    Returns a dictionary keyed by unique message permalinks.
    """
    try:
        with open(MESSAGE_DB_FILE, 'r') as json_file:
            messages = json.loads(json_file.read())
    except IOError:
        with open(MESSAGE_DB_FILE, 'w') as json_file:
            json_file.write('{}')
        messages = {}

    if not messages:
        messages['client'] = 'bot'

    return messages


def _store_db(obj):
    """
    Takes a dictionary keyed by unique message permalinks and writes it to the JSON 'database' on
    disk.
    """
    with open(MESSAGE_DB_FILE, 'w') as json_file:
        json_file.write(json.dumps(obj))

    return True


def _query_messages(client, page=1):
    """
    Convenience method for querying messages from Slack API.
    """
    if DEBUG:
        print(f"requesting page {page}")

    return client.search_messages(query=MESSAGE_QUERY, count=MESSAGE_PAGE_SIZE, page=page)

def _add_messages(message_db, new_messages):
    """
    Search through an API response and add all messages to the 'database' dictionary.
    Returns updated dictionary.
    """
    for match in new_messages['messages']['matches']:
        message_db[match['permalink']] = match['text']

    return message_db


# get all messages, build a giant text corpus
def build_text_model():
    """
    Read the latest 'database' off disk and build a new markov chain generator model.
    Returns TextModel.
    """
    if DEBUG:
        print("Building new model...")

    messages = _load_db()
    return markovify.Text(" ".join(messages.values()), state_size=2)


def format_message(original):
    """
    Do any formatting necessary to markon chains before relaying to Slack.
    """
    if original is None:
        return

    # Clear <> from urls
    cleaned_message = re.sub(r'<(htt.*)>', '\1', original)

    return cleaned_message


def update_corpus(sc, channel):
    """
    Queries for new messages and adds them to the 'database' object if new ones are found.
    Reports back to the channel where the update was requested on status.
    """

    # sc.rtm_send_message(channel, "")
    sc.chat_postMessage(channel=channel, text='Leveling up...')

    # Messages will get queried by a different auth token
    # So we'll temporarily instantiate a new client with that token
    group_sc = WebClient(BOT_TOKEN)

    # Load the current database
    messages_db = _load_db()
    starting_count = len(messages_db.keys())

    # Get first page of messages
    new_messages = _query_messages(group_sc)
    total_pages = new_messages['messages']['paging']['pages']

    # store new messages
    messages_db = _add_messages(messages_db, new_messages)

    # If any subsequent pages are present, get those too
    if total_pages > 1:
        for page in range(2, total_pages + 1):
            new_messages = _query_messages(group_sc, page=page)
            messages_db = _add_messages(messages_db, new_messages)

    # See if any new keys were added
    final_count = len(messages_db.keys())
    new_message_count = final_count - starting_count

    # If the count went up, save the new 'database' to disk, report the stats.
    if final_count > starting_count:
        # Write to disk since there is new data.
        _store_db(messages_db)
        sc.chat_postMessage(channel=channel, text=f"I have been imbued with the power of {new_message_count} new messages!")
    else:
        sc.chat_postMessage(channel=channel, text="No new messages found :(")

    if DEBUG:
        print("Start: {}".format(starting_count), "Final: {}".format(final_count),
              "New: {}".format(new_message_count))

    # Make sure we close any sockets to the other group.
    del group_sc

    return new_message_count


def main():
    """
    Startup logic and the main application loop to monitor Slack events.
    """

    # build the text model
    model = build_text_model()

    # Create the slackclient instance
    sc = WebClient(BOT_TOKEN)

    # check Slack API connection
    if not sc.rtm_connect():
        raise Exception("Couldn't connect to slack.")


    @RTMClient.run_on(event='message')
    def echo_msg(**payload):
        nonlocal model

        # Get WebClient so you can communicate back to Slack
        sc = payload['web_client']

        data = payload['data']
        # use get() to avoid key missing error, esp from json (python dict) parsing
        user_id = data.get('user')  
        channel_id = data.get('channel')
        message = data.get('text')

        # Since message event catches all messages sent to slack, including those from bot,
        # user_id and message are checked
        if user_id and message:
            print(f"receive message from user {user_id} in channel {channel_id}")

            if "parrot me" in message.lower():
                markov_chain = model.make_sentence() or "I don't know what to say."
                sc.chat_postMessage(channel=channel_id, text=format_message(markov_chain))

            if "level up parrot" in message.lower():
                # Fetch new messages.  If new ones are found, rebuild the text model
                if update_corpus(sc, channel_id) > 0:
                    model = build_text_model()


    # Where the magic happens
    rtm_client = RTMClient(token=BOT_TOKEN)
    rtm_client.start()


if __name__ == '__main__':
    main()

