#!/usr/bin/env python3
import argparse
import json

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler

import logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)


def _parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--token')
    parser.add_argument('config')
    return parser.parse_args()


class Handler:

    def __init__(self, config):
        self._config = config

    def _process_state(self, state_name, update, context):
        if state_name not in self._config:
            logger.error("Can't find state '%s' in config", state_name)
            return

        logger.info('Processing state %s', state_name)
        state = self._config[state_name]

        if 'buttons' in state:
            logger.info('Found buttons state')
            keyboard = []
            for info in state['buttons']:
                keyboard.append(
                    InlineKeyboardButton(info['text'], callback_data=info['state'])
                )
            reply_markup = InlineKeyboardMarkup([keyboard])
            context.bot.send_message(chat_id=update.effective_chat.id, text=state['text'], reply_markup=reply_markup)
            return None
        elif 'image' in state:
            logger.info('Found image state')
            with open(state['image'], 'rb') as fin:
                context.bot.send_photo(chat_id=update.effective_chat.id, photo=fin)
            return state['state']
        elif 'text' in state:
            logger.info('Found text state')
            context.bot.send_message(chat_id=update.effective_chat.id, text=state['text'])
            return state['state']
        else:
            logger.error('Unknown state "%s"', state_name)
            return None

    def _do_process_state(self, state_name, update, context):
        while state_name is not None:
            state_name = self._process_state(state_name, update, context)

    def _button_handler(self, update, context):
        self._do_process_state(update.callback_query.data, update, context)
        update.callback_query.answer()

    def _start_handler(self, update, context):
        self._do_process_state('start', update, context)



def start(update, context):
    keyboard = [[InlineKeyboardButton("Option 1", callback_data='1'),
                 InlineKeyboardButton("Option 2", callback_data='2')],

                [InlineKeyboardButton("Option 3", callback_data='3')]]

    reply_markup = InlineKeyboardMarkup(keyboard)

    update.message.reply_text('Please choose:', reply_markup=reply_markup)


def button(update, context):
    query = update.callback_query

    # CallbackQueries need to be answered, even if no notification to the user is needed
    # Some clients may have trouble otherwise. See https://core.telegram.org/bots/api#callbackquery
    query.answer()

    # query.edit_message_text(text="Selected option: {}".format(query.data))
    context.bot.send_message(chat_id=update.effective_chat.id, text="Selected option: {}".format(query.data))


def main():
    args = _parse_args()

    with open(args.config) as fin:
        config = json.load(fin)

    handler = Handler(config)
    updater = Updater(args.token, use_context=True)

    updater.dispatcher.add_handler(CommandHandler('start', handler._start_handler))
    updater.dispatcher.add_handler(CallbackQueryHandler(handler._button_handler))

    # Start the Bot
    updater.start_polling()

    # Run the bot until the user presses Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT
    updater.idle()


if __name__ == '__main__':
    main()
