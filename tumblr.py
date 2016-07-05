#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Encoding: UTF-8

import sys
import pytumblr

from modules import (consumer_key, consumer_secret, oauth_token, oauth_secret, chunkSize, 
                     numbering, downloadFile, animatedTypes, videoTypes)


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

def getPosts(client, blog, downloadDir, gifDir, videoDir, verbose):
    from modules import chunkSize
    posts = []
    
    chunkNo = 0
    
    print "\n--- Getting posts from '%s'" % blog
    
    blogContents = client.posts(blog, limit=1)
    print "\n%s:\n--------------------" % blog 
    print "Blog: %s" % blogContents['blog']['url']
    print "Total posts: %s" % blogContents['blog']['total_posts']
    if blogContents['blog']['is_nsfw']:
        print "\nBlog is NOT safe for work"
    print
        
    totalPosts = blogContents['total_posts']
    
    #totalPosts = 115
    
    while True:
        if chunkNo * chunkSize >= totalPosts:
            print "*** No more posts"
            break
        else:
            chunkNo += 1
            print "--- Getting %s%s chunk..." % (chunkNo, numbering(chunkNo)) 
            print "    Post %s to %s of %s" % (totalPosts - chunkNo * chunkSize + 1, totalPosts - (chunkNo -1) * chunkSize, totalPosts)
            offset = totalPosts - chunkNo * chunkSize
            if offset < 0:
                chunkSize = chunkSize + offset
                offset = 0
            #print "    Offset: %s" % offset
            #print "    Chunk size: %s" % chunkSize
            blogContents = client.posts(blog, offset=offset, limit=chunkSize)
            for line in blogContents['posts']:
                if verbose:
                    print line
                posts.append(line)
                mediaList = findMedia(line, verbose)
                
                for line in mediaList:
                    url, path = checkFile(line, downloadDir, gifDir, videoDir, verbose)
                    downloadFile(url, path, verbose)
                    
            print
            print "--- Posts downloaded: %s" % len(posts)
            
            if chunkNo == 20:
                sys.exit(0)
    
    print len(posts)
    
    if verbose:
        print blogContents
    
    posts = blogContents
    return posts

def findMedia(post, verbose):
    mediaList = []
    if verbose:
        print "Post:"
        print post
    for line in post["photos"]:
        print
        print "Original size url: \n%s" % line["original_size"]["url"]
        print "Width x height: %s x %s" % (line["original_size"]["width"], line["original_size"]["height"])
        
        mediaList.append(line["original_size"]["url"])
        
    return mediaList

def checkFile(line, downloadDir, gifDir, videoDir, verbose):
    url = line
    
    path = downloadDir
    
    for fileType in animatedTypes:
        if url.lower().endswith(fileType):
            if verbose:
                print "File is animated"
            path = gifDir
            break
    
    if path != gifDir:
        for fileType in videoTypes:
            if url.lower().endswith(fileType):
                if verbose:
                    print "File is video"
                path = videoDir
                break
    
    if verbose and path != gifDir and path != videoDir:
        print "File is not animated and not video"
        
    return url, path
    
    
    
    
    
    
    
     