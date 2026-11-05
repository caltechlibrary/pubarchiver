# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- `--dest doaj` writes microPublication.org article metadata as JSON for the article API of the [Directory of Open Access Journals](https://doaj.org) (DOAJ): one file per article, checked against the rules DOAJ applies to incoming articles. An article whose metadata DOAJ would reject is reported as `failed-doaj-validation`.
- An “Upload to DOAJ” workflow that runs daily, writes DOAJ metadata for articles published since its last run, and sends each article to DOAJ. It sends every valid article even when others fail, and keeps a list of articles that could not be written or that DOAJ rejected, which the next run tries again. It records a fingerprint of what it sent for each article and does not resend unchanged metadata. A manual “Resync” run checks every article and resends those whose metadata changed, so abstracts, ORCID iDs, and corrections added to microPublication’s JATS later can reach DOAJ. A manual run can be a dry run, which sends nothing and notifies no one.

### Changed

- microPublication.org article metadata comes from the article’s JATS file instead of Crossref: the DOI, ISSN, title, authors, affiliations, abstract, keywords, volume, and publication date. The article list only decides which articles a run selects and where their files and article pages are. An article is skipped as `missing-metadata` when its JATS can’t be read, lacks a DOI, title, or publication date, or gives a DOI different from the article list’s. The JATS publication date can be earlier than the date in the article list. ORCID iDs are included when the JATS has them. The JATS of the earliest articles has no abstract, so their Portico XML files and DOAJ records have none.
- An article with no metadata is reported as `missing-metadata`, whichever source the journal uses.
- The Slack message for a failed upload no longer says “FTP”, so it fits the DOAJ upload too.

### Fixed

- microPublication.org articles published before November 2026, whose DOIs are registered with DataCite rather than Crossref, are no longer skipped as `missing-crossref`.
- Titles in microPublication.org Portico XML files and TIFF image comments are correct. microPublication’s article list moves italicized words, such as species names, to the end of the title, and 2.2.0 used those titles.
- The volume in the names of microPublication.org PMC and Portico JATS, PDF, and ZIP files is the JATS volume, matching the name the JATS gives its image. For an article published at the turn of a year, the article list’s year can differ.
- Reading microPublication.org’s article list no longer fails with `NameError` when the server answers 404 or 410.

## [2.2.0] - 2026-11-05

### Added

- A “Release” workflow in GitHub Actions. Run it from the Actions page with a patch, minor, or major bump: it updates the version everywhere it is stored, builds the package, installs the wheel in a clean environment and runs it, commits, and opens a draft GitHub release. A dry run, the default, does everything but commit and create the release.
- A “Publish to PyPI” workflow. Publishing a GitHub release builds the package and uploads it to PyPI with Trusted Publishing, after a reviewer approves it in the `pypi` environment.
- `dev/bump_version.py`, which writes a new version into `setup.cfg`, `pubarchiver/__init__.py`, `codemeta.json`, and `CITATION.cff`, and moves the `[Unreleased]` entries in this file under the new version.
- Tommy Keswick as an author and maintainer in `codemeta.json`, `CITATION.cff`, and the package metadata.

### Changed

- microPublication.org article metadata comes from Crossref, where microPublication registers its DOIs, instead of DataCite. An article without a Crossref record is reported as `missing-crossref`.
- The abstract in microPublication.org Portico XML files comes from the article’s JATS file, as plain text, because microPublication’s Crossref records have no abstract.

### Removed

- The `Makefile`. Its release and PyPI steps are replaced by the Release and Publish to PyPI workflows.

### Fixed

- microPublication.org articles whose DOIs are not registered with DataCite are no longer skipped as `missing-datacite`.
- A wheel built with `python -m build` declared no dependencies, because `requirements.txt`, which `setup.py` reads them from, was not in the source distribution. `MANIFEST.in` now includes it.
- `CITATION.cff` gives the DOI as `10.22002/D1.20100`, which resolves, and lists all three authors, with Michael Hucka’s name spelled correctly.


## [2.1.2] - 2022-04-12

This version supports parsing the `<correctionDoi>` field in the microPublication XML article list.


## [2.1.1] - 2022-04-09

This version fixes a bug with the generation of zip files for PMC.


## [2.1.0] - 2022-04-08

This version supports microPublication.org's new XML service.


## [2.0.0] - 2021-07-29

This version introduces a modular journal interface to handle a new journal (The Prompt Journal) archived by the Caltech Library. Along with this change, Microarchiver has been renamed _PubArchiver_. Command-line arguments have also been changed.


## [1.12.1] - 2021-06-01

This release  fixes a couple of issues:

* The default network timeout was too short to get large PDF files from micropublication.org. Fixed by tripling the timeout duration.
* Image conversion exceeded an internal default in the Python Pillow package being used for image conversion. Fixed by disabling the size check.


## [1.12.0] - 2021-04-16

Reports can now be written in _both_ CSV and HTML formats.


## [1.11.0] - 2021-04-16

* Add support for specifying the title of the report.
* Fix incorrect count of articles in ZIP file comments.


## [1.10.7] - 2020-12-09

* Test for more signs of failure in `upload-to-pmc.sh`.
* Make some very tiny tweaks to the format of logs.


## [1.10.6] - 2020-12-03

* Assume the use of Python `virtualenv` to lock in a specific Python environment.
* Fix a bug in one of the workflow scripts in which the lack of a mail message body caused the mail command to hang indefinitely.


## [1.10.5] - 2020-11-30

* Add new helper function to run `curl` in the upload script for PMC.
* Fix inconsistency in the PMC upload script, wherein the user and password variables were not the same name as the cron variables actually used.


## [1.10.4] - 2020-10-23

* Fix bug in date handling in workflow scripts.  The value of the `--after-date` argument to `microarchiver` was set to the date it ran, which caused it to miss articles published on the date that it ran.  The value of the date should have been modified to include the day it last ran so that the date comparison was correct.  (Thanks to Nick Stiffler for catching and reporting the problem.)


## [1.10.3] - 2020-10-23

(Mistaken release -- ignore this.)


## [1.10.2] - 2020-10-13

* Update the workflow scripts and associated crontab template.


## [1.10.1] - 2020-10-12

* Fix behavior when DataCite has no data for an article: `microarchiver` was _meant_ to flag the article and keep going, but instead it treated it as a fatal error.
* Fix some documentation errors about the numeric codes returned by `microarchiver`.
* Minor other improvements.


## [1.10.0] - 2020-10-11

This version changes the behavior of the `-@` command-line option, such that exceptions encountered when running with the `-@` option do _not_ cause `microarchiver` to drop into an interactive debugger.  The old behavior turned out to be unhelpful in practice, and moreover, it mixed two behaviors into one command-line flag.  The latter was problematic when running `microarchiver` from scripts.


## [1.9.4] - 2020-10-10

This version removes an unnecessary dependency on wxPython.  A GUI interface was never completed for Microarchiver, and while the starting code is still in the code base in case we try to build a GUI, it doesn't have to be hooked in at this point.  Removing the internal references to the GUI code allows the wxPython requirement to be removed, which in turn simplifies and speeds up installation.


## [1.9.3] - 2020-09-25

* Add missing Python package requirement to requirements.txt.
* Simplify PMC upload script.


## [1.9.2] - 2020-09-25

* Fix broken logos and images in README.md.
* Replace local version of `debug.py` with the use of [Sidetrack](https://github.com/caltechlibrary/sidetrack).
* Use newer approach to recording version and other metadata in `__init__.py` and the release procedure codified in `Makefile`.
* Minor internal changes.


## [1.9.1] - 2020-07-15

* Fix [issue #2](https://github.com/caltechlibrary/microarchiver/issues/2): volume number in file names is incorrectly determined


## [1.9.0] - 2020-07-13

* Support output for PMC using new command-line option `-s`.
* Rename the JATS XML file after the pattern _issn_-_volume_-_doi_.xml, to make it more compatible with output generated for PMC.
* Remove any alpha channels and convert images to RGB.
* Run ZIP files through a simple validation step after creating them.
* Added missing dependencies to [`requirements.txt`](requirements.txt).
* Some internal code changes.


## [1.8.0] - 2020-04-09

* Instead of quitting with an error if the file given to `-a` is empty, `microarchiver` will now just print a warning.


## [1.7.0] - 2020-04-03

* Store JATS XML for each article, as well as any image referenced in the JATS data. Images are converted to uncompressed TIFF before being stored.
* Perform JATS validation for each article by default.
* Add `-X` option to disable automatic JATS DTD validation.
* Change `-a` option to accept a file containing either a list of DOIs or the XML format sent by micropublication.org.
* Change exit code numbering scheme.
* Communicate number of failures in terms of exit codes; see [README](README.md) for more details.
* Test if date given to `-d` is syntactically correct but not a valid date.
* Refactor and change some internal code.
* Fix miscellaneous bugs.


## [1.6.3] - 2019-10-16

* Catch and handle no-content errors more gracefully.
* Detect mangled XML returned by micropublication.org and handle it more gracefully.


## [1.6.2] - 2019-09-21

* Fix crasher in writing comment into zip file because of reference to no-longer-existing package attribute.


## [1.6.1] - 2019-09-20

* Fix broken handling of debug trace output destination.
* Update `README.md` to describe changes to debug flag.


## [1.6.0] - 2019-09-19

* Change the debug flag `-@` to accept an argument for where to send the debug output trace. The behavior change of `-@` is not backward compatible.
* Put metadata in `setup.cfg` and change how Microarchiver gets the metadata internally.


## [1.5.1] - 2019-09-18

* Fix bug in propagating network failures up to the top of main.
* Fix case of variable being shadowed inside a block.


## [1.5.0] - 2019-09-03

* Added new `-g` option to print the raw XML article list from the server.
* Did very minor internal code refactoring.


## [1.4.0] - 2019-08-29

* Added new `scripts` subdirectory with script for use with cron.
* Fixed behavior: if there are no articles to archive, don't create the output directory either.


## [1.3.0] - 2019-08-29

* Now if there are no articles to archive, it won't create a zip file.


## [1.2.0] - 2019-08-29

* Improved installation instructions.
* Changed debug flag from `-Z` to `-@`.
* Internal code changes for message printing & colorization.


## [1.1.0] - 2019-07-31

* **Backwards incompatible change**: command-line arguments have been significantly changed in terms of names and shortcut letters.
* Addition of new `-d` command-line argument, for getting only articles published after a certain date.
* Output is now always created in a subdirectory of the directory given as the value of the `-o` option, rather than directly into that directory. The subdirectory name is always `micropublication-org`.
* When a zip archive is being created (the default case), then the output directory will be deleted afterward.
* Updates to the documentation (top-level `README.md` file) and internal help strings.
* Minor other internal changes.

[Unreleased]: https://github.com/caltechlibrary/pubarchiver/compare/v2.2.0...HEAD
[2.2.0]: https://github.com/caltechlibrary/pubarchiver/compare/v2.1.2...v2.2.0
[2.1.2]: https://github.com/caltechlibrary/pubarchiver/compare/v2.1.1...v2.1.2
[2.1.1]: https://github.com/caltechlibrary/pubarchiver/compare/v2.1.0...v2.1.1
[2.1.0]: https://github.com/caltechlibrary/pubarchiver/compare/fa9307a...v2.1.0
[2.0.0]: https://github.com/caltechlibrary/pubarchiver/compare/v1.12.1...fa9307a
[1.12.1]: https://github.com/caltechlibrary/pubarchiver/compare/v1.12.0...v1.12.1
[1.12.0]: https://github.com/caltechlibrary/pubarchiver/compare/v1.11.0...v1.12.0
[1.11.0]: https://github.com/caltechlibrary/pubarchiver/compare/v1.10.7...v1.11.0
[1.10.7]: https://github.com/caltechlibrary/pubarchiver/compare/v1.10.6...v1.10.7
[1.10.6]: https://github.com/caltechlibrary/pubarchiver/compare/v1.10.5...v1.10.6
[1.10.5]: https://github.com/caltechlibrary/pubarchiver/compare/v1.10.4...v1.10.5
[1.10.4]: https://github.com/caltechlibrary/pubarchiver/compare/v1.10.3...v1.10.4
[1.10.3]: https://github.com/caltechlibrary/pubarchiver/compare/v1.10.2...v1.10.3
[1.10.2]: https://github.com/caltechlibrary/pubarchiver/compare/v1.10.1...v1.10.2
[1.10.1]: https://github.com/caltechlibrary/pubarchiver/compare/v1.10.0...v1.10.1
[1.10.0]: https://github.com/caltechlibrary/pubarchiver/compare/v1.9.4...v1.10.0
[1.9.4]: https://github.com/caltechlibrary/pubarchiver/compare/v1.9.3...v1.9.4
[1.9.3]: https://github.com/caltechlibrary/pubarchiver/compare/v1.9.2...v1.9.3
[1.9.2]: https://github.com/caltechlibrary/pubarchiver/compare/v1.9.1...v1.9.2
[1.9.1]: https://github.com/caltechlibrary/pubarchiver/compare/v1.9.0...v1.9.1
[1.9.0]: https://github.com/caltechlibrary/pubarchiver/compare/v1.8.0...v1.9.0
[1.8.0]: https://github.com/caltechlibrary/pubarchiver/compare/v1.7.0...v1.8.0
[1.7.0]: https://github.com/caltechlibrary/pubarchiver/compare/v1.6.3...v1.7.0
[1.6.3]: https://github.com/caltechlibrary/pubarchiver/compare/v1.6.2...v1.6.3
[1.6.2]: https://github.com/caltechlibrary/pubarchiver/compare/v1.6.1...v1.6.2
[1.6.1]: https://github.com/caltechlibrary/pubarchiver/compare/v1.6.0...v1.6.1
[1.6.0]: https://github.com/caltechlibrary/pubarchiver/compare/v1.5.1...v1.6.0
[1.5.1]: https://github.com/caltechlibrary/pubarchiver/compare/v1.5.0...v1.5.1
[1.5.0]: https://github.com/caltechlibrary/pubarchiver/compare/v1.4.0...v1.5.0
[1.4.0]: https://github.com/caltechlibrary/pubarchiver/compare/v1.3.0...v1.4.0
[1.3.0]: https://github.com/caltechlibrary/pubarchiver/compare/v1.2.0...v1.3.0
[1.2.0]: https://github.com/caltechlibrary/pubarchiver/compare/1.10...v1.2.0
[1.1.0]: https://github.com/caltechlibrary/pubarchiver/releases/tag/1.10
