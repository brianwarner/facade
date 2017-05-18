# Facade
## See who is actually doing the work in your projects

Facade is a program that analyzes the contributors to git repos, organized into
groups called projects, on a commit-by-commit basis.  It is (mostly) managed
using a web interface, and provides some basic data summaries.  For more
advanced analysis, you can export the contributor data as a CSV.  While there is
basic authentication, it's probably best to run it on a private machine.

Facade is licensed under GPL v2.

### Server setup:

1. Install Apache, PHP, Python, and Mysql. On Debian, run install_deps.sh
2. Make sure mod_php and mod_rewrite are enabled.
3. Change Overrides None to Overrides All in your site configuration.
4. Move the Facade files to your webroot.

### Mysql setup:

1. Create a database, a user, and grant all privileges.
2. Copy includes/db.php.default to includes/db.php, add credentials.
3. Copy utilities/db.py.default to utilities/db.py, add credentials.
4. Run 'python utilities/setup.py'

At this point, you should be able to access facade's web interface.

### Git repo setup:

1. Choose a volume with plenty of storage, and create a directory.
2. Ensure the user account that will run facade-worker.py has r/w permissions.
3. In the web interface, go to Configure and update 'Location of git repos'.

### Worker script setup:

Set up a cron job to run utilities/facade-worker.py daily.  It can run more
or less often, and will generally Do The Right Thing. Cron user must have write
access to git repo directory.

### Some tips and tricks

Facade works by cloning a git repo, calculating the parents of HEAD (bounded by
the start date), and scaping each patch for statistics. It calculates lines
added and removed, whitespace changes, patch counts, and unique contributors
over a given period of time. Each time facade-worker.py runs, it recalculates
the parents and trims any that have disappeared (for example, if the start date
changes) or that were introduced (a freshly-merged branch).

facade-worker.py will not run if it thinks a previous instanace is still
running.  This could happen when you're doing the initial clone and building of
data for large repos (like the kernel) or if you have a cron job running
facade-worker.py too often.  If for some reason facade-worker.py fails, you will
need to run reset-status.py before it will run again.  You may also want to
decrease the frequency of your cron job.

If facade-worker.py is taking forever to run, you should verify that your start
date isn't too early.  Setting this appropriately forward can eliminate a lot of
unnecessary calculations.

If you discover a bunch of (Unknown) affiliations, don't panic. This probably
means you are analyzing a repo with domains that aren't in the stock domain
mappings.  You can import config files from gitdm using the
import_gitdm_configs.py script in utilities/ and run Facade with the -n option
to force a rebuild of affiliation data.

The main reason for tags is to be able to isolate a specific subset of data for
a group of people, for example, your department at work.  Because people and
their email addresses come and go, you just tell Facade the dates between which
a certain email should be tagged, and it'll show up in the output.

I hope this is helpful to you.  Apologies in advance for inconsistent coding
styles or cumbersome logic.  Contributions and fixes are welcomed!

Brian
