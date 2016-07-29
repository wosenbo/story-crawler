# -*- coding: utf-8 -*-
import urllib2
import re
import time
import os
import urlparse
import threading
import socket
import Queue
from html2text import html2text

baseurl = "http://www.5aigushi.com/mingjian/"

def showlog(message):
    lock.acquire()
    print message
    lock.release()

def gethtml(url):
    try:
        html = urllib2.urlopen(url).read().decode('gbk', 'ignore')
    except Exception, e:
        showlog("Failed connect " + url)
        html = ""
    return html

def getbaseurl(url):
    return urlparse.urljoin(baseurl, url)

def cacheexists(name):
    cachefile = cachedir + '/' + name
    return os.path.exists(cachefile)

def setcache(name, data):
    cachefile = cachedir + '/' + name
    with open(cachefile, 'wb') as f:
        f.writelines(data)
        f.close()

def getcache(name):
    cachefile = cachedir + '/' + name
    if not os.path.exists(cachefile):
        return
    with open(cachefile, 'r') as f:
        data = f.read()
        f.close()
    return data

def sortlist(lists):
    pass

def formatcontent(content):
    content = re.sub(u'本故事地址.*?</a>', '', content)
    content = re.sub(u'<li>[\s\S]+免费订阅[\s\S]+微信[\s\S]+</li>', '', content)
    content = html2text(content)
    return content.strip()

def gettitle(html):
    match = re.search('<h2>(.+?)</h2>', html)
    if not match:
        return
    return match.group(1)

def getcontent(html):
    regex = '<div class="content">.*?<td>(.+?)</td>[\s\r\n]+</tr>[\s\r\n]+</table>'
    pattern = re.compile(regex, re.S)
    match = pattern.search(html)
    if not match:
        return
    content = match.group(1)
    return content

def crawllist():
    while 1:
        if not listurls:
            showlog("Empty list")
            time.sleep(5)
            continue
        url = listurls.pop(0)
        visitedlisturls.append(url)
        cachename = os.path.basename(url)
        if not cachename:
            cachename = 'index.html'
        html = getcache(cachename)
        if not html:
            html = gethtml(url)
            setcache(cachename, html)
        regex = 'href="(.+?)" class="title"'
        for pageurl in re.findall(regex, html):
            pagequeue.put(getbaseurl(pageurl))
        regex = '<ul class="pagelist">(.+?)</ul>'
        pattern = re.compile(regex, re.S)
        match = pattern.search(html)
        if match:
            for listurl in re.findall('(list_\d+_\d+\.html)', html):
                listurl = getbaseurl(listurl)
                if listurl not in list(listurls + visitedlisturls):
                    listurls.append(listurl)

def crawlpage():
    while 1:
        if pagequeue.empty():
            showlog("Empty page queue")
            time.sleep(5)
            continue
        url = pagequeue.get()
        cachename = os.path.basename(url)
        if cacheexists(cachename):
            continue
        html = gethtml(url)
        setcache(cachename, html)

if __name__ == "__main__":
    socket.setdefaulttimeout(1)
    lock = threading.Lock()
    rootdir = os.path.dirname(os.path.realpath(__file__))
    cachedir = rootdir + '/data/cache'
    pagequeue = Queue.Queue()
    listurls = []
    visitedlisturls = []

    listurls.append(baseurl)
    threading.Thread(target=crawllist).start()
    threading.Thread(target=crawlpage).start()