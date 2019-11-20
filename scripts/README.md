Scripts fro microarchiver
=========================

These are scripts for running microarchiver at the Caltech Library.  On our servers, the script is invoked using a crontab entry that looks like this:

```
MAILTO=MMM@caltech.edu
0 10 * * 6 . $HOME/.profile; FTP_USER=UUU FTP_PASS=PPP /path/to/scripts/archive-micropublication
```

where `MMM`, `UUU`, and `PPP` are filled in with actual values (not shown here for security reasons).  The `.` ahead of `$HOME/.profile` causes the user's profile to be sourced, so that the user's environment (including the `$path` and environment variables) are available to cron when it executes the rest of the command line.

