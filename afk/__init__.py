# -*- encoding: utf-8 -*-
#
# AFK Plugin for BigBrotherBot(B3) (www.bigbrotherbot.net)
# Copyright (C) 2015 Thomas LEVEIL <thomasleveil@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA 02110-1301 USA
#
from ConfigParser import NoOptionError
from threading import Timer
from time import time
from b3 import TEAM_SPEC, TEAM_UNKNOWN
from b3.plugin import Plugin
from weakref import WeakKeyDictionary

__author__ = "Thomas LEVEIL"
__version__ = "1.0"


class AfkPlugin(Plugin):
    def __init__(self, console, config=None):
        """
        Build the plugin object.
        """
        Plugin.__init__(self, console, config)

        """:type : WeakKeyDictionary of [Client, int]"""
        self.last_activity_by_player = None

        """:type : int"""
        self.check_frequency_second = 0

        """:type : int"""
        self.inactivity_threshold_second = None

        """:type : int"""
        self.last_chance_delay = 10

        """:type : str"""
        self.kick_reason = None

        """:type : str"""
        self.are_you_afk = None

        """:type : threading.Timer"""
        self.check_timer = None

        """:type : WeakKeyDictionary of [Client, threading.Timer]"""
        self.kick_timers = WeakKeyDictionary()

    def onLoadConfig(self):
        try:
            self.check_frequency_second = int(60 * self.config.getDuration('settings', 'check_frequency'))
            self.info('settings/check_frequency: %s sec' % self.check_frequency_second)
        except (NoOptionError, ValueError), err:
            self.warning("No value or bad value for settings/check_frequency. %s", err)
            self.check_frequency_second = 0
        else:
            if self.check_frequency_second < 0:
                self.warning("settings/check_frequency cannot be less than 0")
                self.check_frequency_second = 0

        try:
            self.inactivity_threshold_second = int(60 * self.config.getDuration('settings', 'inactivity_threshold'))
            self.info('settings/inactivity_threshold: %s sec' % self.inactivity_threshold_second)
        except (NoOptionError, ValueError), err:
            self.warning("No value or bad value for settings/inactivity_threshold. %s", err)
            self.inactivity_threshold_second = 0
        else:
            if self.inactivity_threshold_second < 30:
                self.warning("settings/inactivity_threshold cannot be less than 30 sec")
                self.inactivity_threshold_second = 30

        try:
            self.kick_reason = self.config.get('settings', 'kick_reason')
            if len(self.kick_reason.strip()) == 0:
                raise ValueError()
            self.info('settings/kick_reason: %s sec' % self.kick_reason)
        except (NoOptionError, ValueError), err:
            self.warning("No value or bad value for settings/kick_reason. %s", err)
            self.kick_reason = "AFK for too long on this server"

        try:
            self.are_you_afk = self.config.get('settings', 'are_you_afk')
            if len(self.are_you_afk.strip()) == 0:
                raise ValueError()
            self.info('settings/are_you_afk: %s sec' % self.are_you_afk)
        except (NoOptionError, ValueError), err:
            self.warning("No value or bad value for settings/are_you_afk. %s", err)
            self.are_you_afk = "Are you AFK?"

        self.stop_check_timer()
        self.stop_kick_timers()
        self.start_check_timer()

    def onStartup(self):
        """
        Initialize plugin.
        """
        # register events needed
        self.registerEvent(self.console.getEventID('EVT_CLIENT_CONNECT'), self.on_client_init_activity)
        self.registerEvent(self.console.getEventID('EVT_CLIENT_AUTH'), self.on_client_init_activity)
        self.registerEvent(self.console.getEventID('EVT_CLIENT_JOIN'), self.on_client_init_activity)

        self.registerEvent(self.console.getEventID('EVT_CLIENT_SAY'), self.on_client_activity)
        self.registerEvent(self.console.getEventID('EVT_CLIENT_TEAM_SAY'), self.on_client_activity)
        self.registerEvent(self.console.getEventID('EVT_CLIENT_SQUAD_SAY'), self.on_client_activity)
        self.registerEvent(self.console.getEventID('EVT_CLIENT_PRIVATE_SAY'), self.on_client_activity)
        self.registerEvent(self.console.getEventID('EVT_CLIENT_KILL'), self.on_client_activity)
        self.registerEvent(self.console.getEventID('EVT_CLIENT_GIB'), self.on_client_activity)
        self.registerEvent(self.console.getEventID('EVT_CLIENT_GIB_TEAM'), self.on_client_activity)
        self.registerEvent(self.console.getEventID('EVT_CLIENT_GIB_SELF'), self.on_client_activity)
        self.registerEvent(self.console.getEventID('EVT_CLIENT_SUICIDE'), self.on_client_activity)
        self.registerEvent(self.console.getEventID('EVT_CLIENT_KILL_TEAM'), self.on_client_activity)
        self.registerEvent(self.console.getEventID('EVT_CLIENT_DAMAGE'), self.on_client_activity)
        self.registerEvent(self.console.getEventID('EVT_CLIENT_DAMAGE_SELF'), self.on_client_activity)
        self.registerEvent(self.console.getEventID('EVT_CLIENT_DAMAGE_TEAM'), self.on_client_activity)
        self.registerEvent(self.console.getEventID('EVT_CLIENT_ITEM_PICKUP'), self.on_client_activity)
        self.registerEvent(self.console.getEventID('EVT_CLIENT_ACTION'), self.on_client_activity)

        self.last_activity_by_player = WeakKeyDictionary()
        self.penalty_timers = WeakKeyDictionary()

    def onEnable(self):
        self.start_check_timer()

    def onDisable(self):
        self.info("stopping timers")
        self.stop_check_timer()
        self.stop_kick_timers()

    ####################################################################################################################
    #                                                                                                                  #
    #   EVENTS                                                                                                         #
    #                                                                                                                  #
    ####################################################################################################################

    def on_client_init_activity(self, event):
        """
        create an entry in self.last_activity_by_player if missing.

        :param event: b3.events.Event
        """
        if not event.client:
            return

        if event.client not in self.last_activity_by_player:
            self.last_activity_by_player[event.client] = time()

    def on_client_activity(self, event):
        """
        update an entry in self.last_activity_by_player.

        :param event: b3.events.Event
        """
        if not event.client:
            return

        self.last_activity_by_player[event.client] = time()

        # cancel eventual pending kick
        if event.client in self.kick_timers:
            self.info("cancelling pending kick for %s due to new activity" % event.client)
            self.kick_timers.pop(event.client).cancel()


    ####################################################################################################################
    #                                                                                                                  #
    #   OTHERS                                                                                                         #
    #                                                                                                                  #
    ####################################################################################################################

    def search_for_afk(self):
        """
        check all connected players who are not in the spectator team for inactivity.
        """
        self.verbose("looking for afk players...")
        for client in self.console.clients.getList():
            self.check_client(client)
        self.start_check_timer()

    def check_client(self, client):
        """
        check if client is afk
        :param client: b3.clients.Client
        """
        if self.is_client_inactive(client):
            self.ask_client(client)

    def is_client_inactive(self, client):
        if client.team in (TEAM_SPEC,):
            self.verbose2("%s is in %s team" % (client.name, client.team))
            return False
        if client in self.last_activity_by_player:
            last_activity_time = self.last_activity_by_player[client]
            current_time = time()
            self.verbose2("last activity for %s: %s (current time: %s, threshold: %s)" % (
                client.name,
                last_activity_time,
                current_time,
                self.inactivity_threshold_second
            ))
            if last_activity_time + self.inactivity_threshold_second > current_time:
                return False
        return True

    def ask_client(self, client):
        """
        ask a player if he is afk.

        :param client : b3.clients.Client
        """
        if client in self.kick_timers:
            self.verbose("%s is already in kick_timers" % client)
            return
        client.message(self.are_you_afk)
        self.console.say("%s suspected of being AFK, kicking in %ss if no answer" % (client.name, self.last_chance_delay))
        self.kick_timers[client] = Timer(self.last_chance_delay, self.kick, (client, ))
        self.kick_timers[client].start()

    def kick(self, client):
        """
        kick a player after showing a message on the server
        :param client: the player to kick
        """
        self.console.say("kicking %s: %s" % (client.name, self.kick_reason))
        client.kick(reason=self.kick_reason)

    def start_check_timer(self):
        """
        start a timer for the next check
        """
        if self.check_frequency_second > 0:
            self.check_timer = Timer(self.check_frequency_second, self.search_for_afk)
            self.check_timer.start()

    def stop_check_timer(self):
        if self.check_timer:
            self.check_timer.cancel()

    def stop_kick_timers(self):
        if self.kick_timers:
            for timer in list(self.kick_timers.values()):
                if timer:
                    timer.cancel()

    def verbose2(self, msg, *args, **kwargs):
        """
        Log a VERBOSE2 message to the main log. More "chatty" than a VERBOSE message.
        """
        self.console.verbose2('%s: %s' % (self.__class__.__name__, msg), *args, **kwargs)