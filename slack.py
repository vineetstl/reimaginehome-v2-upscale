import logging
from slack_logger import SlackHandler, SlackFormatter

sh = SlackHandler(
    'https://hooks.slack.com/services/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')
sh.setFormatter(SlackFormatter())
logging.basicConfig(handlers=[sh])
logging.getLogger().setLevel(logging.INFO)
logging.info('warn message')
