Change log for microarchiver
============================

Version 1.6.1
-------------

* Fix broken handling of debug trace output destination.
* Update `README.md`.


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
