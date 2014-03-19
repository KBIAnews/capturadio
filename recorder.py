#!/usr/bin/env python2.7
# -*- coding: utf_8 -*-
import sys
import os
import re
import logging
from docopt import docopt
from capturadio import Configuration, Recorder, version_string
from capturadio.rss import Audiofiles
from capturadio.util import find_configuration

logging.basicConfig(
    filename=os.path.join(Configuration.folder, 'log'),
    format='[%(asctime)s] %(levelname)-6s %(module)s::%(funcName)s:%(lineno)d: %(message)s',
    level=logging.DEBUG,
)


def show_capture(*args):
    """Usage:
    recorder show capture [--duration=<duration>] [options]

Capture a show.

Options:
    --duration,-d=<duration> Set the duration, overrides show setting

Examples:
    1. Capture an episode of the show 'nighttalk'
        recorder show capture nighttalk

    2. Capture an episode of the show 'nighttalk', but only 35 minutes
        recorder show capture nighttalk -d 35m

    """

    config = Configuration()
    if len(config.stations) == 0:
        print('No stations defined, add stations at first!')
        sys.exit(0)

    if len(config.shows) == 0:
        print('No shows defined, add shows at first!')
        sys.exit(0)
    args = args[0]
    if args[0] in config.shows:
        show = config.shows[args[0]]
        try:
            recorder = Recorder()
            recorder.capture(show)
        except Exception as e:
            print('Unable to capture recording: %s' % e)
    else:
        print('Unknown show %r' % args[0])


def config_setup(args):
    """Usage:
    recorder config setup [ -u | -p ]

Setup program settings. A new settings file is created.

Options:
    -u        Create user settings in ~/.capturadio
    -p        Crete local settings in current work directory

    """
    config = Configuration()
    config.write_config()
    config_list([])


def config_list(args):
    """Usage:
    recorder config list

Show program settings.

    """
    config = Configuration()

    for key in ['destination', 'date_pattern', 'comment_pattern', 'folder',
                'filename', 'tempdir']:
        val = config._shared_state[key]
        if key == 'comment_pattern':
            val = val.replace('\n', '\n      ')
        print u"%s: %s" % (key, val)

    for key, val in config._shared_state['feed'].items():
        print u"feed.%s: %s" % (key, val)

    show_ids = map(lambda id: id.encode('ascii'), config.shows.keys())
    station_ids = map(lambda id: id.encode('ascii'), config.stations.keys())
    print('stations: %s' % ', '.join(station_ids) if len(station_ids) else 'No stations defined')
    print('shows: %s' % ', '.join(show_ids) if len(show_ids) else 'No shows defined')


def ignore_folder(dirname, patterns=['.git', '.bzr', 'svn', '.svn', '.hg']):
    for p in patterns:
        pattern = r'.*%s%s$|.*%s%s%s.*' % (os.sep, p, os.sep, p, os.sep)
        if re.match(pattern, dirname) is not None:
            return True
    return False


def feed_update(args):
    """Usage:
    recorder feed update

Generate rss feed files.

    """
    config = Configuration()
    path = config.destination
    for dirname, dirnames, filenames in os.walk(path):
        if not ignore_folder(dirname):
            Audiofiles.process_folder(dirname, path)


def help(args):
    cmd = r'%s_%s' % (args['<command>'], args['<action>'])
    try:
        print(globals()[cmd].__doc__)
    except KeyError:
        exit("%r is not a valid command. See 'recorder help'." %
             cmd.replace('_', ' '))


def find_command(args):
    if not args['help']:
        for command in ['feed', 'config', 'show']:
            if args[command]:
                for action in ['list', 'update', 'capture', 'show', 'setup']:
                    if args[action]:
                        return r'%s_%s' % (command, action)
    return 'help'


def main(argv=None):
    """
capturadio - Capture internet radio broadcasts in mp3 encoding format.

Usage:
    recorder.py help <command> <action>
    recorder.py show capture <show>
    recorder.py config list
    recorder.py config setup
    recorder.py feed update

General Options:
    -h, --help        show this screen and exit
    --version         Show version and exit.

Commands:
    show capture      Capture an episode of a show
    config setup      Create configuration file
    config list       Show configuration values
    feed update       Update rss feed files

See 'recorder.py help <command>' for more information on a specific command."""

    args = docopt(
        main.__doc__,
        version=version_string,
        options_first=True,
        argv=argv or sys.argv[1:]
    )

    if len(sys.argv) == 1:
        sys.argv.append('--help')

    config_location = find_configuration()
    if config_location:
        Configuration.folder = os.path.dirname(config_location)
        Configuration.filename = os.path.basename(config_location)
    else:
        config = Configuration()
        config.write_config()

    try:
        cmd = find_command(args)
        method = globals()[cmd]
        assert callable(method)
    except (KeyError, AssertionError):
        exit("%r is not a valid command. See 'recorder help'." %
             cmd.replace('_', ' '))

    method(args)


if __name__ == "__main__":
    main()
