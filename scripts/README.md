Scripts fro microarchiver
=========================

These are the Bash scripts we use for running `microarchiver` at the Caltech Library.

On our servers, the scripts are invoked using crontab entries based on the text in the file [`crontab.template`](crontab.template).  (The values listed as `CHANGEME` need to be adjusted for the specific computer installation being used.)

The actual scripts are [`archive-in-portico`](archive-in-portico) and [`upload-to-pmc`](upload-to-pmc).  They rely on environment variables to set certain values.  These include the paths where Portico and PMC outputs are stored (set by variables `PORTICO_OUTPUT` and `PMC_OUTPUT`), the account names and passwords for FTP uploads to Portico and PMC, and a Slack API token and channel name.

The scripts assume that certain things are installed on the computer and are in the user's shell command search $path:

* `microarchiver`
* `curl`
* (optional) [`slack-cli`](https://github.com/rockymadden/slack-cli)
* Common Linux/Unix programs such as `sed`, `grep`, `mail`, etc.

Note that some of these programs themselves have additional dependencies of their own.
