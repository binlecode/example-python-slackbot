import markovify
import time
import os

from slack import WebClient
from slack import RTMClient

# BOT_TOKEN = os.environ["SLACK_BOT_TOKEN"]

BOT_TOKEN = 'xoxb-634428264979-791218203461-DKEIXKbtiIukhLqGZDUYxFW2'

def main():
    """
    Startup logic and the main application loop to monitor Slack events.
    """

    # Create the slackclient instance
    sc = WebClient(token=BOT_TOKEN)

    # Connect to slack RTM API
    if not sc.rtm_connect():
        raise Exception("Couldn't connect to slack.")

    print("Starter Bot connected and running!")
    # Each bot user has a user ID for each workspace the Slack App is installed within.
    # Read bot's user ID by calling Web API method `auth.test`
    bot_id = sc.api_call("auth.test")["user_id"]

    print('slack channels:')
    channels = sc.channels_list()['channels']
    for cnl in channels:
        print(str(cnl))

    # this will raise StopIteration error if not found, which will never happen for 'general' channel
    chn_general = next(c for c in channels if c['name'] == 'general')
    # usr_bot = next(u for u in sc.users_list()['members'] if u['name'] == 'test-py-bot')

    if bot_id not in chn_general['members']:
        raise Exception(f"Bot {bot_id} is not a member of channel {chn_general['name']}")
        
    # test shout out
    sc.chat_postMessage(
        channel=chn_general['id'],  # general channel
        text="Hello from test-py-bot! :tada:"
    )

# The Real Time Messaging (RTM) API is a WebSocket-based API that allows you to receive events 
# from Slack in real time and send messages as users.
# An RTMClient allows apps to communicate with the Slack Platform's RTM API

@RTMClient.run_on(event='message')
def echo_msg(**payload):
    # Get WebClient so you can communicate back to Slack
    web_client = payload['web_client']

    data = payload['data']
    # use get() to avoid key missing error, esp from json (python dict) parsing
    user_id = data.get('user')  
    channel_id = data.get('channel')
    text = data.get('text')

    # Since message event catches all messages sent to slack, including those from bot,
    # user_id check is filtering non-user messages 
    if user_id:
        print(f"receive message from user {user_id} in channel {channel_id}")

        if text and text.lower() == 'hello':
            web_client.chat_postMessage(
                channel=channel_id,
                text=f"Hi <@{user_id}>!",
            )


def run_echo_svr():
    rtm_client = RTMClient(token=BOT_TOKEN)
    rtm_client.start()



if __name__ == '__main__':
    # main()
    run_echo_svr()