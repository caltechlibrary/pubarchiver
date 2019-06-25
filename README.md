Microarchiver<img width="12%" align="right" src=".graphics/microarchiver-logo.svg">
=======

A program to create archives of articles from [microPublication.org](https://www.micropublication.org) for sending to [Portico](https://www.portico.org).


*Authors*:      [Michael Hucka](http://github.com/mhucka), [Tom Morrell](https://github.com/tmorrell)<br>
*Repository*:   [https://github.com/caltechlibrary/microarchiver](https://github.com/caltechlibrary/microarchiver)<br>
*License*:      BSD/MIT derivative &ndash; see the [LICENSE](LICENSE) file for more information

[![License](https://img.shields.io/badge/License-BSD%203--Clause-blue.svg?style=flat-square)](https://choosealicense.com/licenses/bsd-3-clause)
[![Python](https://img.shields.io/badge/Python-3.4+-brightgreen.svg?style=flat-square)](http://shields.io)
[![Latest release](https://img.shields.io/badge/Latest_release-1.0.0-b44e88.svg?style=flat-square)](http://shields.io)


Table of Contents
-----------------
* [Introduction](#-introduction)
* [Installation](#-installation)
* [Usage](#︎-usage)
* [Known issues and limitations](#-known-issues-and-limitations)
* [Getting help and support](#-getting-help-and-support)
* [Contributing](#-contributing)
* [License](#︎-license)
* [Authors and history](#-authors-and-history)
* [Acknowledgments](#︎-acknowledgments)


☀ Introduction
-----------------------------

The Caltech Library is the publisher of the online journal [microPublication](https://www.micropublication.org) and provides services to the journal that include archiving the journal in a dark archive (specifically, [Portico](https://www.portico.org)).  The archiving process involves pulling down articles from [microPublication](https://www.micropublication.org) and packaging them up in a format suitable for sending to Portico.  The programs in this repository are used to automate this process.


✺ Installation
-------------

You can download the source code for Microarchiver and run the programs using a Python&nbsp;3 interpreter on macOS, Windows or Linux.  The following is probably the simplest and most direct way to install this software on your computer:
```sh
sudo python3 -m pip install git+https://github.com/caltechlibrary/microarchiver.git --upgrade
```

Alternatively, you can clone this GitHub repository and then run `setup.py`:
```sh
git clone https://github.com/caltechlibrary/microarchiver.git
cd microarchiver
sudo python3 -m pip install . --upgrade
```


▶︎ Usage
-------

Microarchiver is a command-line program.  The installation process should put a program named `microarchiver` in a location normally searched by your shell interpreter.  For help with usage at any time, run `microarchiver` with the option `-h` (or `/h` on Windows).

```bash
microarchiver -h
```

### _Basic usage_

The simplest use of `microarchiver` involves running it without any arguments.  This will make it will contact [micropublication.org](http://micropublication.org) to get a list of current articles, and create an archive of all the articles in a subdirectory of the current directory.

```bash
microarchiver
```

If given the argument `-d` (or `/d` on Windows), the output will be written to the directory named after the `-d`.  For example:

```bash
microarchiver -d /tmp/micropublication-archive
```

The following is a screen recording of an actual run of `microarchiver`:

<p align="center">
  <a href="https://asciinema.org/a/KprJnt3xcfhKn45xZL3jlvXCx"><img src=".graphics/microarchiver-asciinema.png" alt="Screencast of simple microarchiver demo"></a>
</p>

### _Additional command-line arguments_

If given the argument `-a` (or `/a` on Windows) followed by a file name, the given file will be read instead instead of getting the list from the server. The contents of the file must be in the same XML format as the list obtain from micropublication.org.

As it works, microarchiver writes information to the terminal about the archives it puts into the archive, including whether any problems are encountered. To save this info to a file, use the argument `-r` (or `/r` on Windows).

The output directory will also be put into a single-file archive in [ZIP](https://en.wikipedia.org/wiki/Zip_(file_format)) format unless the argument `-A` (or `/A` on Windows) is given to prevent creation of the compressed archive file.

Microarchiver will print informational messages as it works. To reduce messages to only warnings and errors, use the argument `-q` (or `/q` on Windows). Also, output is color-coded by default unless the `-C` argument (or `/C` on Windows) is given; this argument can be helpful if the color control signals create problems for your terminal emulator.

If given the argument `-n` (or `/n` on Windows), microarchiver will _only_ display a list of articles it will archive and stop short of creating the archive. This is useful to see what would be produced without actually doing it.


### _Summary of command-line options_


The following table summarizes all the command line options available. (Note: on Windows computers, `/` must be used as the prefix character instead of `-`):

| Short   | Long&nbsp;form&nbsp;opt | Meaning | Default |
|---------|-------------------|----------------------|---------|
| `-a`_A_ | `--articles`_A_   | Get list of articles from file _A_ | Get list from server |
| `-d`_D_ | `--dest-dir`_D_   | Write output in directory _D_ | Write in current dir |
| `-r`_R_ | `--report`_R_     | Write list of article & results in file _R_ | Don't write a report |
| `-n`    | `--dry-run`       | Only print what would be obtained | Do the work |
| `-q`    | `--quiet`         | Don't print info messages while working | Be chatty while working |
| `-A`    | `--no-archive`    | Don't put output into one ZIP archive | ZIP up the output |
| `-C`    | `--no-color`      | Don't color-code the output | Use colors in the terminal output |
| `-V`    | `--version`       | Print program version info and exit | Do other actions instead |
| `-Z`    | `--debug`         | Debugging mode | Normal mode |


⚑ Known issues and limitations
-------------------------------

Currently, the only way to indicate that a subset of articles should be obtained from micropublication.org is to use the argument `-a` in combination with a file that contains the list of desired articles.


⁇ Getting help and support
--------------------------

If you find an issue, please submit it in [the GitHub issue tracker](https://github.com/caltechlibrary/microarchiver/issues) for this repository.


♬ Contributing
-------------

We would be happy to receive your help and participation with enhancing `microarchiver`!  Please visit the [guidelines for contributing](CONTRIBUTING.md) for some tips on getting started.


☮︎ License
----------

Copyright &copy; 2019, Caltech.  This software is freely distributed under a BSD/MIT type license.  Please see the [LICENSE](LICENSE) file for more information.


❡ Authors and history
--------------------

[Tom Morrell](https://github.com/tmorrell) developed the original algorithm for extracting metadata from DataCite and creating XML files for use with Portico submissions of micropublication.org articles.  [Mike Hucka](https://github.com/mhucka) created the much-expanded second version now known as `microarchiver`.


♥︎ Acknowledgments
-----------------------

The [vector artwork](https://thenounproject.com/search/?q=archive&i=158401) used as a starting point for the logo for this repository was created by [Thomas Helbig](https://thenounproject.com/dergraph/) for the [Noun Project](https://thenounproject.com).  It is licensed under the Creative Commons [Attribution 3.0 Unported](https://creativecommons.org/licenses/by/3.0/deed.en) license.  The vector graphics was modified by Mike Hucka to change the color.

_Microarchiver_ makes use of numerous open-source packages, without which it would have been effectively impossible to develop _Microarchiver_ with the resources we had.  We want to acknowledge this debt.  In alphabetical order, the packages are:

* [colorama](https://github.com/tartley/colorama) &ndash; makes ANSI escape character sequences work under MS Windows terminals
* [humanize](https://github.com/jmoiron/humanize) &ndash; make numbers more easily readable by humans
* [ipdb](https://github.com/gotcha/ipdb) &ndash; the IPython debugger
* [lxml](https://lxml.de) &ndash; an XML parsing library for Python
* [plac](http://micheles.github.io/plac/) &ndash; a command line argument parser
* [recordclass](https://github.com/intellimath/recordclass) &ndash; a mutable version of Python named tuples
* [requests](http://docs.python-requests.org) &ndash; an HTTP library for Python
* [setuptools](https://github.com/pypa/setuptools) &ndash; library for `setup.py`
* [termcolor](https://pypi.org/project/termcolor/) &ndash; ANSI color formatting for output in terminal
* [urllib3](https://urllib3.readthedocs.io/en/latest/) &ndash; a powerful HTTP library for Python
* [xmltodict](https://github.com/martinblech/xmltodict) &ndash; a module to make working with XML feel like working with JSON

Finally, we are grateful for computing &amp; institutional resources made available by the California Institute of Technology.
    
<div align="center">
  <a href="https://www.caltech.edu">
    <img width="100" height="100" src=".graphics/caltech-round.svg">
  </a>
</div>
