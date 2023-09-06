#!/bin/sh

##################################################
#needs to be run as root (to preserve permissions)
##################################################

#the mount point of the drive using for your backups
BACKUP_DIR='/backup'

mountpoint ${BACKUP_DIR} && /usr/bin/rsync -az --ignore-errors --delete --delete-excluded --exclude "snap" --exclude "tethys" --exclude "VirtualBox VMs" --exclude "filestore" --exclude "h_drive" --exclude "Google Drive" --exclude "Dropbox" --exclude "firedrake" --exclude "telemac" --exclude "*.iso" /home $BACKUP_DIR > /tmp/rsyncErr

if [ -s /tmp/rsyncErr ]; then
#send you an email with any messages (errors) returned by the script.
    mail -s "rsyncErr backupserver from mainserver" jon.hill@york.ac.uk < /tmp/rsyncErr
fi;
