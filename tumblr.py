#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Encoding: UTF-8

import math, os
import pytumblr

from modules import (consumer_key, consumer_secret, oauth_token, oauth_secret, 
                     numbering, checkFileExists, downloadFile, animatedTypes, videoTypes, 
                     onError, logFileName, logFileExtension, writeToLog, 
                     writeLogSummary)

##### create client #####
#client = pytumblr.TumblrRestClient(
#    '<consumer_key>',
#    '<consumer_secret>',
#    '<oauth_token>',
#    '<oauth_secret>',
#)

def authenticateClient(verbose):
    
    print "\n--- Authenticating..."
    
    if verbose:
        print "Consumer key: '%s'" % consumer_key
        print "Consumer secret: '%s'" % consumer_secret
        print "OAuth token: '%s'" % oauth_token
        print "OAuth secret: '%s'" % oauth_secret

    # Authenticate via OAuth
    client = pytumblr.TumblrRestClient(
        consumer_key,
        consumer_secret, 
        oauth_token, 
        oauth_secret)
    
    # Make the request
    clientInfo = client.info()
    
    if verbose:
        print "Client info:\n--------------------"
        print clientInfo
    
    return client

def getPosts(client, blog, mainDir, downloadDir, gifDir, videoDir, keepGoing, writeLog, verbose):
    
    from modules import chunkSize
    
    posts = []
    fileList = []
    
    chunkNo = 0
    postNo = 0
    
    mainLogPath = os.path.join(mainDir, "%s.%s" % (logFileName, logFileExtension))
    subLogPath = os.path.join(mainDir, "%s_%s.%s" % (logFileName, blog, logFileExtension))
    
    print "\n--- Getting posts from '%s'" % blog
    writeToLog(mainLogPath, "---------- Getting posts from '%s'" % blog, writeLog, verbose)
    writeToLog(subLogPath, "---------- Getting posts from '%s'" % blog, writeLog, verbose)
    
    blogContents = client.posts(blog, limit=1)
    print "\n%s:\n--------------------" % blog 
    print "Blog: %s" % blogContents['blog']['url']
    print "Total posts: %s" % blogContents['blog']['total_posts']
    writeToLog(subLogPath, "Found %s posts" % blogContents['blog']['total_posts'], writeLog, verbose)
    
    if blogContents['blog']['is_nsfw']:
        print "\nBlog is NOT safe for work"
        writeToLog(subLogPath, "Blog is NOT safe for work", writeLog, verbose)
        
    print
        
    totalPosts = blogContents['total_posts']
    totalChunks = int(math.ceil(totalPosts / chunkSize))
    
    videoTotal = 0
    videoTotalExists = 0
    videoTotalDownloaded = 0
    videoTotalDownloadError = 0
    
    animatedTotal = 0
    animatedTotalExists = 0
    animatedTotalDownloaded = 0
    animatedTotalDownloadError = 0
    
    pictureTotal = 0
    pictureTotalExists = 0
    pictureTotalDownloaded = 0
    pictureTotalDownloadError = 0
    
    byteTotal = 0
    byteTotalExists = 0
    byteTotalDownloaded = 0
    byteTotalDownloadError = 0
    
    while True:
        
        if chunkNo * chunkSize >= totalPosts:
            print "*** No more posts"
            break
        else:
            if writeLog and chunkNo > 0:
                (videoTotal, videoTotalExists, videoTotalDownloaded, videoTotalDownloadError, 
                 animatedTotal, animatedTotalExists, animatedTotalDownloaded, animatedTotalDownloadError, 
                 pictureTotal, pictureTotalExists, pictureTotalDownloaded, pictureTotalDownloadError, 
                 byteTotal, byteTotalExists, byteTotalDownloaded, byteTotalDownloadError) = writeLogSummary(videoTotal, videoTotalExists, videoTotalDownloaded, videoTotalDownloadError, 
                                                                                                            animatedTotal, animatedTotalExists, animatedTotalDownloaded, animatedTotalDownloadError, 
                                                                                                            pictureTotal, pictureTotalExists, pictureTotalDownloaded, pictureTotalDownloadError, 
                                                                                                            byteTotal, byteTotalExists, byteTotalDownloaded, byteTotalDownloadError, 
                                                                                                            subLogPath, chunkNo, writeLog, fileList, verbose)
                     
            chunkNo += 1
            partNo = 0
                
            fileList = []
            
            print "--- Getting %s%s chunk..." % (chunkNo, numbering(chunkNo))
            writeToLog(subLogPath, "Getting %s%s chunk..." % (chunkNo, numbering(chunkNo)), writeLog, verbose)
            print "    Post %s to %s of %s" % (totalPosts - chunkNo * chunkSize + 1, totalPosts - (chunkNo -1) * chunkSize, totalPosts)
            
            offset = totalPosts - chunkNo * chunkSize
            if offset < 0:
                chunkSize = chunkSize + offset
                offset = 0
            #print "    Offset: %s" % offset
            #print "    Chunk size: %s" % chunkSize
            blogContents = client.posts(blog, offset=offset, limit=chunkSize)
            
            for line in blogContents['posts']:
                postNo += 1
                partNo += 1
                print "\n--- Blog: %s" % blog
                print "    Post: %s / %s" % (postNo, totalPosts)
                print "    Chunk: %s / %s" % (chunkNo, totalChunks)
                print "    Part: %s / %s" % (partNo, chunkSize)
                #if verbose:
                #    print line
                posts.append(line)
                
                mediaList = findMedia(line, keepGoing, verbose)
                    
                for line in mediaList:
                    downloadSuccess = False
                    fileSize = 0
                    
                    url, savePath = checkMedia(line, downloadDir, gifDir, videoDir, verbose)
                    
                    fileExists, filePath, fileName = checkFileExists(url, savePath, verbose)
                    
                    if not fileExists:
                        writeToLog(subLogPath, "Downloading %s to %s" % (url, savePath), writeLog, verbose)
                        
                        downloadSuccess, fileName, filePath = downloadFile(url, savePath, verbose)
                    
                        if verbose and not downloadSuccess:
                            print "+++ Failed to download file"
                        if writeLog and downloadSuccess:
                            fileSize = os.path.getsize(filePath)
                        writeToLog(subLogPath, "Downloaded %s\t%s B" % (fileName, fileSize), writeLog, verbose)
                    else:
                        print "+++ Already exists. Skipping file..."
                        
                        if writeLog:
                            fileSize = os.path.getsize(filePath)
                        
                        writeToLog(subLogPath, "%s already exists\t%s B" % (fileName, fileSize), writeLog, verbose)
                    
                    if writeLog:
                        if savePath.endswith(gifDir):
                            fileType = "animated"
                        elif savePath.endswith(videoDir):
                            fileType = "video"
                        else:
                            fileType = "picture"
                            
                        fileList.append({'fileType': fileType, 
                                         'fileName': fileName, 
                                         'fileExists': fileExists, 
                                         'downloadSuccess': downloadSuccess, 
                                         'fileSize': fileSize})
                    
            print "\n--- Posts processed: %s" % len(posts)
    
    print len(posts)
    
    if verbose:
        print blogContents
    
    posts = blogContents
    return posts

def findMedia(post, keepGoing, verbose):
    mediaList = []
    
    if verbose:
        print "Post:"
        print post
        
    if "photos" in post:
        for line in post["photos"]:
            print "Original size url: \n%s" % line["original_size"]["url"]
            if verbose:
                print "Width x height: %s x %s" % (line["original_size"]["width"], line["original_size"]["height"])
            mediaList.append(line["original_size"]["url"])
    elif "video_url" in post:
        print "Video url: \n %s" %  post["video_url"]
        mediaList.append(post["video_url"])
    else:
        if not keepGoing:
            onError(5, "Did not find photos or video")
        
    return mediaList

def checkMedia(line, downloadDir, gifDir, videoDir, verbose):
    url = line
    
    savePath = downloadDir
    
    for fileType in animatedTypes:
        if url.lower().endswith(fileType):
            if verbose:
                print "File is animated"
            savePath = gifDir
            break
    
    if savePath != gifDir:
        for fileType in videoTypes:
            if url.lower().endswith(fileType):
                if verbose:
                    print "File is video"
                savePath = videoDir
                break
    
    if verbose and savePath != gifDir and savePath != videoDir:
        print "File is not animated and not video"
        
    return url, savePath
    
    
    
    
    
    
    
     