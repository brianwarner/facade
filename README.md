# Facade
## See who is actually doing the work in your projects

Facade is a program that uses gitdm to analyze the contributors to git repos, 
organized into groups called projects, on an ongoing daily basis.  It is 
(mostly) managed using a web interface, and provides some basic data summaries.  
For more advanced analysis, you can export the contributor data as a CSV.  As 
of now there's absolutely zero authentication, so it's probably best to run it 
on a very private machine.

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
4. Run 'python setup.py'

At this point, you should be able to access facade's web interface.

### Git repo setup:

1. Choose a volume with plenty of storage, and create a directory.
2. Ensure the user account that will run facade-worker.py has r/w permissions.
3. In the web interface, go to Configure and update 'Location of git repos'.

### Gitdm setup:

1. Clone gitdm from git://git.lwn.net/gitdm.git
2. Move it to wherever you want to keep it on the system.
3. In the web interface, go to Configure and update 'Location of gitdm'.
4. There's a patch for gitdm in facade/utilities, if you plan to analyze GitHub repos.

### Worker script setup:

1. Set up a cron job to run utilities/facade-worker.py daily.  It can run more 
or less often, and will generally Do The Right Thing. Cron user must have write 
access to git repo directory.

### Some tips and tricks

Remember that by default, the gitdm analysis goes from the start date up to 
yesterday, and only for repos that are marked as up-to-date.  If a repo fails 
to pull, gitdm won't run because there's no new data.  If at some point in the 
future the repo does pull successfully, the missing dates will be filled in 
automatically.

facade-worker.py will not run if it thinks a previous instanace is still 
running.  The only times this is actually likely would be during the initial 
clone and building of data for large repos (like the kernel) or if you have a 
cron job running facade-worker.py too often.  If for some reason 
facade-worker.py fails, you will need to run reset-status.py before it will run 
again.

If facade-worker.py is taking forever to run, you should verify that your start 
date isn't too early.  Setting this appropriately forward can eliminate a lot 
of unnecessary calculations.  Facade will trim any database data that falls 
outside the date range, which is set in Configuration.

If you discover a bunch of (Unknown) affiliations, don't panic. This probably 
means you are checking a repo with domains that aren't in the stock gitdm 
domain mappings.  You can update the config files in gitdm and Facade will 
detect the changes the next time facade-worker runs.  It will also search for 
any historical (Unknown) affiliations that are now known, and fix them.

The main reason for tags is to be able to isolate a specific subset of data for 
a group of people, for example, your department at work.  Because people and 
their email addresses come and go, you just tell Facade the dates between which 
a certain email should be tagged, and it'll show up in the output.

Last but not least, this is entirely dependent upon Jon Corbet and Greg KH's 
most excellent gitdm.  This would't be possible without their work, which is 
greatly appreciated.

I hope this is helpful to you.  Apologies in advance for inconsistent coding 
styles or cumbersome logic.  Contributions and fixes are welcomed!

Brian
