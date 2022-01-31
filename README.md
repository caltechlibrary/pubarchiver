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

The Caltech Library is the publisher of a few academic journals and provides services for them. The services include archiving in a [dark archive](http://preservationmatters.blogspot.com/2013/05/light-dark-and-dim-archives-what-are.html) (specifically, [Portico](https://www.portico.org)) as well as submitting articles to [PMC](https://www.ncbi.nlm.nih.gov/pmc/).  The archiving process involves pulling down articles from the journals and packaging them up in a format suitable for sending to the archives.  PubArchiver is a program to help automate this process.


✺ Installation
-------------

There are multiple ways of installing PubArchiver.  Please choose the alternative that suits you.

### _Alternative 1: installing PubArchiver using `pipx`_

You can use [pipx](https://pypa.github.io/pipx/) to install PubArchiver. Pipx will install it into a separate Python environment that isolates the dependencies needed by PubArchiver from other Python programs on your system, and yet the resulting `pubarchiver` command wil be executable from any shell &ndash; like any normal program on your computer. If you do not already have `pipx` on your system, it can be installed in a variety of easy ways and it is best to consult [Pipx's installation guide](https://pypa.github.io/pipx/installation/) for instructions. Once you have pipx on your system, you can install PubArchiver with the following command:
```sh
pipx install pubarchiver
```

Pipx can also let you run PubArchiver directly using `pipx run pubarchiver`, although in that case, you must always prefix every `pubarchiver` command with `pipx run`.  Consult the [documentation for `pipx run`](https://github.com/pypa/pipx#walkthrough-running-an-application-in-a-temporary-virtual-environment) for more information.


### _Alternative 2: installing PubArchiver using `pip`_

The instructions below assume you have a Python 3 interpreter installed on your computer.  Note that the default on macOS at least through 10.14 (Mojave) is Python **2** &ndash; please first install Python version 3 and familiarize yourself with running Python programs on your system before proceeding further.

On **Linux**, **macOS**, and **Windows** operating systems, you should be able to install `pubarchiver` with [`pip`](https://pip.pypa.io/en/stable/installing/) for Python&nbsp;3.  To install `pubarchiver` from the [Python package repository (PyPI)](https://pypi.org), run the following command:
```sh
python3 -m pip install pubarchiver
```

As an alternative to getting it from [PyPI](https://pypi.org), you can use `pip` to install `pubarchiver` directly from GitHub:
```sh
python3 -m pip install git+https://github.com/calitechlibrary/pubarchiver.git
```

_If you already installed PubArchiver once before_, and want to update to the latest version, add `--upgrade` to the end of either command line above.


### _Alternative 3: installing PubArchiver from sources_

If  you prefer to install PubArchiver directly from the source code, you can do that too. To get a copy of the files, you can clone the GitHub repository:
```sh
git clone https://github.com/caltechlibrary/pubarchiver
```

Alternatively, you can download the files as a ZIP archive using this link directly from your browser using this link: <https://github.com/caltechlibrary/pubarchiver/archive/refs/heads/main.zip>

Next, after getting a copy of the files,  run `setup.py` inside the code directory:
```sh
cd pubarchiver
python3 setup.py install
```


▶︎ Usage
-------

PubArchiver is a command-line program.  The installation process should put a program named `pubarchiver` in a location normally searched by your shell interpreter.  For help with usage at any time, run `pubarchiver` with the option `--help` (or `-h` for short).

```bash
pubarchiver -h
```

The following is a screen recording of an actual run of `pubarchiver`:

<p align="center">
  <a href="https://asciinema.org/a/260298"><img src="https://github.com/caltechlibrary/pubarchiver/blob/main/.graphics/pubarchiver-asciinema.png?raw=true" alt="Screencast of simple pubarchiver demo"></a>
</p>


### _Basic usage_

Options to `pubarchiver` use a dash (`-`) as the prefix character on macOS and Linux, and forward slash (`/`) on Windows.

The journal whose articles are to be archived must be indicated using the required option `--journal` (or `-j` for short). To see a list of supported journals, you can use `--journal list` like this:

```bash
pubarchiver --journal list
```

If not given any additional options besides a `--journal` option to select the journal, `pubarchiver` will proceed to contact the journal website as well as either [DataCite](https://datacite.org) or [Crossref](https://www.crossref.org), and create an archive containing articles and their metadata for all articles published to date by the journal.  The options below can be used to select articles and influence other `pubarchiver` behaviors.


### _Printing information without doing anything_

The option `--list-dois` (or `-l` for short) can be used to obtain a list of all DOIs for all articles published by the selected journal. When `--list-dois` is used, `pubarchiver` prints the list to the terminal and exits without doing further work. This can be useful if you intend to use the `--doi-file` option discussed below.

If given the option `--preview` (or `-p` for short), `pubarchiver` will _only_ print a list of articles it will archive and stop short of creating the archive. This is useful to see what would be produced without actually doing it.  Note, however, that because it does not attempt to download the articles and associated files, it cannot report errors that _might_ occur when actually creating an archive.  Consequently, do not use the output of `--preview` as a prediction of eventual success or failure.


### _Selecting the archive format and archive output location_

The value supplied after the option `--dest` (or `-d` for short) can be used to tell `pubarchiver` the intended destination where the archive will be sent.  The option changes the structure and content of the archive created by `pubarchiver`. The possible alternatives are `portico` and `pmc`. Portico is assumed to be the default destination if no `--dest` option is given. 

By default, `pubarchiver` will write its output to a new subdirectory it creates in the directory from which `pubarchiver` is being run. The option `--output-dir` (or `/o` on Windows) can be used to select a different location. For example,

```bash
pubarchiver --journal micropublication --output-dir /tmp/micropub
```

The materials for each article will be written to an individual subdirectory named after the DOI of the article.  The output for each article will consist of an XML metadata file describing the article, the article itself in PDF format, and (if the journal provides [JATS](https://jats.nlm.nih.gov)) a subdirectory named `jats` containing the article in JATS XML format along with any image that may appear in the article.  The image is always converted to uncompressed TIFF format, because it is considered a good preservation format. The PMC structure follows the _naming and delivery_ specifications defined at https://www.ncbi.nlm.nih.gov/pmc/pub/filespec-delivery/.

Unless the option `--no-zip` (or `-Z` for short) is given, the output will be archived in [ZIP](https://en.wikipedia.org/wiki/Zip_(file_format)) format.  If the output structure (as determine by the `--dest` option) is being generated for PMC, each article will be put into its own individual ZIP archive; else, the default action is to put the collected output of all articles into a single ZIP archive file.  The option `--no-zip` makes `pubarchiver` leave the output unarchived in the directory determined by the `--output-dir` option.


### _Selecting a subset of articles_

If the option `--after-date` is given, `pubarchiver` will download only articles whose publication dates are _after_ the given date.  Valid date descriptors are those accepted by the Python [dateparser](https://pypi.org/project/dateparser/) library.  Make sure to enclose descriptions within single or double quotes.  Examples:

```
  pubarchiver --after-date "2014-08-29"   ....
  pubarchiver --after-date "12 Dec 2014"  ....
  pubarchiver --after-date "July 4, 2013"  ....
  pubarchiver --after-date "2 weeks ago"  ....
```

The option `--doi-file` (or `-f` for short) can be used to tell `pubarchiver` to read a file containing DOIs and only fetch those particular articles instead of asking the journal for all articles.  The format of the file indicated after the `--doi-file` option must be a simple text file containing one DOI per line.

The selection by date performed by the `--after-date` option is performed after reading the list of articles using the `--doi-file` option if present, and thus can be used to filter by date the articles whose DOIs are provided.


### _Writing a report_

As it works, `pubarchiver` writes information to the terminal about the articles it puts into the archive, including whether any problems are encountered.  To save this information to a file, use the option `--rep-file` (or `-r` for short), which will make `pubarchiver` write a report file.  By default, the format of the report file is [CSV](https://en.wikipedia.org/wiki/Comma-separated_values); the option `--rep-fmt` (or `-s` for short) can be used to select `csv` or `html` (or both) as the format.  The title of the report will be based on the current date, unless the option `--rep-title` (or `-t` for short) is used to supply a different title.


### _Additional command-line options_

When `pubarchiver` downloads the JATS XML version of articles from the journal site, it will by default validate the XML content against the JATS DTD.  To skip the XML validation step, use the option `--no-check` (or `-X` for short).

`pubarchiver` will print informational messages as it works. To reduce messages to only warnings and errors, use the option `--quiet` (or `-q` for short). Also, output is color-coded by default unless the `--no-color` option (or `-C` for short) is given; this option can be helpful if the color control sequences create problems for your terminal emulator.

If given the `--debug` option (or `-@` for short), this program will output a detailed real-time trace of what it is doing.  The output will be written to the given destination, which can be a dash character (`-`) to indicate console output, or a file path.

If given the `--version` option (or `-V` for short), this program will print version information and exit without doing anything else.


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
| `-V`    | `--version`       | Print program version info & exit | Do other actions instead | |
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

Copyright &copy; 2019-2021, Caltech.  This software is freely distributed under a BSD 3-clause license.  Please see the [LICENSE](LICENSE) file for more information.


❡ Authors and history
--------------------

[Tom Morrell](https://github.com/tmorrell) developed the original algorithm for extracting metadata from DataCite and creating XML files for use with Portico submissions of microPublication.org articles.  Starting with that original script, [Mike Hucka](https://github.com/mhucka) created the much-expanded Microarchiver program (later renamed to PubArchiver).


♥︎ Acknowledgments
-----------------------

The [vector artwork](https://thenounproject.com/term/archive/1590047/) used as a starting point for the logo for this repository was created by [Cuby Design](https://thenounproject.com/back1design1/) for the [Noun Project](https://thenounproject.com).  It is licensed under the Creative Commons [Attribution 3.0 Unported](https://creativecommons.org/licenses/by/3.0/deed.en) license.  The vector graphics was modified by Mike Hucka to change the color.

[Nick Stiffler](https://github.com/nickstiffler) from the [microPublication.org team](https://www.micropublication.org/contact-us/) helped figure out the requirements for PMC output (introduced in Microarchiver version 1.9), helped guide development of Microarchiver/PubArchiver, and engaged in many discussions about microPublication.org's needs.

PubArchiver makes use of numerous open-source packages, without which it would have been effectively impossible to develop PubArchiver with the resources we had.  We want to acknowledge this debt.  In alphabetical order, the packages are:

* [Beautiful Soup](https://www.crummy.com/software/BeautifulSoup/) &ndash; an HTML parsing library
* [bun](https://github.com/caltechlibrary/bun) &ndash; a set of basic user interface classes and functions
* [commonpy](https://github.com/caltechlibrary/commonpy) &ndash; a collection of commonly-useful Python functions
* [crossrefapi](https://github.com/fabiobatalha/crossrefapi) &ndash; a python library that implements the Crossref API
* [dateparser](https://github.com/scrapinghub/dateparser) &ndash; parser for human-readable dates
* [humanize](https://github.com/jmoiron/humanize) &ndash; make numbers more easily readable by humans
* [lxml](https://lxml.de) &ndash; an XML parsing library for Python
* [Pillow](https://github.com/python-pillow/Pillow) &ndash; a fork of the Python Imaging Library
* [plac](http://micheles.github.io/plac/) &ndash; a command line argument parser
* [recordclass](https://github.com/intellimath/recordclass) &ndash; a mutable version of Python named tuples
* [setuptools](https://github.com/pypa/setuptools) &ndash; library for `setup.py`
* [sidetrack](https://github.com/caltechlibrary/sidetrack) &ndash; simple debug logging/tracing package
* [slack-cli](https://github.com/rockymadden/slack-cli) &ndash; a command-line interface to Slack written in [Bash](https://www.gnu.org/software/bash/)
* [urllib3](https://urllib3.readthedocs.io/en/latest/) &ndash; a powerful HTTP library for Python
* [xmltodict](https://github.com/martinblech/xmltodict) &ndash; a module to make working with XML feel like working with JSON

Finally, we are grateful for computing &amp; institutional resources made available by the California Institute of Technology.
    
<div align="middle">
  <a href="https://www.caltech.edu">
    <img align="center" width="80" src="https://github.com/caltechlibrary/pubarchiver/blob/main/.graphics/caltech-round.png?raw=true">
  </a>
  &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
  <a href="https://micropublication.org">
    <img align="center" height="60" src="https://github.com/caltechlibrary/pubarchiver/blob/main/.graphics/micropublication-logo-main.png?raw=true">
  </a>
  &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
  <a href="http://thepromptjournal.com">
    <img align="center" height="60" src="https://github.com/caltechlibrary/pubarchiver/blob/main/.graphics/prompt-logo.jpg?raw=true">
  </a>

</div>
