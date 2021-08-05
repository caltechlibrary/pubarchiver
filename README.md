PubArchiver<img width="12%" align="right" src="https://github.com/caltechlibrary/pubarchiver/blob/main/.graphics/pubarchiver-logo.png?raw=true">
=======

A program that creates archives of articles from specific journal sites (currently [microPublication](https://www.micropublication.org) and [Prompt](https://thepromptjournal.com/index.php/prompt)) for sending to [Portico](https://www.portico.org) and [PMC](https://www.ncbi.nlm.nih.gov/pmc/).

*Authors*:      [Michael Hucka](http://github.com/mhucka), [Tom Morrell](https://github.com/tmorrell)<br>
*Repository*:   [https://github.com/caltechlibrary/pubarchiver](https://github.com/caltechlibrary/pubarchiver)<br>
*License*:      BSD/MIT derivative &ndash; see the [LICENSE](LICENSE) file for more information

[![License](https://img.shields.io/badge/License-BSD%203--Clause-yellow.svg?style=flat-square)](https://choosealicense.com/licenses/bsd-3-clause)
[![Python](https://img.shields.io/badge/Python-3.5+-brightgreen.svg?style=flat-square)](https://www.python.org/downloads/release/python-350/)
[![Latest release](https://img.shields.io/github/v/release/caltechlibrary/pubarchiver.svg?style=flat-square&color=b44e88)](https://github.com/caltechlibrary/pubarchiver/releases)
[![DOI](https://img.shields.io/badge/dynamic/json.svg?label=DOI&style=flat-square&colorA=gray&colorB=navy&query=$.metadata.doi&uri=https://data.caltech.edu/api/record/1982)](https://data.caltech.edu/records/1982)
[![PyPI](https://img.shields.io/pypi/v/pubarchiver.svg?style=flat-square&color=red)](https://pypi.org/project/pubarchiver/)


Table of Contents
-----------------
* [Introduction](#-introduction)
* [Installation](#-installation)
* [Usage](#︎-usage)
* [Getting help and support](#-getting-help-and-support)
* [Contributing](#-contributing)
* [License](#︎-license)
* [Authors and history](#-authors-and-history)
* [Acknowledgments](#︎-acknowledgments)


☀ Introduction
-----------------------------

The Caltech Library is the publisher of a few academic journals and provides services for them. The services include archiving in a dark archive (specifically, [Portico](https://www.portico.org)) as well as submitting articles to [PMC](https://www.ncbi.nlm.nih.gov/pmc/).  The archiving process involves pulling down articles from the journals and packaging them up in a format suitable for sending to the archives.  PubArchiver is a program to help automate this process.


✺ Installation
-------------

On **Linux**, **macOS**, and **Windows** operating systems, you should be able to install PubArchiver directly from the GitHub repository using [pip](https://pip.pypa.io/en/stable/installing/).  If you don't have the `pip` package or are uncertain if you do, first run the following command in a terminal command line interpreter: 
```
sudo python3 -m ensurepip
```

Then, install this software by running the following command on your computer:
```sh
python3 -m pip install git+https://github.com/caltechlibrary/pubarchiver.git 
```

Alternatively, you can clone this GitHub repository and then run `setup.py`:
```sh
git clone https://github.com/caltechlibrary/pubarchiver.git
cd pubarchiver
python3 -m pip install .
```


▶︎ Usage
-------

PubArchiver is a command-line program.  The installation process should put a program named `pubarchiver` in a location normally searched by your shell interpreter.  For help with usage at any time, run `pubarchiver` with the option `-h` (or `/h` on Windows).

```bash
pubarchiver -h
```

The following is a screen recording of an actual run of `pubarchiver`:

<p align="center">
  <a href="https://asciinema.org/a/260298"><img src="https://github.com/caltechlibrary/pubarchiver/blob/main/.graphics/pubarchiver-asciinema.png?raw=true" alt="Screencast of simple pubarchiver demo"></a>
</p>


### _Basic usage_

The journal whose articles are to be archived must be indicated using the required option `-j` (or `/j` on Windows). To see a list of supported journals, you can use `-j list` (or `/j list` on Windows) like this:

```bash
pubarchiver -j list
```

If not given any additional options besides a `-j` option to select the journal, `pubarchiver` will proceed to contact the journal website as well as either [DataCite](https://datacite.org) or [Crossref](https://www.crossref.org), and create an archive containing articles and their metadata for all articles published to date by the journal.  The options below can be used to select articles and influence other `pubarchiver` behaviors.


### _Printing information without doing anything_

The option `-l` (or `/l` on Windows) can be used to obtain a list of all DOIs for all articles published by the selected journal. When `-l` is used, `pubarchiver` prints the list to the terminal and exits without doing further work. This can be useful if you intend to use the `-f` option discussed below.

If given the option `-p` (or `/p` on Windows), `pubarchiver` will _only_ print a list of articles it will archive and stop short of creating the archive. This is useful to see what would be produced without actually doing it.  Note, however, that because it does not attempt to download the articles and associated files, it cannot report errors that _might_ occur when actually creating an archive.  Consequently, do not use the output of `-p` as a prediction of eventual success or failure.


### _Selecting the archive format and archive output location_

The value supplied after the option `-d` (or `/d` on Windows) can be used to tell `pubarchiver` the intended destination where the archive will be sent.  The option changes the structure and content of the archive created by `pubarchiver`. The possible alternatives are `portico` and `pmc`. Portico is assumed to be the default destination if no `-d` option is given. 

By default, `pubarchiver` will write its output to a new subdirectory it creates in the directory from which `pubarchiver` is being run. The option `-o` (or `/o` on Windows) can be used to select a different location. For example,

```bash
pubarchiver -j micropublication -o /tmp/micropublication-archive
```

The materials for each article will be written to an individual subdirectory named after the DOI of the article.  The output for each article will consist of an XML metadata file describing the article, the article itself in PDF format, and (if the journal provides [JATS](https://jats.nlm.nih.gov)) a subdirectory named `jats` containing the article in JATS XML format along with any image that may appear in the article.  The image is always converted to uncompressed TIFF format, because it is considered a good preservation format. The PMC structure follows the _naming and delivery_ specifications defined at https://www.ncbi.nlm.nih.gov/pmc/pub/filespec-delivery/.

Unless the option `-Z` (or `/Z` on Windows) is given, the output will be archived in [ZIP](https://en.wikipedia.org/wiki/Zip_(file_format)) format.  If the output structure (as determine by the `-d` option) is being generated for PMC, each article will be put into its own individual ZIP archive; else, the default action is to put the collected output of all articles into a single ZIP archive file.  The option `-Z` makes `pubarchiver` leave the output unarchived in the directory determined by the `-o` option.


### _Selecting a subset of articles_

If the option `-a` is given, `pubarchiver` will download only articles whose publication dates are _after_ the given date.  Valid date descriptors are those accepted by the Python [dateparser](https://pypi.org/project/dateparser/) library.  Make sure to enclose descriptions within single or double quotes.  Examples:

```
  pubarchiver -a "2014-08-29"   ....
  pubarchiver -a "12 Dec 2014"  ....
  pubarchiver -a "July 4, 2013"  ....
  pubarchiver -a "2 weeks ago"  ....
```

The option `-f` (or `/f` on Windows) can be used to tell `pubarchiver` to read a file containing DOIs and only fetch those particular articles instead of asking the journal for all articles.  The format of the file indicated after the `-f` option must be a simple text file containing one DOI per line.

The selection by date performed by the `-a` option is performed after reading the list of articles using the `-f` option if present, and thus can be used to filter by date the articles whose DOIs are provided.


### _Writing a report_

As it works, `pubarchiver` writes information to the terminal about the articles it puts into the archive, including whether any problems are encountered.  To save this information to a file, use the option `-r` (or `/r` on Windows), which will make `pubarchiver` write a report file.  By default, the format of the report file is [CSV](https://en.wikipedia.org/wiki/Comma-separated_values); the option `-s` (`/s` on Windows) can be used to select `csv` or `html` (or both) as the format.  The title of the report will be based on the current date, unless the option `-t` (or `/t` on Windows) is used to supply a different title.


### _Additional command-line options_

When `pubarchiver` downloads the JATS XML version of articles from the journal site, it will by default validate the XML content against the JATS DTD.  To skip the XML validation step, use the option `-X` (`/X` on Windows).

`pubarchiver` will print informational messages as it works. To reduce messages to only warnings and errors, use the option `-q` (or `/q` on Windows). Also, output is color-coded by default unless the `-C` option (or `/C` on Windows) is given; this option can be helpful if the color control sequences create problems for your terminal emulator.

If given the `-@` option (`/@` on Windows), this program will output a detailed real-time trace of what it is doing.  The output will be written to the given destination, which can be a dash character (`-`) to indicate console output, or a file path.

If given the `-V` option (`/V` on Windows), this program will print version information and exit without doing anything else.


### Return values

This program exits with a return code of `0` if no problems are encountered while fetching data from the server.  It returns a nonzero value otherwise, following conventions for use in shells such as bash which only understand return code values of `0` to `255`.  If no network is detected, it returns a value of 1; if it is interrupted (e.g., using `ctrl-c`) it returns a value of `2`; if it encounters a fatal error, it returns a value of `3`.  If it encounters any non-fatal problems (such as a missing PDF file or JATS validation error), it returns a nonzero value equal to 100 + the number of articles that had failures.   Summarizing the possible return codes:

| Return value | Meaning |
|:------------:|---------|
| `0`          | No errors were encountered &ndash; success |
| `1`          | No network detected &ndash; cannot proceed |
| `2`          | The user interrupted program execution |
| `3`          | An exception or fatal error occurred |
| `100` + _n_  | Encountered non-fatal problems on a total of _n_ articles |


### _Summary of command-line options_

The following table summarizes all the command line options available. (Note: on Windows computers, `/` must be used as the prefix character instead of `-`):

| Short&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; | Long&nbsp;form&nbsp;opt&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; | Meaning | Default | |
|---------|-------------------|----------------------|---------|--|
| `-a`_A_ | `--after-date`_A_ | Only get articles published after date _A_ | Get all articles | ⬥ |
| `-C`    | `--no-color`      | Don't color-code info messages | Color-code terminal output |
| `-d`_D_ | `--dest`_D_       | Destination for archive: Portico or PMC | Portico | |
| `-f`_F_ | `--doi-file`_F_   | Only get articles whose DOIs are in file _F_ | Get all articles | |
| `-j`_J_ | `--journal`_J_    | Work with journal _J_ | | ★ |
| `-l`    | `--list-dois`     | Print a list of all known DOIs & exit | Do other actions instead | |
| `-o`_O_ | <nobr><code>--output-dir</code></nobr>_O_ | Write output in directory _O_ | Write in current dir | |
| `-p`    | `--preview`       | Preview what would be archived & exit | Obtain the articles | |
| `-q`    | `--quiet`         | Only print important messages | Be chatty while working | |
| `-r`_R_ | `--rep-file`_R_   | Write list of article & results in file _R_ | Don't write a report | |
| `-s`_S_ | `--rep-fmt`_S_    | With `-r`, write either `html` or `csv` | `csv` | |
| `-t`_T_ | `--rep-title`_T_  | With `-r`, use _T_ as the report title | Use the current date | |
| `-V`    | `--version`       | Print program version info, then exit | Do other actions instead | |
| `-X`    | `--no-check`      | Don't validate JATS XML files | Validate JATS XML | |
| `-Z`    | `--no-zip`        | Don't put output into one ZIP archive | ZIP up the output | |
| `-@`_OUT_ | `--debug`_OUT_  | Debugging mode; write trace to _OUT_ | Normal mode | ⚑ |

⬥ &nbsp; Enclose the date in quotes if it contains space characters; e.g., `"12 Dec 2014"`.<br>
★ &nbsp; Required argument.<br>
⚑ &nbsp; To write to the console, use the character `-` (a single dash) as the value of _OUT_; otherwise, _OUT_ must be the name of a file where the output should be written.


⁇ Getting help and support
--------------------------

If you find an issue, please submit it in [the GitHub issue tracker](https://github.com/caltechlibrary/pubarchiver/issues) for this repository.


♬ Contributing
-------------

We would be happy to receive your help and participation with enhancing `pubarchiver`!  Please visit the [guidelines for contributing](CONTRIBUTING.md) for some tips on getting started.


☥ License
----------

Copyright &copy; 2019-2021, Caltech.  This software is freely distributed under a BSD/MIT type license.  Please see the [LICENSE](LICENSE) file for more information.


❡ Authors and history
--------------------

[Tom Morrell](https://github.com/tmorrell) developed the original algorithm for extracting metadata from DataCite and creating XML files for use with Portico submissions of microPublication.org articles.  [Mike Hucka](https://github.com/mhucka) created the much-expanded second version of the software, now known as PubArchiver.


♥︎ Acknowledgments
-----------------------

The [vector artwork](https://thenounproject.com/term/archive/1590047/) used as a starting point for the logo for this repository was created by [Cuby Design](https://thenounproject.com/back1design1/) for the [Noun Project](https://thenounproject.com).  It is licensed under the Creative Commons [Attribution 3.0 Unported](https://creativecommons.org/licenses/by/3.0/deed.en) license.  The vector graphics was modified by Mike Hucka to change the color.

[Nick Stiffler](https://github.com/nickstiffler) from the [microPublication.org team](https://www.micropublication.org/contact-us/) helped figure out the requirements for PMC output (introduced in version 1.9), helped guide development of PubArchiver, and engaged in many discussions about microPublication.org's needs.

PubArchiver makes use of numerous open-source packages, without which it would have been effectively impossible to develop PubArchiver with the resources we had.  We want to acknowledge this debt.  In alphabetical order, the packages are:

* [colorful](https://github.com/timofurrer/colorful) &ndash; terminal/text string styling
* [commonpy](https://github.com/caltechlibrary/commonpy) &ndash; a collection of commonly-useful Python functions
* [dateparser](https://github.com/scrapinghub/dateparser) &ndash; parser for human-readable dates
* [dateutil](https://dateutil.readthedocs.io/en/stable/) &ndash; extensions to the Python `datetime` module
* [humanize](https://github.com/jmoiron/humanize) &ndash; make numbers more easily readable by humans
* [lxml](https://lxml.de) &ndash; an XML parsing library for Python
* [Pillow](https://github.com/python-pillow/Pillow) &ndash; a fork of the Python Imaging Library
* [plac](http://micheles.github.io/plac/) &ndash; a command line argument parser
* [pypubsub](https://github.com/schollii/pypubsub) &ndash; a publish-and-subscribe message-passing library for Python
* [recordclass](https://github.com/intellimath/recordclass) &ndash; a mutable version of Python named tuples
* [requests](http://docs.python-requests.org) &ndash; an HTTP library for Python
* [setuptools](https://github.com/pypa/setuptools) &ndash; library for `setup.py`
* [slack-cli](https://github.com/rockymadden/slack-cli) &ndash; a command-line interface to Slack written in [Bash](https://www.gnu.org/software/bash/)
* [urllib3](https://urllib3.readthedocs.io/en/latest/) &ndash; a powerful HTTP library for Python
* [xmltodict](https://github.com/martinblech/xmltodict) &ndash; a module to make working with XML feel like working with JSON
* [wxPython](https://wxpython.org) &ndash; a cross-platform GUI toolkit for the Python language

Finally, we are grateful for computing &amp; institutional resources made available by the California Institute of Technology.
    
<div align="center">
  <a href="https://micropublication.org">
    <img height="100" src="https://github.com/caltechlibrary/pubarchiver/blob/main/.graphics/micropublication-logo-main.png?raw=true">
  </a>
  &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
  <a href="https://www.caltech.edu">
    <img width="100" height="100" src="https://github.com/caltechlibrary/pubarchiver/blob/main/.graphics/caltech-round.png?raw=true">
  </a>
  &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
</div>
