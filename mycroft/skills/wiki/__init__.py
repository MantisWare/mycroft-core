# Copyright 2016 Mycroft AI, Inc.
#
# This file is part of Mycroft Core.
#
# Mycroft Core is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Mycroft Core is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Mycroft Core.  If not, see <http://www.gnu.org/licenses/>.


import re
from os.path import join, dirname
from random import randrange

import wikipedia as wiki

from adapt.intent import IntentBuilder
from mycroft.skills.core import MycroftSkill
from mycroft.util import read_stripped_lines
from mycroft.util.log import getLogger

__author__ = 'jdorleans'

LOGGER = getLogger(__name__)


class WikipediaSkill(MycroftSkill):
    def __init__(self):
        super(WikipediaSkill, self).__init__(name="WikipediaSkill")
        self.max_results = int(self.config['max_results'])
        self.max_phrases = int(self.config['max_phrases'])
        self.question = 'Would you like to know more about '  # TODO - i10n
        self.feedback_prefix = read_stripped_lines(
            join(dirname(__file__), 'dialog', self.lang,
                 'FeedbackPrefix.dialog'))
        self.feedback_search = read_stripped_lines(
            join(dirname(__file__), 'dialog', self.lang,
                 'FeedbackSearch.dialog'))

    def initialize(self):
        self.load_vocab_files(join(dirname(__file__), 'vocab', 'en-us'))

        prefixes = ['wiki', 'wikipedia', 'tell me about', 'tell us about',
                    'who is', 'who was']  # TODO - i10n
        self.__register_prefixed_regex(prefixes, "(?P<ArticleTitle>.*)")

        intent = IntentBuilder("WikipediaIntent").require(
            "WikipediaKeyword").require("ArticleTitle").build()
        self.register_intent(intent, self.handle_intent)

    def __register_prefixed_regex(self, prefixes, suffix_regex):
        for prefix in prefixes:
            self.register_regex(prefix + ' ' + suffix_regex)

    def handle_intent(self, message):
        try:
            title = message.metadata.get("ArticleTitle")
            self.__feedback_search(title)
            results = wiki.search(title, self.max_results)
            summary = re.sub(
                r'\([^)]*\)|/[^/]*/', '',
                wiki.summary(results[0], self.max_phrases))
            self.speak(summary)

        except wiki.exceptions.DisambiguationError as e:
            options = e.options[:self.max_results]
            LOGGER.debug("Multiple options found: " + ', '.join(options))
            self.__ask_more_about(options)

        except Exception as e:
            LOGGER.error("Error: {0}".format(e))

    def __feedback_search(self, title):
        prefix = self.feedback_prefix[randrange(len(self.feedback_prefix))]
        feedback = self.feedback_search[randrange(len(self.feedback_search))]
        sentence = feedback.replace('<prefix>', prefix).replace(
            '<title>', title)
        self.speak(sentence)

    def __ask_more_about(self, opts):
        sentence = self.question
        size = len(opts)

        for idx, opt in enumerate(opts):
            sentence += opt

            if idx < size - 2:
                sentence += ', '
            elif idx < size - 1:
                sentence += ' or '  # TODO - i10n

        self.speak(sentence)

    def stop(self):
        pass


def create_skill():
    return WikipediaSkill()
