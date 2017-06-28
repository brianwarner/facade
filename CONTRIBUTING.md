Contributions, fixes, and changes to Facade are welcome, but I do ask that you
follow a few basic guidelines.

1) Please follow kernel conventions and include a Signed-off-by line.

2) Inbound and outbound license is Apache 2.0. Please don't co-mingle code under
other licenses.

3) If you're working on something non-trivial, please file an issue on GitHub so
others are aware (and don't collide with your work).

4) The most likely sources of breakage are weird formatting in commit logs. If
you encounter an error, please restart the analysis with "Debug"-level logging
and include the following in a GitHub issue:
 - The repo that caused the problem
 - The exact error message
 - The previous 10 lines of output

5) Even under the best of circumstances, analyses can take a long time. We keep
track of progress and commit changes to the database often, so that if the
script exits mid-run, we don't have to start back at the beginning. Please keep
this in mind if you're proposing changes to facade-worker.py.

6) If something's confusing or broken, please come find me.

Brian
