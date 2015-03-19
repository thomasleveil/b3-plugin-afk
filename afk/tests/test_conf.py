# -*- encoding: utf-8 -*-
from textwrap import dedent
from mock import Mock
from afk.tests import *


@pytest.mark.skipif(not os.path.exists(DEFAULT_PLUGIN_CONFIG_FILE), reason="Could not find default plugin config file %r" % DEFAULT_PLUGIN_CONFIG_FILE)
def test_default_conf(console):
    plugin = plugin_maker(console, DEFAULT_PLUGIN_CONFIG_FILE)
    plugin.start_check_timer = Mock()
    plugin.onLoadConfig()
    assert 10 == plugin.check_frequency_second
    assert 30 == plugin.inactivity_threshold_second
    assert "AFK for too long on this server" == plugin.kick_reason
    assert "Are you AFK?" == plugin.are_you_afk


def test_empty_conf(console):
    plugin = plugin_maker_ini(console,  dedent(""""""))
    plugin.start_check_timer = Mock()
    plugin.onLoadConfig()
    assert 0 == plugin.check_frequency_second
    assert 0 == plugin.inactivity_threshold_second
    assert "AFK for too long on this server" == plugin.kick_reason
    assert "Are you AFK?" == plugin.are_you_afk


def test_bad_values(console):
    plugin = plugin_maker_ini(console, dedent("""
        [settings]
        check_frequency: f00
        inactivity_threshold: bar
        kick_reason:
        are_you_afk:
        """))
    plugin.start_check_timer = Mock()
    plugin.onLoadConfig()
    assert 0 == plugin.check_frequency_second
    assert 30 == plugin.inactivity_threshold_second
    assert "AFK for too long on this server" == plugin.kick_reason
    assert "Are you AFK?" == plugin.are_you_afk


def test_check_frequency(console):
    plugin = plugin_maker_ini(console, dedent("""
        [settings]
        check_frequency: 5m
        """))
    plugin.start_check_timer = Mock()
    plugin.onLoadConfig()
    assert 300 == plugin.check_frequency_second


def test_inactivity_threshold(console):
    plugin = plugin_maker_ini(console, dedent("""
        [settings]
        inactivity_threshold: 5s
        """))
    plugin.start_check_timer = Mock()
    plugin.onLoadConfig()
    assert 30 == plugin.inactivity_threshold_second

