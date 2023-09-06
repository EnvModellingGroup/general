#!/bin/sh
# Script obtained from: https://gist.github.com/enoch85/45eba73c49f760905bc2
# This script is used on a QNAP TS-269 PRO. https://www.en0ch.se/qnap-and-rsync/
# 
# You have to change:
# 1. $BKDRIVE
# 2. $EXCLUDES (if you want to change the name of the file servername.excludes)
# 3. $SOURCE & $DESTINATION
# 4. user@yourserver.se for the mysqldump 
# 5. --password=SUPERSECRET
 
TODAY=`date +"%Y%m%d"`
YESTERDAY=`date -d "1 day ago" +"%Y%m%d"`
OLDBACKUP=`date -d "7 days ago" +"%Y%m%d"`

# Remmeber to run as root if you want to store all data (sudo cron -e)
RSYNC="/usr/bin/rsync"

# Where to save it. Don't forget to make sure it exists and is mounted
# This is checked during the script.
BKDRIVE="/backup"
 
# This is a list of files to ignore from backups.
# Dont't forget to touch $EXCLUDES
EXCLUDES="excludes"

#LOG file
# Dont't forget to touch $LOG
LOG="$BKDRIVE/BACKUP_success.log"
 
# Remember that you will not be generating
# backups that are particularly large (other than the initial backup), but that
# you will be creating thousands of hardlinks on disk that will consume inodes.

# Source and Destination
SOURCE="/home/"

DESTINATION="$BKDRIVE/$TODAY/"
 
# Keep database backups in a separate directory.
mkdir -p $BKDRIVE/$TODAY/db

# This command rsync's files from the remote server to the local server.
# Flags:
#   -z enables gzip compression of the transport stream.
#   -e enables using ssh as the transport prototcol.
#   -a preserves all file attributes and permissions.
#   -x (or --one-file-system) Don’t cross filesystem boundaries
#   -v shows the progress.
#   --rsync-path lets us pass the remote rsync command through sudo.
#   --exclude-from points to our configuration of files and directories to skip.
#   --numeric-ids is needed if user ids don't match between the source and
#       destination servers.
#   --delete -r(ecursive) Deletes files from $DESTINATION that are not present on the $SOURCE
#   --link-dest is a key flag. It tells the local rsync process that if the
#       file on the server is identical to the file in ../$YESTERDAY, instead
#       of transferring it create a hard link. You can use the "stat" command
#       on a file to determine the number of hard links. Note that when
#       calculating disk space, du includes disk space used for the first
#       instance of a linked file it encounters. To properly determine the disk
#       space used of a given backup, include both the backup and it's previous
#       backup in your du command.
#
# The "rsync" user is a special user on the remote server that has permissions
# to run a specific rsync command. We limit it so that if the backup server is
# compromised it can't use rsync to overwrite remote files by setting a remote
# destination. I determined the sudo command to allow by running the backup
# with the rsync user granted permission to use any flags for rsync, and then
# copied the actual command run from ps auxww. With these options, under
# Ubuntu, the sudo line is:
#
#   rsync	ALL=(ALL) NOPASSWD: /usr/bin/rsync --server --sender -logDtprze.iLsf --numeric-ids . /
#
# Note the NOPASSWD option in the sudo configuration. For remote
# authentication use a password-less SSH key only allowed read permissions by
# the backup server's root user.
rsync -zavx --exclude-from=$EXCLUDES --numeric-ids  --delete -r --link-dest=../$YESTERDAY $SOURCE $DESTINATION


# Un-hash this if you want to remove old backups (older than 2 days)
rm -R $BKDRIVE/$OLDBACKUP

# Writes a log of successful updates
echo "BACKUP success-$TODAY" >> $LOG

# Clean exit
exit 0
