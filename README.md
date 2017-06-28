# Facade
## See who is actually doing the work in your projects

Facade is a program that analyzes the contributors to git repos, organized into
groups called projects, on a commit-by-commit basis.  It is (mostly) managed
using a web interface, and provides some basic data summaries.  For more
advanced analysis, you can export the contributor data as a CSV.  While there is
basic authentication, it's probably best to run it on a private machine.

Facade is licensed under Apache 2.0.

### Server setup:

1. Install Apache, PHP, Python, and Mysql. On Debian, run install_deps.sh
2. Make sure mod_php and mod_rewrite are enabled.
3. Change Overrides None to Overrides All in your site configuration.
4. Move the Facade files to your webroot.

### Mysql setup:

1. Create a database, a user, and grant all privileges (optional, or Facade can
do this for you during setup if you have the root mysql password).
2. Run 'python utilities/setup.py'

You can optionally choose to use a different database for the affiliation and
alias data, which maps email addresses to organizations. This is useful if you
have a few instances of Facade, and only want to do these mappings once. It
should go without saying that you shouldn't clear the affiliation and alias data
during setup if you're choosing to use an external database for this, as you'll
wipe out your hard work elsewhere.

At this point, you should be able to access facade's web interface.

### Git repo setup:

1. By default, Facade will clone git repos into its own directory. You can
change this in the web configuration.
2. Ensure the user account that will run facade-worker.py has r/w permissions.

### Worker script setup:

Set up a cron job to run utilities/facade-worker.py daily.  It can run more
or less often, and will generally Do The Right Thing to get caught up on
analysis data.  The first run is very resource intensive, because it must scrape
every commit.  After that it'll detect the commits it hasn't already processed,
and just scrape those.  Things get much faster at that point.

You can also just run facade-worker.py whenever you want, and it'll update
everything on the spot.

### Some tips and tricks

Facade is known to work on Linux Mint 18, with Apache 2.4.18, Python 2.7.12, PHP
7.0.18, and mysql 5.7.17. For best results, try these versions (or higher).

Facade works by cloning a git repo, calculating the parents of HEAD (bounded by
the start date), and scraping each patch for statistics. It calculates lines
added and removed, whitespace changes, patch counts, and unique contributors
over a given period of time. Each time facade-worker.py runs, it recalculates
the parents and trims any commits that have disappeared (for example, if the
start date changes or something was reverted) or that were introduced (new
commits or a freshly-merged branch).

facade-worker.py will not run if it thinks a previous instance is still running.
This could happen when you're doing the initial clone and building of data for
large repos (like the kernel) or if you have a cron job running facade-worker.py
too frequently.  If for some reason facade-worker.py fails and exits early, you
will need to run reset-status.py before it will run again.  You may also want to
decrease the frequency of your cron job.

The command line options for facade-worker.py are documented, and you can run
the various parts of the analysis separately. Use the -h flag to find out what
your options are.

If facade-worker.py is taking forever to run, you should verify that your start
date isn't too early.  Setting this appropriately forward can eliminate a lot of
unnecessary calculations.

If you discover a bunch of (Unknown) affiliations, don't panic. This probably
means you are analyzing a repo with domains that aren't in the stock domain
mappings.  You have a few options here:

1. The easiest way is to enter the affiliation data on the People page. This
causes Facade to rebuild affiliation data for anyone who matches the domain or
email address.

2. The more complicated but faster way is to import config files from gitdm
using the import_gitdm_configs.py script in utilities/

After you do one of the two, you MUST run facade-worker.py at least once for the
changes to be reflected in the web UI.

If you think your affiliation data isn't right, you can always nuke it (yes
really).  Facade looks for any results where the author or committer affiliation
is NULL, and then fills those.  This can trigger very, very long analysis jobs
though, so use it wisely.  Running facade-worker.py -n will do this for you.

If you think your analysis data is corrupt, you can also nuke it (yes really).
Facade will just detect that there is no stored commit data, so it'll rebuild
everything from scratch.  You can do this by deleting all the rows from the
analysis_data table in the database.  The next run will rebuild all of it.

The main reason for tags is to be able to isolate a specific subset of data for
a group of people, for example, your department at work.  Because people and
their email addresses come and go, you just tell Facade the dates between which
a certain email should be tagged, and it'll show up in the output.

Finally, you can choose whether you want statistics on the web UI organized by
author or committer email, and by author or committer date. The default is
author email and committer date, but you can change it up on the configuration
page. You'll need to run facade-worker.py at least once to see the changes.

I hope this is helpful to you.  Apologies in advance for inconsistent coding
styles or cumbersome logic.  Contributions and fixes are welcomed!

Brian
