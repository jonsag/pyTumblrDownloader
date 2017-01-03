#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Encoding: UTF-8

import ConfigParser, os, sys
from urllib2 import urlopen, URLError, HTTPError
from datetime import datetime

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
logFileName = config.get('directory_settings', 'logFileName')
logFileExtension = config.get('directory_settings', 'logFileExtension')

animatedTypes = config.get('file_types', 'animatedTypes').replace(" ", "").split(",")
videoTypes = config.get('file_types', 'videoTypes').replace(" ", "").split(",")

fileSizeSuffixes = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']

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
    print "-k    keep going on non fatal errors"
    print "-l    write log files"
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
    
    mainDir = os.path.join(downloadDir, subDir)
    checkDirectory(downloadDir, verbose)
    
    downloadDir = os.path.join(mainDir, blog)
    checkDirectory(downloadDir, verbose)
    
    gifDir = os.path.join(downloadDir, gifDir)
    checkDirectory(gifDir, verbose)
    
    videoDir = os.path.join(downloadDir, videoDir)
    checkDirectory(videoDir, verbose)
    
    return mainDir, downloadDir, gifDir, videoDir

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
        
    filePath = os.path.join(path, fileName)
    
    if os.path.isfile(filePath):
        fileExists = True
        if verbose:
            print "File already downloaded"
        
    return fileExists, filePath, fileName
        
def downloadFile(url, path, verbose):
    downloadSuccess = False
    
    fileName = url.split('/')[-1]
    fullPath = os.path.join(path, fileName)
    
    if verbose:
        print
        print "Downloading \n%s \nto \n%s" % (url, fullPath)
    
    # Open the url
    print "Downloading..."
    try:
        f = urlopen(url)

        # Open our local file for writing
        with open("%s.%s" % (fullPath, tempFileExtension), "wb") as local_file:
            local_file.write(f.read())

    #handle errors
    except HTTPError, e:
        print "HTTP Error:", e.code, url
        downloadSuccess = False
    except URLError, e:
        print "URL Error:", e.reason, url
        downloadSuccess = False
    except:
        print "Error"
        downloadSuccess = False
        
    else:
        os.rename("%s.%s" % (fullPath, tempFileExtension), fullPath)
        downloadSuccess = True
        
    return downloadSuccess, fileName, fullPath
        
def writeToLog(logFile, logMessage, writeLog, verbose):
    
    if writeLog:
        if verbose:
            print "--- Writing to log file %s ..." % logFile
            print "    %s" % logMessage
        with open(logFile, "a") as myLog:
            myLog.write("\n%s\t%s" % (str(datetime.now()), logMessage))
        
def humanFileSize(nbytes):
    if nbytes == 0: return '0 B'
    i = 0
    while nbytes >= 1024 and i < len(fileSizeSuffixes)-1:
        nbytes /= 1024.
        i += 1
    f = ('%.2f' % nbytes).rstrip('0').rstrip('.')
    return '%s %s' % (f, fileSizeSuffixes[i])

def writeLogSummary(videoTotal, videoTotalExists, videoTotalDownloaded, videoTotalDownloadError, 
                    animatedTotal, animatedTotalExists, animatedTotalDownloaded, animatedTotalDownloadError, 
                    pictureTotal, pictureTotalExists, pictureTotalDownloaded, pictureTotalDownloadError, 
                    byteTotal, byteTotalExists, byteTotalDownloaded, byteTotalDownloadError, 
                    subLogPath, chunkNo, writeLog, fileList, verbose):
    
    videoChunk = 0
    videoChunkExists = 0
    videoChunkDownloaded = 0
    videoChunkDownloadError = 0
    
    animatedChunk = 0
    animatedChunkExists = 0
    animatedChunkDownloaded = 0
    animatedChunkDownloadError = 0
    
    pictureChunk = 0
    pictureChunkExists = 0
    pictureChunkDownloaded = 0
    pictureChunkDownloadError = 0
    
    byteChunk = 0
    byteChunkExists = 0
    byteChunkDownloaded = 0
    byteChunkDownloadError = 0
    
    writeToLog(subLogPath, "Generating summary after chunk no %s:" % chunkNo, writeLog, verbose)
    for line in fileList:
        if line['fileType'] == "video":
            videoTotal += 1
            videoChunk += 1
            if line['fileExists']:
                videoTotalExists += 1
                videoChunkExists += 1
            elif line['downloadSuccess']:
                videoTotalDownloaded += 1
                videoChunkDownloaded += 1
            else:
                videoTotalDownloadError += 1
                videoChunkDownloadError += 1
                
        elif line['fileType'] == "animated":
            animatedTotal += 1
            animatedChunk += 1
            if line['fileExists']:
                animatedTotalExists += 1
                animatedChunkExists += 1
            elif line['downloadSuccess']:
                animatedTotalDownloaded += 1
                animatedChunkDownloaded += 1
            else:
                animatedTotalDownloadError += 1
                animatedChunkDownloadError += 1
                
        elif line['fileType'] == "picture":
            pictureTotal += 1
            pictureChunk += 1
            if line['fileExists']:
                pictureTotalExists += 1
                pictureChunkExists += 1
            if line['fileExists']:
                pictureTotalDownloaded += 1
                pictureChunkDownloaded += 1
            else:
                pictureTotalDownloadError += 1
                pictureChunkDownloadError += 1
            
        byteTotal = byteTotal + int(line['fileSize'])
        byteChunk = byteChunk + int(line['fileSize'])
        if line['fileExists']:
            byteTotalExists = byteTotalExists + int(line['fileSize'])
            byteChunkExists = byteChunkExists + int(line['fileSize'])
        if line['fileExists']:
            byteTotalExists = byteTotalExists + int(line['fileSize'])
            byteChunkExists = byteChunkExists + int(line['fileSize'])
        else:
            byteTotalDownloadError = byteTotalDownloadError + int(line['fileSize'])
            byteChunkDownloadError = byteChunkDownloadError + int(line['fileSize'])
        
    writeToLog(subLogPath, 
               "Videos this chunk:"+
               "\n\t\t\t\tVideos: %s" % videoChunk+
               "\n\t\t\t\tVideos existed: %s" % videoChunkExists+
               "\n\t\t\t\tVideos downloaded: %s" % videoChunkDownloaded+
               "\n\t\t\t\tFailed video downloads: %s" % videoChunkDownloadError+
               "\n\t\t\t\tVideos processed: %s" % (videoChunkExists + 
                                                   videoChunkDownloaded + 
                                                   videoChunkDownloadError)+
               "\n\n\t\t\t\tAnimated this chunk:"+
               "\n\t\t\t\tAnimated: %s" % animatedChunk+
               "\n\t\t\t\tAnimateds existed: %s" % animatedChunkExists+
               "\n\t\t\t\tAnimateds downloaded: %s" % animatedChunkDownloaded+
               "\n\t\t\t\tFailed animated downloads: %s" % animatedChunkDownloadError+
               "\n\t\t\t\tAnimateds processed: %s" % (animatedChunkExists + 
                                                      animatedChunkDownloaded + 
                                                      animatedChunkDownloadError)+
               "\n\n\t\t\t\tPictures this chunk:"+
               "\n\t\t\t\tPictures: %s" % pictureChunk+
               "\n\t\t\t\tPictures existed: %s" % pictureChunkExists+
               "\n\t\t\t\tPictures downloaded: %s" % pictureChunkDownloaded+
               "\n\t\t\t\tFailed pictures downloads: %s" % pictureChunkDownloadError+
               "\n\t\t\t\tPicturess processed: %s" % (pictureChunkExists + 
                                                      pictureChunkDownloaded + 
                                                      pictureChunkDownloadError)+
               "\n\n\t\t\t\tBytes this chunk:"+
               "\n\t\t\t\tSize: %s B\t%s" % (byteChunk, humanFileSize(byteChunk))+
               "\n\t\t\t\tBytes existed: %s" % byteChunkExists+
               "\n\t\t\t\tNytes downloaded: %s" % byteChunkDownloaded+
               "\n\t\t\t\tFailed byte downloads: %s" % byteChunkDownloadError+
               "\n\t\t\t\tBytes processed: %s" % (byteChunkExists + 
                                                  byteChunkDownloaded + 
                                                  byteChunkDownloadError)+
               
               "\n\n\t\t\t\tVideos total:"+
               "\n\t\t\t\tVideos: %s" % videoTotal+
               "\n\t\t\t\tVideos existed: %s" % videoTotalExists+
               "\n\t\t\t\tVideos downloaded: %s" % videoTotalDownloaded+
               "\n\t\t\t\tFailed video downloads: %s" % videoTotalDownloadError+
               "\n\t\t\t\tVideos processed: %s" % (videoTotalExists + 
                                                   videoTotalDownloaded + 
                                                   videoTotalDownloadError)+
               "\n\n\t\t\t\tAnimated total:"+
               "\n\t\t\t\tAnimated: %s" % animatedTotal+
               "\n\t\t\t\tAnimated existed: %s" % animatedTotalExists+
               "\n\t\t\t\tAnimateds downloaded: %s" % animatedTotalDownloaded+
               "\n\t\t\t\tFailed animated downloads: %s" % animatedTotalDownloadError+
               "\n\t\t\t\tAnimateds processed: %s" % (animatedTotalExists + 
                                                      animatedTotalDownloaded + 
                                                      animatedTotalDownloadError)+
               "\n\n\t\t\t\tPictures total:"
               "\n\t\t\t\tPictures: %s" % pictureTotal+
               "\n\t\t\t\tPictures existed: %s" % pictureTotalExists+
               "\n\t\t\t\tPictures downloaded: %s" % pictureTotalDownloaded+
               "\n\t\t\t\tFailed picture downloads: %s" % pictureTotalDownloadError+
               "\n\t\t\t\tPictures processed: %s" % (pictureTotalExists + 
                                                     pictureTotalDownloaded + 
                                                     pictureTotalDownloadError)+
               "\n\n\t\t\t\tBytes total:"+
               "\n\t\t\t\tSize: %s B\t%s" % (byteTotal, humanFileSize(byteTotal))+
               "\n\t\t\t\tBytes existed: %s B\t%s" % (byteTotalExists,  humanFileSize(byteTotalExists))+
               "\n\t\t\t\tBytes downloaded: %s B\t%s" % (byteTotalDownloaded, humanFileSize(byteTotalDownloaded))+
               "\n\t\t\t\tFailed byte downloads: %s B\t%s" % (byteTotalDownloadError, humanFileSize(byteTotalDownloadError))+
               "\n\t\t\t\tBytes processed: %s B\t%s" % ((byteTotalExists + 
                                                         byteTotalDownloaded + 
                                                         byteTotalDownloadError), 
                                                         humanFileSize((byteTotalExists + 
                                                                        byteTotalDownloaded + 
                                                                        byteTotalDownloadError))),  
               writeLog, verbose)  
    
    return (videoTotal, videoTotalExists, videoTotalDownloaded, videoTotalDownloadError, 
            animatedTotal, animatedTotalExists, animatedTotalDownloaded, animatedTotalDownloadError, 
            pictureTotal, pictureTotalExists, pictureTotalDownloaded, pictureTotalDownloadError, 
            byteTotal, byteTotalExists, byteTotalDownloaded, byteTotalDownloadError)
        
        
        
        
        
        