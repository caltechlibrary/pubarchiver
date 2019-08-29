Change log for microarchiver
============================

Version 1.3.1
-------------

* If there are no articles to archive, don't create the output directory either.


Version 1.3.0
-------------

* If there are no articles to archive, don't create a zip file.


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
