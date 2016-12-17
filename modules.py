#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Encoding: UTF-8

import ConfigParser, os, sys
from urllib2 import urlopen, URLError, HTTPError

config = ConfigParser.ConfigParser()  # define config file
config.read("%s/config.ini" % os.path.dirname(os.path.realpath(__file__)))  # read config file

consumer_key = config.get('tumblr_api_keys', 'consumer_key').strip(" ")
consumer_secret = config.get('tumblr_api_keys', 'consumer_secret').strip(" ")
oauth_token = config.get('tumblr_api_keys', 'oauth_token').strip(" ")
oauth_secret = config.get('tumblr_api_keys', 'oauth_secret').strip(" ")

chunkSize = int(config.get('tumblr_options', 'chunkSize'))

defaultDownloadDir = config.get('directory_settings', 'defaultDownloadDir').lstrip(" ").rstrip(" ")
subDir = config.get('directory_settings', 'subDir').lstrip(" ").rstrip(" ")
gifDir = config.get('directory_settings', 'gifDir').lstrip(" ").rstrip(" ")
videoDir = config.get('directory_settings', 'videoDir').lstrip(" ").rstrip(" ")
tempFileExtension = config.get('directory_settings', 'tempFileExtension')

animatedTypes = config.get('file_types', 'animatedTypes').replace(" ", "").split(",")
videoTypes = config.get('file_types', 'videoTypes').replace(" ", "").split(",")

def onError(errorCode, extra):
    print "\nError %s" % errorCode
    if errorCode == 1:
        print extra
        usage(errorCode)
    elif errorCode == 2:
        print "No options given"
        usage(errorCode)
    elif errorCode in (4, 5):
        print extra
        sys.exit(errorCode)
    elif errorCode == 3:
        print extra
        return
        
def usage(exitCode):
    print "\nUsage:"
    print "----------------------------------------"
    print "%s -b <blog_name> " % sys.argv[0]
    print "\nMisc options:"
    print "-v    verbose output"
    print "-h    prints this"

    sys.exit(exitCode)
    
def numbering(number):
    if number == 1:
        text = "st"
    elif number == 2:
        text = "nd"
    elif number == 3:
        text = "rd"
    else:
        text = "th"
        
    return text

def checkDirectories(defaultDownloadDir, subDir, blog, gifDir, videoDir, verbose):
    downloadDir = defaultDownloadDir
    
    if not downloadDir.startswith("/"):
        homeDir = os.path.expanduser('~')
        if verbose:
            print "Home directory: %s" % homeDir
        downloadDir = os.path.join(homeDir, downloadDir)
    if verbose:
        print "Download directory: %s" % downloadDir
        
    checkDirectory(downloadDir, verbose)
    
    downloadDir = os.path.join(downloadDir, subDir)
    checkDirectory(downloadDir, verbose)
    
    downloadDir = os.path.join(downloadDir, blog)
    checkDirectory(downloadDir, verbose)
    
    gifDir = os.path.join(downloadDir, gifDir)
    checkDirectory(gifDir, verbose)
    
    videoDir = os.path.join(downloadDir, videoDir)
    checkDirectory(videoDir, verbose)
    
    return downloadDir, gifDir, videoDir

def checkDirectory(path, verbose):
    if os.path.isdir(path):
        if verbose:
            print "%s exists" % path
    else:
        onError(3, "%s does NOT exist!" % path)
        print "Creating it..."
        os.makedirs(path)

    if os.access(path, os.W_OK):
        if verbose:
            print "%s is writeable" % path
    else:
        onError(4, "%s is NOT writeable" % path)
        
    if verbose:
        print "Deleting .%s files..."
    oldTempFiles = [ f for f in os.listdir(path) if f.endswith(".%s" % tempFileExtension) ]
    for f in oldTempFiles:
        os.remove(os.path.join(path, f))
        
def checkFileExists(url, path, verbose):
    fileExists = False
    
    fileName = url.split('/')[-1]
    
    if verbose:
        print "Checking if %s exists at \n %s ..." % (fileName, path)
        
    path = os.path.join(path, fileName)
    
    if os.path.isfile(path):
        fileExists = True
        if verbose:
            print "File already downloaded"
        
    return fileExists
        
def downloadFile(url, path, verbose):
    
    fileName = url.split('/')[-1]
    path = os.path.join(path, fileName)
    
    if verbose:
        print
        print "Downloading \n%s \nto \n%s" % (url, path)
    
    # Open the url
    print "Downloading..."
    try:
        f = urlopen(url)

        # Open our local file for writing
        with open("%s.%s" % (path, tempFileExtension), "wb") as local_file:
            local_file.write(f.read())

    #handle errors
    except HTTPError, e:
        print "HTTP Error:", e.code, url
    except URLError, e:
        print "URL Error:", e.reason, url
        
    else:
        os.rename("%s.%s" % (path, tempFileExtension), path)
        