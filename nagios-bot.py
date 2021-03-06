#!/usr/bin/python2.6
import sys

from ircutils import bot
import re
import os
from settings import *
import subprocess
import time
from MozillaIRCPager import MozillaIRCPager
from MozillaNagiosStatus import MozillaNagiosStatus
class NagiosBot(bot.SimpleBot):
    my_nick = ''
    to_me = False
    message = ''
    has_registered = False
    ### message_commands is a list of dictionary objects. The regex object is the regex to match, the function object is the function name to call at a match

    plugins = [
                {'plugin':MozillaIRCPager},
                {'plugin':MozillaNagiosStatus},
              ]
    help_commands = []
    message_commands = []
    def load_plugins(self):
        self.message_commands.append({'class':NagiosBot, 'regex':'help$', 'function':'print_help'})
        for plugin in self.plugins:
            plugin = plugin['plugin'](self, channels)
            for mc in plugin.return_plugins():
                self.message_commands.append(mc)
            for mc in plugin.return_help():
                self.help_commands.append(mc)
    def on_channel_message(self, event):
        if re.search('^%s[,: ]' % self.bot_name, event.message):
            self.message = re.sub('^%s[,: ]+' % self.bot_name, '', event.message).strip()
            if self.message == 'help':
                self.send_message(event.target, "%s: Here is a list of available commands" % (event.source))
                for hc in self.help_commands:
                    self.send_message(event.target, "%s" % (hc))
            else:
                _is_found = False
                for message_command in self.message_commands:
                    if _is_found is False:
                        m = re.search(message_command['regex'], self.message)
                        if m is not None:
                            _is_found = True
                            try:
                                target, message = message_command['callback'](event, event.message, m)
                                if isinstance(message, basestring):
                                    self.send_message(target, message)
                                else:
                                    for m in message:
                                        self.send_message(target, m)

                            except Exception, e:
                                self.send_message(event.target, "%s: %s From Exception I'm sorry but I don't understand your command" % (e, event.source) )
                if _is_found is False:
                    self.send_message(event.target, "%s: I'm sorry but I don't understand your command" % (event.source) )
    def on_notice(self, event):
        print event.params
    def on_any(self, event):
        #print event.params
        #print dir(event)
        #print event.message
        if event.command == "TOPIC" or event.command == 'RPL_LIST' or event.command == 'RPL_TOPIC' or event.command == 'RPL_TOPICWHOTIME':
            self.set_topic(event)
        if not self.has_registered:
            try:
                if event.params[0] == "End of /MOTD command.":
                    time.sleep(2)
                    nagios_bot.send_message("NickServ", "IDENTIFY %s" % (identify_pass))
                    self.has_registered = True
            except:
                pass

    """ Handler for when the bot joins a room.
        Bot will ask for the topic and then it will get caught by the on_any handler
        The on_any handler will dispatch to set_topic()
    """
    def on_join(self, event):
        self.execute("TOPIC", event.target)

    def set_topic(self, event):
        #print event.target
        channel = None
        topic = None
        if event.command == "TOPIC" or event.command == 'RPL_TOPIC':
            channel = event.target
            topic = event.params[0]
        if event.command == 'RPL_TOPIC':
            channel = event.params[0]
            topic = event.params[1]
        if channel and topic:
            for c in channels:
                if c['name'] == channel:
                    c['topic'] = topic
    def on_disconnect(self, event):
        print "Disconnected, trying reconnect in 5 sec."
        time.sleep(5)
        self.connect(server, port=port, use_ssl=use_ssl, channel = [channel['name'] for channel in channels], ssl_options=ssl_options)

    @staticmethod            
    def print_help(conn, event, options):
        messages = []
        messages.append("page <id> (Optional) <recipient> (Required) <message> (Reqired)")
        print event.target
        for message in messages:
            conn.send_message(event.target, message)
    

if __name__ == "__main__":
    nagios_bot = NagiosBot(bot_name)
    nagios_bot.bot_name = bot_name
    nagios_bot.connect(server, port=port, use_ssl=use_ssl, channel = [channel['name'] for channel in channels], ssl_options=ssl_options)
    nagios_bot.load_plugins()
    nagios_bot.start()
    nagios_bot.register_listener('RPL_TOPIC', on_topic)
    nagios_bot.register_listener('topic', on_topic)
    nagios_bot.identify(identify_pass)
