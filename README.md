# example-python-slackbot

Example includes `markov_bot.py`, a 'parrot' bot that tracks target user's slack messge and generate response sentences based on markov model. 

The Original post [bot-mimic-colleague](https://hirelofty.com/blog/how-build-slack-bot-mimics-your-colleague/) was using Python slackclient v1, this code updates it with slackclient v2 as slack API usage is largely changed in v2.

This is the reference of [markovify python library](https://github.com/jsvine/markovify).

## pyenv

python 3.7.2

check [requirements.txt](./requirements.txt) for loaded modules 


## run app

First make sure that pyenv virtualenv is correctly set.

```bash
export SLACK_BOT_TOKEN="<token-value>"
python bot.py
```

## kill debug process

```bash
ps aux | grep python
pgrep -f "__main__.py" | xargs kill -9
```
