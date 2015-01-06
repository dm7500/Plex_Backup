# --------------------------------------------------
# Project: Plex Backup 
# Name:    Plex_Backup 
# Created: 12/29/2014
# Author: David.Martinez
#
# Created using PyCharm Community Edition
#--------------------------------------------------

import module_locator
import os
import subprocess
import sys
import shutil
import logging
import datetime
import dropbox
import zipfile
import errno

#Setting up logging and other housekeeping
myDate = datetime.datetime.now().strftime("%y-%m-%d")
myTime = datetime.datetime.now().strftime("%H:%M")
myDateTime = datetime.datetime.now().strftime("%y-%m-%d %H:%M")

scriptdir = module_locator.module_path()
logdir = scriptdir + '\\logs\\'
tempdir = 'C:\\temp\\Plex Backup-%s\\' % myDate
regbackupfile = tempdir + "PlexRegistry-" + myDate + ".reg"
PlexDBDir = os.environ['LOCALAPPDATA'] + "\\Plex Media Server\\"
PZtemp = tempdir + "PlexBackup-" + myDate + ".zip"
BackupFile = tempdir + "PB-" + myDate + ".zip"
BackupDir = tempdir
allowZip64 = True
DB_appkey = '2tenjnd5fxlxxzj'
DB_appsecret = '7jfpfvnx7seew3i'
ACCESS_TYPE = 'app_folder'
auth_token = 'bB7LjlOoHncAAAAAAAAkCLBdTWfmixI2IMiSy6lSLqAPD6YEgUHYCcFjFleqte6j'
db = dropbox.client.DropboxClient(auth_token)

logger = logging.getLogger('Plex Backup')
logdate = datetime.datetime.now().strftime("%y-%m-%d-%H-%M")
logfile = logdir + '\\PlexBackup-' + logdate + '.log'
hdlr = logging.FileHandler(logfile)
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s' )
hdlr.setFormatter(formatter)
logger.addHandler(hdlr)
logger.setLevel(logging.INFO)
###################################

def make_zipfile(output_filename, source_dir):
    relroot = os.path.abspath(os.path.join(source_dir, os.pardir))
    with zipfile.ZipFile(output_filename, "w", zipfile.ZIP_DEFLATED, allowZip64) as zip:
        for root, dirs, files in os.walk(source_dir):
            # add directory (needed for empty dirs)
            zip.write(root, os.path.relpath(root, relroot))
            for file in files:
                filename = os.path.join(root,file)
                if os.path.isfile(filename): # regular files only
                    arcname = os.path.join(os.path.relpath(root, relroot), file)
                    zip.write(filename, arcname)



def main():
    # logger.info()
    ##############################
    #Setting up directories for logs and temp work
    if not os.path.exists(logdir):
        os.makedirs(logdir)
    if not os.path.exists(tempdir):
        os.makedirs(tempdir)
        logger.info('Temp directory created.')
    ###############################
    #Registry export of Plex hive
    logger.info("Capturing export from Plex registry hive")
    subprocess.call('regedit /E %s "HKEY_CURRENT_USER\\Software\\Plex, Inc.\\Plex Media Server\\"' % regbackupfile, shell=True)
    logger.info("Registry Keys captured.")
    ###############################

    ###############################
    #Captures Zip file from PMS folder, and moves it to temp
    logger.info("Creating ZIP file from PMS data folder.")
    make_zipfile(PZtemp, PlexDBDir)
    zipsize1 = os.path.getsize(PZtemp)
    logger.info("Initial PMS ZIP captured. ZIP size is %s" % zipsize1)
    #todo: Need to parse the zip file size into a readable format.
    ###############################

    ###############################
    #Creates new Zip file containing both PMS dir and regkeys
    logger.info("Creating final ZIP backup file.")
    make_zipfile(BackupFile, tempdir)
    logger.info("Final Backup Zip completed.")
    ################################

    ###################################
    #Uploads the final Zip to Dropbox for archiving
    archiveloc = db.put_file('/PB-' + myDate + '.zip', BackupFile)
    print "uploaded: ", archiveloc
    ###################################

    ###################################
    #This section clears out the temp directory to save space
    logger.info("Removing temp directory")
    shutil.rmtree(tempdir)
    if not os.path.exists(tempdir):
        logger.info("Temp directory cleared")
    else:
        logger.warning("Temp directory not cleared. Please remove manually.")
    ####################################

    ####################################
    #Checks if existing file is older then 7 days, and deletes it if it is.
    for zipf in os.listdir(BackupDir):
        fullpath = os.path.join(BackupFile, zipf)    # turns 'file1.txt' into '/path/to/file1.txt'
        timestamp = os.stat(fullpath).st_ctime  # get timestamp of file
        createtime = datetime.datetime.fromtimestamp(timestamp)
        now = datetime.datetime.now()
        delta = now - createtime
        if delta.days > 7:
            os.remove(fullpath)
            logger.info('%s deleted, as it was older then 7 days.' % fullpath)
    ######################################
    print "All Done. Check it out."


if __name__ == '__main__':
    main()
