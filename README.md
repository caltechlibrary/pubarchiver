Microarchiver<img width="12%" align="right" src="https://github.com/caltechlibrary/microarchiver/blob/main/.graphics/microarchiver-logo.png?raw=true">
=======

A program to create archives of articles from [microPublication.org](https://www.micropublication.org) for sending to [Portico](https://www.portico.org).

*Authors*:      [Michael Hucka](http://github.com/mhucka), [Tom Morrell](https://github.com/tmorrell)<br>
*Repository*:   [https://github.com/caltechlibrary/microarchiver](https://github.com/caltechlibrary/microarchiver)<br>
*License*:      BSD/MIT derivative &ndash; see the [LICENSE](LICENSE) file for more information

[![License](https://img.shields.io/badge/License-BSD%203--Clause-yellow.svg?style=flat-square)](https://choosealicense.com/licenses/bsd-3-clause)
[![Python](https://img.shields.io/badge/Python-3.5+-brightgreen.svg?style=flat-square)](https://www.python.org/downloads/release/python-350/)
[![Latest release](https://img.shields.io/github/v/release/caltechlibrary/microarchiver.svg?style=flat-square&color=b44e88)](https://github.com/caltechlibrary/microarchiver/releases)
[![DOI](http://img.shields.io/badge/DOI-10.22002/D1.1643-blue.svg?style=flat-square)](https://data.caltech.edu/records/1643)
[![PyPI](https://img.shields.io/pypi/v/microarchiver.svg?style=flat-square&color=red)](https://pypi.org/project/microarchiver/)


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

The Caltech Library is the publisher of the online journal [microPublication](https://www.micropublication.org) and provides services to the journal that include archiving the journal in a dark archive (specifically, [Portico](https://www.portico.org)).  The archiving process involves pulling down articles from [microPublication](https://www.micropublication.org) and packaging them up in a format suitable for sending to Portico.  `microarchiver` is a program to automate this process.


✺ Installation
-------------

On **Linux**, **macOS**, and **Windows** operating systems, you should be able to install Microarchiver directly from the GitHub repository using [pip](https://pip.pypa.io/en/stable/installing/).  If you don't have the `pip` package or are uncertain if you do, first run the following command in a terminal command line interpreter: 
```
sudo python3 -m ensurepip
```

Then, install this software by running the following command on your computer:
```sh
python3 -m pip install git+https://github.com/caltechlibrary/microarchiver.git --user --upgrade 
```

Alternatively, you can clone this GitHub repository and then run `setup.py`:
```sh
git clone https://github.com/caltechlibrary/microarchiver.git
cd microarchiver
python3 -m pip install . --user --upgrade
```


▶︎ Usage
-------

Microarchiver is a command-line program.  The installation process should put a program named `microarchiver` in a location normally searched by your shell interpreter.  For help with usage at any time, run `microarchiver` with the option `-h` (or `/h` on Windows).

```bash
microarchiver -h
```

### _Basic usage_

The simplest use of `microarchiver` involves running it without any options.  By default, it will contact [microPublication.org](http://micropublication.org) to get a list of current articles, and create an archive of all the articles in a subdirectory of the current directory.

```bash
microarchiver
```

If given the option `-o` (or `/o` on Windows), the output will be written to the directory named after the `-o`.  (If no `-o` is given, the output will be written to the current directory instead.)  For example:

```bash
microarchiver -o /tmp/micropublication-archive
```

If the option `-d` is given, `microarchiver` will download only articles whose publication dates are _after_ the given date.  Valid date descriptors are those accepted by the Python [dateparser](https://pypi.org/project/dateparser/) library.  Make sure to enclose descriptions within single or double quotes.  Examples:

```
  microarchiver -d "2014-08-29"   ....
  microarchiver -d "12 Dec 2014"  ....
  microarchiver -d "July 4, 2013"  ....
  microarchiver -d "2 weeks ago"  ....
```

As it works, `microarchiver` writes information to the terminal about the archives it puts into the archive, including whether any problems are encountered. To save this info to a file, use the option `-r` (or `/r` on Windows), which will make `microarchiver` write a report file in [CSV](https://en.wikipedia.org/wiki/Comma-separated_values) format.

The following is a screen recording of an actual run of `microarchiver`:

<p align="center">
  <a href="https://asciinema.org/a/260298"><img src="https://github.com/caltechlibrary/microarchiver/blob/main/.graphics/microarchiver-asciinema.png?raw=true" alt="Screencast of simple microarchiver demo"></a>
</p>


### Previewing the list of articles

If given the option `-p` (or `/p` on Windows), `microarchiver` will _only_ print a list of articles it will archive and stop short of creating the archive. This is useful to see what would be produced without actually doing it.  However, note that because it does not attempt to download the articles and associated files, it will not be able to report on errors that might occur when not operating in preview mode.  Consequently, do not use the output of `-p` as a prediction of eventual success or failure.

If given the option `-g` (or `/g` on Windows), `microarchiver` will _only_ write a file named `article-list.xml` containing the complete current article list from the micropublication.org server, and exit without doing anything else.  This is useful as a starting point for creating the file used by option `-a`.  It's probably a good idea to redirect the output to a file; e.g.,

```
microarchiver -g > article-list.xml
```

### Output

Unless given the option `-g` or `-p`, microarchiver will download articles from micropublication.org and create archive files out of them.

The value supplied after the option `-s` (or `/s` on Windows) determines the structure of the archive generated by this program.  Currently, two output structures are supported: PMC, and a structure suitable for Portico.  (The PMC structure follows the "naming and delivery" specifications defined at https://www.ncbi.nlm.nih.gov/pmc/pub/filespec-delivery/.) If the output will be sent to PMC, use `-s pmc`; else, use `-s portico` or leave off the option altogether (because Portico is the default).

The output will be written to the directory indicated by the value of the option `-o` (or `/o` on Windows).  If no `-o` is given, the output will be written to the directory in which `microarchiver` was started. Each article will be written to a subdirectory named after the DOI of the article. The output for each article will consist of an XML metadata file describing the article, the article itself in PDF format, and a subdirectory named `jats` containing the article in JATS XML format along with any image that may appear in the article.  The image is always converted to uncompressed TIFF format (because it is considered a good preservation format).

Unless the option `-Z` (or `/Z` on Windows) is given, the output will be archived in [ZIP](https://en.wikipedia.org/wiki/Zip_(file_format)) format. If the output structure (as determine by the `-s` option) is being generated for PMC, each article will be put into its own individual ZIP archive; else, the default action is to put the collected output of all articles into a single ZIP archive file.  The option `-Z` makes `microarchiver` leave the output unarchived in the output directory determined by the `-o` option.


### _Additional command-line options_

If given the option `-a` (or `/a` on Windows) followed by a file name, the given file will be read for the list of articles instead of getting the list from the server. The contents of the file can be either a list of DOIs, or article data in the same XML format as the list obtained from micropublication.org.  (See option `-g` above for a way to get an article list in XML from the server.)

Microarchiver always downloads the JATS XML version of articles from micropublication.org (in addition to downloading the PDF version), and by default, microarchiver validates the XML content against the JATS DTD.  To skip the XML validation step, use the option `-X` (`/X` on Windows).

`microarchiver` will print informational messages as it works. To reduce messages to only warnings and errors, use the option `-q` (or `/q` on Windows). Also, output is color-coded by default unless the `-C` option (or `/C` on Windows) is given; this option can be helpful if the color control sequences create problems for your terminal emulator.

If given the `-@` option (`/@` on Windows), this program will output a detailed real-time trace of what it is doing.  The output will be written to the given destination, which can be a dash character (`-`) to indicate console output, or a file path.

If given the `-V` option (`/V` on Windows), this program will print version
information and exit without doing anything else.


### Return values

This program exits with a return code of `0` if no problems are encountered while fetching data from the server.  It returns a nonzero value otherwise, following conventions for use in shells such as bash which only understand return code values of `0` to `255`.  If it is interrupted (e.g., using `ctrl-c`) it returns a value of `1`; if it encounters a fatal error, it returns a value of `2`.  If it encounters any non-fatal problems (such as a missing PDF file or JATS validation error), it returns a nonzero value equal to 100 + the number of articles that had failures.   Summarizing the possible return codes:

| Return value | Meaning |
|:------------:|---------|
| `0`          | No errors were encountered &ndash; success |
| `1`          | No network detected &ndash; cannot proceed |
| `2`          | The user interrupted program execution |
| `3`          | An exception or fatal error occurred |
| `100` + _n_  | Encountered non-fatal problems on a total of _n_ articles |


### _Summary of command-line options_

The following table summarizes all the command line options available. (Note: on Windows computers, `/` must be used as the prefix character instead of `-`):

| Short&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; | Long&nbsp;form&nbsp;opt&nbsp;&nbsp; | Meaning | Default | |
|---------|-------------------|----------------------|---------|--|
| `-a`_A_ | `--articles`_A_   | Get list of articles from file _A_ | Get list from server | |
| `-C`    | `--no-color`      | Don't color-code the output | Color the terminal output | |
| `-d`_D_ | `--after-date`_D_ | Only get articles published after date _D_ | Get all articles | ⬥ |
| `-g`    | `--get-xml`       | Print the server's article list & exit | Do other actions instead | |
| `-o`_O_ | <nobr><code>--output-dir</code></nobr>_O_ | Write output in directory _O_ | Write in current dir | |
| `-p`    | `--preview`       | Preview what would be obtained | Obtain the articles | |
| `-q`    | `--quiet`         | Only print important messages | Be chatty while working | |
| `-r`_R_ | `--report`_R_     | Write list of article & results in file _R_ | Don't write a report | |
| `-s`_S_ | `--structure`_S_  | Structure output for Portico or PMC | Portico | |
| `-V`    | `--version`       | Print program version info and exit | Do other actions instead | |
| `-X`    | `--no-check`      | Don't validate JATS XML files | Validate JATS XML | |
| `-Z`    | `--no-zip`        | Don't put output into one ZIP archive | ZIP up the output | |
| `-@`_OUT_ | `--debug`_OUT_  | Debugging mode; write trace to _OUT_ | Normal mode | ⚑ |

⬥ &nbsp; Enclose the date in quotes if it contains space characters; e.g., `"12 Dec 2014"`.<br>
⚑ &nbsp; To write to the console, use the character `-` (a single dash) as the value of _OUT_; otherwise, _OUT_ must be the name of a file where the output should be written.


⚑ Known issues and limitations
-------------------------------

Currently, the only way to indicate that a subset of articles should be obtained from microPublication.org is to use the option `-a` in combination with a file that contains the list of desired articles, or the `-d` option to indicate a cut-off for the article publication date.


⁇ Getting help and support
--------------------------

If you find an issue, please submit it in [the GitHub issue tracker](https://github.com/caltechlibrary/microarchiver/issues) for this repository.


♬ Contributing
-------------

We would be happy to receive your help and participation with enhancing `microarchiver`!  Please visit the [guidelines for contributing](CONTRIBUTING.md) for some tips on getting started.


☥ License
----------

Copyright &copy; 2019-2020, Caltech.  This software is freely distributed under a BSD/MIT type license.  Please see the [LICENSE](LICENSE) file for more information.


❡ Authors and history
--------------------

[Tom Morrell](https://github.com/tmorrell) developed the original algorithm for extracting metadata from DataCite and creating XML files for use with Portico submissions of microPublication.org articles.  [Mike Hucka](https://github.com/mhucka) created the much-expanded second version now known as Microarchiver.


♥︎ Acknowledgments
-----------------------

The [vector artwork](https://thenounproject.com/search/?q=archive&i=158401) used as a starting point for the logo for this repository was created by [Thomas Helbig](https://thenounproject.com/dergraph/) for the [Noun Project](https://thenounproject.com).  It is licensed under the Creative Commons [Attribution 3.0 Unported](https://creativecommons.org/licenses/by/3.0/deed.en) license.  The vector graphics was modified by Mike Hucka to change the color.

[Nick Stiffler](https://github.com/nickstiffler) from the [microPublication.org team](https://www.micropublication.org/contact-us/) helped figure out the requirements for PMC output (introduced in version 1.9), helped guide development of microarchiver, and engaged in many discussions about microPublication.org's needs.

Microarchiver makes use of numerous open-source packages, without which it would have been effectively impossible to develop Microarchiver with the resources we had.  We want to acknowledge this debt.  In alphabetical order, the packages are:

* [colorful](https://github.com/timofurrer/colorful) &ndash; terminal/text string styling
* [dateparser](https://github.com/scrapinghub/dateparser) &ndash; parser for human-readable dates
* [humanize](https://github.com/jmoiron/humanize) &ndash; make numbers more easily readable by humans
* [lxml](https://lxml.de) &ndash; an XML parsing library for Python
* [Pillow](https://github.com/python-pillow/Pillow) &ndash; a fork of the Python Imaging Library
* [plac](http://micheles.github.io/plac/) &ndash; a command line argument parser
* [pypubsub](https://github.com/schollii/pypubsub) &ndash; a publish-and-subscribe message-passing library for Python
* [recordclass](https://github.com/intellimath/recordclass) &ndash; a mutable version of Python named tuples
* [requests](http://docs.python-requests.org) &ndash; an HTTP library for Python
* [setuptools](https://github.com/pypa/setuptools) &ndash; library for `setup.py`
* [urllib3](https://urllib3.readthedocs.io/en/latest/) &ndash; a powerful HTTP library for Python
* [xmltodict](https://github.com/martinblech/xmltodict) &ndash; a module to make working with XML feel like working with JSON
* [wxPython](https://wxpython.org) &ndash; a cross-platform GUI toolkit for the Python language

Finally, we are grateful for computing &amp; institutional resources made available by the California Institute of Technology.
    
<div align="center">
  <a href="https://micropublication.org">
    <img height="100" src="https://github.com/caltechlibrary/microarchiver/blob/main/.graphics/micropublication-logo-main.png?raw=true">
  </a>
  &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
  <a href="https://www.caltech.edu">
    <img width="100" height="100" src="https://github.com/caltechlibrary/microarchiver/blob/main/.graphics/caltech-round.png?raw=true">
  </a>
  &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
</div>
