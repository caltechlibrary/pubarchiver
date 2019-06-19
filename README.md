Microarchiver<img width="12%" align="right" src=".graphics/microarchiver-logo.svg">
=======

A program to create archives of articles from [microPublication.org](https://www.micropublication.org) for sending to [Portico](https://www.portico.org).


*Authors*:      [Michael Hucka](http://github.com/mhucka), [Tom Morrell](https://github.com/tmorrell)<br>
*Repository*:   [https://github.com/caltechlibrary/microarchiver](https://github.com/caltechlibrary/microarchiver)<br>
*License*:      BSD/MIT derivative &ndash; see the [LICENSE](LICENSE) file for more information

[![License](https://img.shields.io/badge/License-BSD%203--Clause-blue.svg?style=flat-square)](https://choosealicense.com/licenses/bsd-3-clause)
[![Python](https://img.shields.io/badge/Python-3.4+-brightgreen.svg?style=flat-square)](http://shields.io)
[![Latest release](https://img.shields.io/badge/Latest_release-0.0.1-b44e88.svg?style=flat-square)](http://shields.io)


Table of Contents
-----------------
* [Introduction](#-introduction)
* [How to install and uninstall Microarchiver](#-installation-instructions)
* [How to use Microarchiver](#︎-basic-operation)
* [Getting help and support](#-getting-help-and-support)
* [Do you like it?](#-do-you-like-it)
* [Acknowledgments](#︎-acknowledgments)
* [Copyright and license](#︎-copyright-and-license)


☀ Introduction
-----------------------------

The Caltech Library is the publisher of the online journal [microPublication](https://www.micropublication.org) and provides services to the journal that include archiving the journal in a dark archive (specifically, [Portico](https://www.portico.org)).  The archiving process involves pulling down articles from [microPublication](https://www.micropublication.org) and packaging them up in a format suitable for sending to Portico.  The programs in this repository are used to automate this process.


✺ How to install and uninstall Microarchiver
-------------------------------------

You can download the source code for Microarchiver and run the programs using a Python&nbsp;3 interpreter.  The following is probably the simplest and most direct way to install this software on your computer:
```sh
sudo python3 -m pip install git+https://github.com/caltechlibrary/microarchiver.git --upgrade
```

Alternatively, you can clone this GitHub repository and then run `setup.py`:
```sh
git clone https://github.com/caltechlibrary/microarchiver.git
cd microarchiver
sudo python3 -m pip install . --upgrade
```


▶︎ How to use Microarchiver
--------------------

_...FORTHCOMING...._


⁇ Getting help and support
--------------------------

If you find an issue, please submit it in [the GitHub issue tracker](https://github.com/caltechlibrary/microarchiver/issues) for this repository.


☺︎ Acknowledgments
-----------------------

The [vector artwork](https://thenounproject.com/search/?q=archive&i=158401) used as a starting point for the logo for this repository was created by [Thomas Helbig](https://thenounproject.com/dergraph/) for the [Noun Project](https://thenounproject.com).  It is licensed under the Creative Commons [Attribution 3.0 Unported](https://creativecommons.org/licenses/by/3.0/deed.en) license.  The vector graphics was modified by Mike Hucka to change the color.

_Microarchiver_ makes use of numerous open-source packages, without which it would have been effectively impossible to develop _Microarchiver_ with the resources we had.  We want to acknowledge this debt.  In alphabetical order, the packages are:

* [colorama](https://github.com/tartley/colorama) &ndash; makes ANSI escape character sequences work under MS Windows terminals
* [halo](https://github.com/ManrajGrover/halo) &ndash; busy-spinners for Python command-line programs
* [humanize](https://github.com/jmoiron/humanize) &ndash; make numbers more easily readable by humans
* [ipdb](https://github.com/gotcha/ipdb) &ndash; the IPython debugger
* [lxml](https://lxml.de) &ndash; an XML parsing library for Python
* [plac](http://micheles.github.io/plac/) &ndash; a command line argument parser
* [requests](http://docs.python-requests.org) &ndash; an HTTP library for Python
* [setuptools](https://github.com/pypa/setuptools) &ndash; library for `setup.py`
* [termcolor](https://pypi.org/project/termcolor/) &ndash; ANSI color formatting for output in terminal
* [urllib3](https://urllib3.readthedocs.io/en/latest/) &ndash; a powerful HTTP library for Python


☮︎ Copyright and license
---------------------

Copyright (C) 2019, Caltech.  This software is freely distributed under a BSD/MIT type license.  Please see the [LICENSE](LICENSE) file for more information.
    
<div align="center">
  <a href="https://www.caltech.edu">
    <img width="100" height="100" src=".graphics/caltech-round.svg">
  </a>
</div>
