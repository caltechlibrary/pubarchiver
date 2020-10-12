Change log for microarchiver
============================

Version 1.10.0
--------------

This version changes the behavior of the `-@` command-line option, such that exceptions encountered when running with the `-@` option do _not_ cause `microarchiver` to drop into an interactive debugger.  The old behavior turned out to be unhelpful in practice, and moreover, it mixed two behaviors into one command-line flag.  The latter was problematic when running `microarchiver` from scripts.


Version 1.9.4
--------------

This version removes an unnecessary dependency on wxPython.  A GUI interface was never completed for Microarchiver, and while the starting code is still in the code base in case we try to build a GUI, it doesn't have to be hooked in at this point.  Removing the internal references to the GUI code allows the wxPython requirement to be removed, which in turn simplifies and speeds up installation.


Version 1.9.3
--------------

* Add missing Python package requirement to requirements.txt.
* Simplify PMC upload script.


Version 1.9.2
--------------

* Fix broken logos and images in README.md.
* Replace local version of `debug.py` with the use of [Sidetrack](https://github.com/caltechlibrary/sidetrack).
* Use newer approach to recording version and other metadata in `__init__.py` and the release procedure codified in `Makefile`.
* Minor internal changes.


Version 1.9.1
-------------

* Fix [issue #2](https://github.com/caltechlibrary/microarchiver/issues/2): volume number in file names is incorrectly determined


Version 1.9.0
-------------

* Support output for PMC using new command-line option `-s`.
* Rename the JATS XML file after the pattern _issn_-_volume_-_doi_.xml, to make it more compatible with output generated for PMC.
* Remove any alpha channels and convert images to RGB.
* Run ZIP files through a simple validation step after creating them.
* Added missing dependencies to [`requirements.txt`](requirements.txt).
* Some internal code changes.


Version 1.8.0
-------------

* Instead of quitting with an error if the file given to `-a` is empty, `microarchiver` will now just print a warning.


Version 1.7.0
-------------

* Store JATS XML for each article, as well as any image referenced in the JATS data. Images are converted to uncompressed TIFF before being stored.
* Perform JATS validation for each article by default.
* Add `-X` option to disable automatic JATS DTD validation.
* Change `-a` option to accept a file containing either a list of DOIs or the XML format sent by micropublication.org.
* Change exit code numbering scheme.
* Communicate number of failures in terms of exit codes; see [README](README.md) for more details.
* Test if date given to `-d` is syntactically correct but not a valid date.
* Refactor and change some internal code.
* Fix miscellaneous bugs.


Version 1.6.3
-------------

* Catch and handle no-content errors more gracefully.
* Detect mangled XML returned by micropublication.org and handle it more gracefully.


Version 1.6.2
-------------

* Fix crasher in writing comment into zip file because of reference to no-longer-existing package attribute.


Version 1.6.1
-------------

* Fix broken handling of debug trace output destination.
* Update `README.md` to describe changes to debug flag.


Version 1.6.0
-------------

* Change the debug flag `-@` to accept an argument for where to send the debug output trace. The behavior change of `-@` is not backward compatible.
* Put metadata in `setup.cfg` and change how Microarchiver gets the metadata internally.


Version 1.5.1
-------------

* Fix bug in propagating network failures up to the top of main.
* Fix case of variable being shadowed inside a block.


Version 1.5.0
-------------

* Added new `-g` option to print the raw XML article list from the server.
* Did very minor internal code refactoring.


Version 1.4.0
-------------

* Added new `scripts` subdirectory with script for use with cron.
* Fixed behavior: if there are no articles to archive, don't create the output directory either.


Version 1.3.0
-------------

* Now if there are no articles to archive, it won't create a zip file.


Version 1.2.0
-------------

* Improved installation instructions.
* Changed debug flag from `-Z` to `-@`.
* Internal code changes for message printing & colorization.


Version 1.1.0
-------------

* **Backwards incompatible change**: command-line arguments have been significantly changed in terms of names and shortcut letters.
* Addition of new `-d` command-line argument, for getting only articles published after a certain date.
* Output is now always created in a subdirectory of the directory given as the value of the `-o` option, rather than directly into that directory. The subdirectory name is always `micropublication-org`.
* When a zip archive is being created (the default case), then the output directory will be deleted afterward.
* Updates to the documentation (top-level `README.md` file) and internal help strings.
* Minor other internal changes.
