typeytypey
==========

This is a Linux CLI demo replay tool, written in Python 3.  As I've gone
to meetups around the place, I've always wondered why presenters rarely
make mistakes.  I mean, how can they be so polished in their presentations,
especially with "live" demos?

I'll let you in on a secret, they're not.

Often presenters will use demo replay tools, and I've written a prrof of
concept showing you how it can be done.

Even though this thing is fine for my personal use, I welcome patches,
bug reports etc to make this thing useful to others.  Feel free to drop me a
line at michael@the-davies.net if you want to help.

Development Installation
========================

You should run this in a venv. Do something like this:

```
$ python3 -m venv ~/venv
$ . ~/venv/bin/activate
$ pip install -U pip
$ pip install .
```

Installing a Release
====================

That's what pypi is for!

```
$ python3 -m venv ~/venv
$ . ~/venv/bin/activate
$ pip install -U pip
$ pip install typeytypey
```

Usage
=====

```
# Show us the options:
$ typeytypey --help

Usage: typeytypey [--help|--version|--make-example] <replay-file>

Supported commands in a replay file are:
  #          This is a comment
  prompt     Set the shell prompt
  cmd        Command to print
  out        Start of output to display
  endout     End of output to display
  wait       <seconds> before proceeding
  clear      Clear the screen
  return     Print an empty prompt
  start      Display start message and delay <seconds>
  end        Suppress input and wait <seconds>

# Check out what version we're running
$ typeytypey --version
typeytypey version typeytypey 0.1.0
Copyright (C) 2019 Michael Davies <michael@the-davies.net>

# Generate a sample replay file
$ typeytypey --make-example
Writing "/tmp/typeytypey.replay" as an example replay file

# Run the replay file we just created
$ typeytypey /tmp/typeytypey.replay
```

And that's about it.  Enjoy!

