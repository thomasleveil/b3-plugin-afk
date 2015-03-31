# -*- encoding: utf-8 -*-
from textwrap import dedent
from mock import Mock
from afk.tests import *


@pytest.mark.skipif(not os.path.exists(DEFAULT_PLUGIN_CONFIG_FILE), reason="Could not find default plugin config file %r" % DEFAULT_PLUGIN_CONFIG_FILE)
def test_default_conf(console):
    plugin = plugin_maker(console, DEFAULT_PLUGIN_CONFIG_FILE)
    plugin.onLoadConfig()
    assert 1 == plugin.min_ingame_humans
    assert 3 == plugin.consecutive_deaths_threshold
    assert 50 == plugin.inactivity_threshold_second
    assert 20 == plugin.last_chance_delay
    assert "AFK for too long on this server" == plugin.kick_reason
    assert "Are you AFK?" == plugin.are_you_afk


def test_empty_conf(console):
    plugin = plugin_maker_ini(console,  dedent(""""""))
    plugin.onLoadConfig()
    assert 1 == plugin.min_ingame_humans
    assert 3 == plugin.consecutive_deaths_threshold
    assert 50 == plugin.inactivity_threshold_second
    assert 20 == plugin.last_chance_delay
    assert "AFK for too long on this server" == plugin.kick_reason
    assert "Are you AFK?" == plugin.are_you_afk


def test_bad_values(console):
    plugin = plugin_maker_ini(console, dedent("""
        [settings]
        min_ingame_humans: mlkj
        consecutive_deaths_threshold: f00
        inactivity_threshold: bar
        last_chance_delay: f00
        kick_reason:
        are_you_afk:
        """))
    plugin.onLoadConfig()
    assert 1 == plugin.min_ingame_humans
    assert 3 == plugin.consecutive_deaths_threshold
    assert 30 == plugin.inactivity_threshold_second
    assert 20 == plugin.last_chance_delay
    assert "AFK for too long on this server" == plugin.kick_reason
    assert "Are you AFK?" == plugin.are_you_afk


def test_min_ingame_humans(console):
    plugin = plugin_maker_ini(console, dedent("""
        [settings]
        min_ingame_humans: 3
        """))
    plugin.onLoadConfig()
    assert 3 == plugin.min_ingame_humans


def test_min_ingame_humans_too_low(console):
    plugin = plugin_maker_ini(console, dedent("""
        [settings]
        min_ingame_humans: -1
        """))
    plugin.onLoadConfig()
    assert 0 == plugin.min_ingame_humans


def test_consecutive_deaths_threshold(console):
    plugin = plugin_maker_ini(console, dedent("""
        [settings]
        consecutive_deaths_threshold: 2
        """))
    plugin.onLoadConfig()
    assert 2 == plugin.consecutive_deaths_threshold


def test_inactivity_threshold_too_low(console):
    plugin = plugin_maker_ini(console, dedent("""
        [settings]
        inactivity_threshold: 5s
        """))
    plugin.onLoadConfig()
    assert 30 == plugin.inactivity_threshold_second


def test_inactivity_threshold_minute(console):
    plugin = plugin_maker_ini(console, dedent("""
        [settings]
        inactivity_threshold: 1m
        """))
    plugin.onLoadConfig()
    assert 60 == plugin.inactivity_threshold_second


def test_last_chance_delay(console):
    plugin = plugin_maker_ini(console, dedent("""
        [settings]
        last_chance_delay: 34
        """))
    plugin.onLoadConfig()
    assert 34 == plugin.last_chance_delay


def test_last_chance_delay_missing(console):
    plugin = plugin_maker_ini(console, dedent("""
        [settings]
        """))
    plugin.onLoadConfig()
    assert 20 == plugin.last_chance_delay


def test_last_chance_delay_empty(console):
    plugin = plugin_maker_ini(console, dedent("""
        [settings]
        last_chance_delay:
        """))
    plugin.onLoadConfig()
    assert 20 == plugin.last_chance_delay


def test_last_chance_delay_bad_value(console):
    plugin = plugin_maker_ini(console, dedent("""
        [settings]
        last_chance_delay: f00
        """))
    plugin.onLoadConfig()
    assert 20 == plugin.last_chance_delay


def test_last_chance_delay_too_low(console):
    plugin = plugin_maker_ini(console, dedent("""
        [settings]
        last_chance_delay: 14
        """))
    plugin.onLoadConfig()
    assert 15 == plugin.last_chance_delay


def test_last_chance_delay_too_high(console):
    plugin = plugin_maker_ini(console, dedent("""
        [settings]
        last_chance_delay: 61
        """))
    plugin.onLoadConfig()
    assert 60 == plugin.last_chance_delay


def test_immunity_level_missing(console):
    plugin = plugin_maker_ini(console, dedent("""
        [settings]
        """))
    plugin.onLoadConfig()
    assert 100 == plugin.immunity_level


def test_immunity_level_bad_value(console):
    plugin = plugin_maker_ini(console, dedent("""
        [settings]
        immunity_level: f00
        """))
    plugin.onLoadConfig()
    assert 100 == plugin.immunity_level


def test_immunity_level_nominal(console):
    plugin = plugin_maker_ini(console, dedent("""
        [settings]
        immunity_level: 40
        """))
    plugin.onLoadConfig()
    assert 40 == plugin.immunity_level

