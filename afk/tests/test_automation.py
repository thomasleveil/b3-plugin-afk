# -*- encoding: utf-8 -*-
from textwrap import dedent
from time import sleep
from afk.tests import *
from mock import call, Mock
from b3 import TEAM_RED, TEAM_SPEC


@pytest.yield_fixture
def plugin(console):
    p = plugin_maker_ini(console, dedent("""
        [settings]
        check_frequency: 10s
        inactivity_threshold: 30s
        kick_reason: AFK for too long on this server
        are_you_afk: Are you AFK?
    """))
    p.original_start_check_timer = p.start_check_timer
    p.start_check_timer = Mock()
    p.onLoadConfig()
    p.onStartup()
    yield p
    p.disable()


def test_check_client_on_spectator(plugin, joe):
    # GIVEN
    plugin.ask_client = Mock()
    joe.team = TEAM_SPEC
    joe.connects(1)
    # WHEN
    plugin.check_client(joe)
    # THEN
    assert 0 == plugin.ask_client.call_count


def test_check_client_active(plugin, joe):
    # GIVEN
    plugin.ask_client = Mock()
    joe.team = TEAM_RED
    joe.connects(1)
    # WHEN
    joe.says("hi")
    plugin.check_client(joe)
    # THEN
    assert 0 == plugin.ask_client.call_count


def test_check_client_inactive(plugin, joe):
    # GIVEN
    plugin.inactivity_threshold_second = 0
    plugin.ask_client = Mock()
    joe.team = TEAM_RED
    joe.connects(1)
    # WHEN
    joe.says("hi")
    sleep(.1)
    plugin.check_client(joe)
    # THEN
    assert [call(joe)] == plugin.ask_client.mock_calls


def test_ask(plugin, joe):
    # GIVEN
    joe.message = Mock()
    joe.team = TEAM_RED
    joe.connects(1)
    # WHEN
    plugin.search_for_afk()
    # THEN
    assert [call('Are you AFK?')] == joe.message.mock_calls


def test_ask_and_no_response(plugin, joe):
    # GIVEN
    plugin.last_chance_delay = .1
    joe.message = Mock()
    joe.kick = Mock()
    joe.team = TEAM_RED
    joe.connects(1)
    # WHEN
    plugin.search_for_afk()
    sleep(.2)
    # THEN
    assert [call('Are you AFK?')] == joe.message.mock_calls
    assert [call(reason='AFK for too long on this server')] == joe.kick.mock_calls


def test_ask_and_response(plugin, joe):
    # GIVEN
    plugin.last_chance_delay = .4
    joe.message = Mock()
    joe.kick = Mock()
    joe.team = TEAM_RED
    joe.connects(1)
    # WHEN
    plugin.search_for_afk()
    sleep(.2)
    # THEN
    assert [call('Are you AFK?')] == joe.message.mock_calls
    # WHEN
    joe.says("I'm here")
    sleep(.5)
    # THEN
    assert 0 == joe.kick.call_count


def test_ask_and_make_kill(plugin, joe, jack):
    # GIVEN
    plugin.last_chance_delay = .4
    joe.message = Mock()
    joe.kick = Mock()
    joe.team = TEAM_RED
    joe.connects(1)
    jack.connects(2)
    # WHEN
    plugin.search_for_afk()
    sleep(.2)
    # THEN
    assert [call('Are you AFK?')] == joe.message.mock_calls
    # WHEN
    joe.kills(jack)
    sleep(.5)
    # THEN
    assert 0 == joe.kick.call_count


def test_kick(plugin, joe):
    # GIVEN
    joe.kick = Mock()
    # WHEN
    plugin.kick(joe)
    # THEN
    assert [call(reason='AFK for too long on this server')] == joe.kick.mock_calls


def test_check_timer(plugin):
    # GIVEN
    plugin.check_frequency_second = .2
    plugin.search_for_afk = Mock()
    # WHEN
    plugin.original_start_check_timer()
    sleep(.21)
    # THEN
    assert 1 == plugin.search_for_afk.call_count
    # WHEN
    plugin.original_start_check_timer()
    sleep(.21)
    # THEN
    assert 2 == plugin.search_for_afk.call_count


def test_check_timer_disabled(plugin):
    # GIVEN
    plugin.check_frequency_second = 0
    plugin.search_for_afk = Mock()
    # WHEN
    plugin.original_start_check_timer()
    sleep(.1)
    # THEN
    assert 0 == plugin.search_for_afk.call_count

