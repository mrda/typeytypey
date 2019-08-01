#!/usr/bin/env py3
#
# typeytypey.py - command-line demo replay tool
#                 Inspired by https://github.com/paxtonhare/demo-magic
#                 and watching Geoffrey Bennett do this for years
#                 at LinuxSA, and never quite knowing whether his demos
#                 were live or staged :-)
#
# Copyright (C) 2019 Michael Davies <michael@the-davies.net>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
# Or try here: http://www.fsf.org/copyleft/gpl.html

import fcntl
import getopt
import os
import pkg_resources
import sys
import time
import termios
import tty


valid_opts = ['help', 'version', 'make-example']

debug = False


class raw(object):
    def __init__(self, stream):
        self.stream = stream
        self.fd = self.stream.fileno()

    def __enter__(self):
        self.original_stty = termios.tcgetattr(self.stream)
        tty.setcbreak(self.stream)

    def __exit__(self, type, value, traceback):
        termios.tcsetattr(self.stream, termios.TCSANOW, self.original_stty)


class nonblocking(object):
    def __init__(self, stream):
        self.stream = stream
        self.fd = self.stream.fileno()

    def __enter__(self):
        self.orig_fl = fcntl.fcntl(self.fd, fcntl.F_GETFL)
        fcntl.fcntl(self.fd, fcntl.F_SETFL, self.orig_fl | os.O_NONBLOCK)

    def __exit__(self, *args):
        fcntl.fcntl(self.fd, fcntl.F_SETFL, self.orig_fl)


class ReplayFileReader:

    commands = {
        "#":      {"description": "This is a comment", "jump": None},
        "prompt": {"description": "Set the shell prompt", "jump": None},
        "cmd":    {"description": "Command to print", "jump": None},
        "out":    {"description": "Start of output to display", "jump": None},
        "endout": {"description": "End of output to display", "jump": None},
        "wait":   {"description": "<seconds> before proceeding", "jump": None},
        "clear":  {"description": "Clear the screen", "jump": None},
        "return": {"description": "Print an empty prompt", "jump": None},
        "start":  {"description": "Display start message and delay <seconds>",
                   "jump": None},
        "end":    {"description": "Suppress input and wait <seconds>",
                   "jump": None},
    }

    def __init__(self, filename):
        ReplayFileReader.commands['#']['jump'] = self.process_comment
        ReplayFileReader.commands['prompt']['jump'] = self.process_prompt
        ReplayFileReader.commands['cmd']['jump'] = self.process_cmd
        ReplayFileReader.commands['out']['jump'] = self.process_out
        ReplayFileReader.commands['endout']['jump'] = self.process_endout
        ReplayFileReader.commands['wait']['jump'] = self.process_wait
        ReplayFileReader.commands['clear']['jump'] = self.process_clear
        ReplayFileReader.commands['return']['jump'] = self.process_return
        ReplayFileReader.commands['start']['jump'] = self.process_start
        ReplayFileReader.commands['end']['jump'] = self.process_end
        self.filename = filename
        self.fd = open(filename, 'r')

    def display_file_format():
        sys.stderr.write("\nSupported commands in a replay file are:\n")
        for cmd in ReplayFileReader.commands:
            sys.stderr.write("  {:<10} {}\n".format
                             (cmd,
                              ReplayFileReader.commands[cmd]['description']))

    def process_comment(self, params):
        if debug:
            print("#")

    def process_clear(self, params):
        if debug:
            print("Clearing the screen")
        os.system('cls' if os.name == 'nt' else 'clear')

    def snaffle_keypress(self):
        # Wait for keypress
        with raw(sys.stdin):
            with nonblocking(sys.stdin):
                while True:
                    if sys.stdin.read(1):
                        break
                    time.sleep(0.1)

    def process_start(self, params):
        if debug:
            print("Starting a replay")
        print("Starting a replay in {} seconds".format(params))
        sys.stderr.write("Press <CTRL-C> to exit...\n")
        self.sleep_ignoring_input(int(params))
        os.system('cls' if os.name == 'nt' else 'clear')

    def process_end(self, params):
        if debug:
            print("Finishing the replay")
        print(self.prompt, end="")
        sys.stdout.flush()
        self.snaffle_keypress()
        # TODO(mrda): Ensure params is an integer
        self.sleep_ignoring_input(int(params))
        print()
        sys.stdout.flush()

    def process_prompt(self, params):
        if debug:
            print("Setting prompt")
        end = ""
        # Prompts should have a space on the end
        if params[:-1] != ' ':
            end = ' '
        self.prompt = params + end

    def process_return(self, params):
        if debug:
            print("Printing a prompt")
        print(self.prompt, end="")
        sys.stdout.flush()
        self.snaffle_keypress()
        print()
        sys.stdout.flush()

    def process_cmd(self, params):
        if debug:
            print("Command to execute \"{}\"".format(params))
        print(self.prompt, end="")
        sys.stdout.flush()
        self.fake_command(params)

    def process_out(self, params):
        if debug:
            print(">>>Starting output")
        self.in_output = True

    def process_endout(self, params):
        if debug:
            print("<<< Ending output")
        self.in_output = False

    def process_wait(self, params):
        if debug:
            print("Time to wait")
        # TODO(mrda): Ensure params is an integer
        self.sleep_ignoring_input(int(params))

    def process_next_command(self):
        self.in_output = False
        for line in self.fd:
            line = line.strip()
            if line == "":
                if debug:
                    print("Empty line")
                continue

            tokens = line.split(" ", 1)
            cmd = tokens[0]
            params = None

            if len(tokens) == 2:
                # Only some commands have params
                params = tokens[1]

            try:
                command = ReplayFileReader.commands[cmd]
                command['jump'](params)
            except KeyError:
                if self.in_output:
                    print(line)
                else:
                    print("*** Unknown cmd \"{}\"".format(line))
                    exit(2)

    def sleep_ignoring_input(self, sec):
        """Implement my own sleep, ignoring user input while sleeping"""
        buzzer = int(time.time()) + sec
        with raw(sys.stdin):
            with nonblocking(sys.stdin):
                while True:
                    c = sys.stdin.read(1)
                    if time.time() >= buzzer:
                        break

    def fake_command(self, st):
        if debug:
            print("Faking this command: \"{}\"".format(st))

        # Grab 'st' chars worth of output & print as if it were being typed
        with raw(sys.stdin):
            with nonblocking(sys.stdin):
                for c in st:
                    while True:
                        k = sys.stdin.read(1)
                        if k:
                            print(c, end="")
                            sys.stdout.flush()
                            if debug:
                                print(" keycode is {}".format(ord(k)))
                            break
                        time.sleep(0.1)
                print()


def make_example(filename):
    print("Writing \"{}\" as an example replay file".format(filename))
    with open(filename, "w") as w:
        w.write("""\
#
# This is an example typeytypey replay file
# Author: Michael Davies <michael@the-davies.net>
# See https://github.com/mrda/junkcode/blob/master/typeytypey.py
#
start 5

prompt [mrda@xenon ~]$
return
return

cmd hostane
out
bash: hostane: command not found...
endout
cmd hostname
out
xenon
endout
return

cmd cd src/junkcode
prompt [mrda@xenon junkcode]$
# return

cmd ls -1 s*.py
wait 5
out
secretary.py*
select-name.py*
simple_text_encoder.py*
ski-ramp.py*
sleep_sort.py*
speechinator.py*
sudoku.py*
endout

cmd md5sum sudoku.py
out
199d21127b0b6a8dc0612402e0d87803  sudoku.py
endout

# Note that it's good to capture input at the end of your replay script
# for a certain time period to make sure you're not caught out by typing
# too many characters :-)
end 10
""")


def display_version():
    try:
        vers = pkg_resources.require("typeytypey")[0]
    except pkg_resources.DistributionNotFound:
        vers = "UNKNOWN-VERSION"

    sys.stderr.write("{0} version {1}\n".format(os.path.basename(sys.argv[0]),
                     vers))
    sys.stderr.write("Copyright (C) 2019 Michael Davies <michael@the-davies.net>\n")  # noqa


def exit_with_usage(code=1):
    sys.stderr.write("Usage: {0} [{1}] <replay-file>\n"
                     .format(os.path.basename(sys.argv[0]),
                             '|'.join('--'+opt for opt in valid_opts)))
    ReplayFileReader.display_file_format()
    sys.exit(code)


def main():
    # Allow debugging from environment variable
    if os.getenv('DEBUG', False) in ['True', 'TRUE', 'true', '1', 1]:
        sys.stderr.write("Printing bug out because DEBUG env variable set\n")
        debug = True

    try:
        opts, args = getopt.getopt(sys.argv[1:], '', valid_opts)
    except getopt.error:
        exit_with_usage(0)

    opt_flags = [flag for (flag, val) in opts]
    for opt in opt_flags:
        if opt == '--help':
            exit_with_usage(0)
        elif opt == '--make-example':
            make_example("/tmp/typeytypey.replay")
            sys.exit(0)
        elif opt == '--version':
            display_version()
            sys.exit(0)

    if len(sys.argv) != 2:
        exit_with_usage()

    replay_file = ReplayFileReader(sys.argv[1])
    while(replay_file.process_next_command()):
        pass
    print()


if __name__ == '__main__':
    main()
