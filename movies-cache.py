#!/usr/bin/env python
import orjson
import json
import boto3
import botocore
import os
import re
import sys
import multiprocessing
import traceback
#
# Looking to query by:
#  - Year
#  - Movie Title
#  - Cast Member
#  - Genre
#

movieLastModified = ''
movies = []
moviesJson = ""
cacheMovies = dict()
cacheAllYears = set()
cacheAllTitles = set()
cacheAllCast = set()
cacheAllGenres = set()
cachedIndexFile = "movie-query-cache-index.json"
movieJsonFile = "movie-copy.json"

if (os.environ.get('AB_MOVIE_S3_URL') == None):
    url = ''
else:
    url = os.environ.get('AB_MOVIE_S3_URL')

# Update movies from S3
def getMoviesFromS3(url):
    global movieLastModified
    global movies
    global movies_initial
    global moviesJson
    pattern = '^s3://([^/]+)/(.+)$'
    result = re.search(pattern, url)
    if result:
        s3bucket = result.group(1)
        s3key = result.group(2)
        session = boto3.session.Session()
        if (os.environ.get('AWS_ACCESS_KEY_ID') == None):
            s3 = session.client('s3', config=botocore.client.Config(signature_version=botocore.UNSIGNED))
        elif (os.environ.get('AWS_SECRET_ACCESS_KEY') == None):
            s3 = session.client('s3', config=botocore.client.Config(signature_version=botocore.UNSIGNED))
        else:
            s3 = session.client('s3')

        # Get the object and compare the last-modified and update if different
        try:
            s3MovieInfo=s3.get_object(Bucket=s3bucket, Key=s3key)
            if (s3MovieInfo["ResponseMetadata"]["HTTPHeaders"]["last-modified"] != movieLastModified):
                movieLastModified = s3MovieInfo["ResponseMetadata"]["HTTPHeaders"]["last-modified"]
                moviesJson = s3MovieInfo["Body"].read()
                movies_initial = orjson.loads(moviesJson)
                movies = movies_initial
                cacheFu() 
        except Exception as e:
            print("[ERROR] Error accesssing S3: %s." % (url))
            print(traceback.format_exec())
            return 1
    else:
        print("[ERROR] Malformed S3 Repository URL given: ", url)
        return 1

# Search the movie data structure lists
def searchMovieList(key, value):
    results = list()
    for i, movie in enumerate(movies):
        if type(movie[key]) == list:
            if value in movie[key]:
                results.append(i)
    return results

# Search the movie data structure strings
def searchMovieStr(key, value):
    results = list()
    for i, movie in enumerate(movies):
        if str(movie[key]) == value:
            results.append(i)
    return results

def cacheStoreYear(value):
    v = dict()
    v[value] = searchMovieStr("year",value)
    queue.put(v)

def cacheStoreGenres(value):
    v = dict()
    v[value] = searchMovieList("genres",value)
    queue.put(v)

def cacheStoreTitle(value):
    v = dict()
    v[value] = searchMovieStr("title",value)
    queue.put(v)

def cacheStoreCast(value):
    v = dict()
    v[value] = searchMovieList("cast",value)
    queue.put(v)


def init_worker(shared_queue):
    global queue
    queue = shared_queue

# Cache everything to achieve fast response time
def cacheFu():
    cachedIndex = []
    # check if the cache file exists
    if os.path.isfile(cachedIndexFile):
        with open(cachedIndexFile) as cachedIndexFileD:
            cachedIndex = json.load(cachedIndexFileD)
    if "last-modified" in cachedIndex:
        if (cachedIndex["last-modified"] == movieLastModified):
            return None
    global cacheMovies 
    sq = multiprocessing.SimpleQueue()
    cacheMovies["year"] = dict()
    cacheMovies["titles"] = dict()
    cacheMovies["cast"] = dict()
    cacheMovies["genres"] = dict()
    cacheMovies["last-modified"] = movieLastModified
    global cacheAllYears 
    global cacheAllTitles 
    global cacheAllCast 
    global cacheAllGenres
    for movie in movies:
        cacheAllYears.add(str(movie["year"]))
        cacheAllTitles.add(str(movie["title"]))
        cacheAllCast.update(movie["cast"])
        cacheAllGenres.update(movie["genres"])
    print("[INFO] Caching Year Queries. Total items:", len(cacheAllYears))
    with multiprocessing.Pool(initializer=init_worker, initargs=(sq,)) as pool:
        _ = pool.imap(cacheStoreYear,cacheAllYears)
        for i,v in enumerate(cacheAllYears):
            sys.stdout.write("Year Cache Generation: %-3d%% \r" % (i/len(cacheAllYears)*100))
            sys.stdout.flush()
            r = sq.get()
            for k in r:
                cacheMovies["year"][k]=r[k]
    print("[INFO] Caching Genre Queries. Total items:", len(cacheAllGenres))
    with multiprocessing.Pool(initializer=init_worker, initargs=(sq,)) as pool:
        _ = pool.imap(cacheStoreGenres,cacheAllGenres)
        for i,v in enumerate(cacheAllGenres):
            sys.stdout.write("Genre Cache Generation: %-3d%% \r" % (i/len(cacheAllGenres)*100))
            sys.stdout.flush()
            r = sq.get()
            for k in r:
                cacheMovies["genres"][k]=r[k]
    print("[INFO] Caching Title Queries. Total items:", len(cacheAllTitles))
    with multiprocessing.Pool(initializer=init_worker, initargs=(sq,)) as pool:
        _ = pool.imap(cacheStoreTitle,cacheAllTitles)
        for i,v in enumerate(cacheAllTitles):
            sys.stdout.write("Title Cache Generation: %-3d%% \r" % (i/len(cacheAllTitles)*100))
            sys.stdout.flush()
            r = sq.get()
            for k in r:
                cacheMovies["titles"][k]=r[k]
    print("[INFO] Caching Cast Queries. Total items:", len(cacheAllCast))
    with multiprocessing.Pool(initializer=init_worker, initargs=(sq,)) as pool:
        pool.imap(cacheStoreCast,cacheAllCast)
        for i,v in enumerate(cacheAllCast):
            sys.stdout.write("Cast Cache Generation: %-3d%% \r" % (i/len(cacheAllCast)*100))
            sys.stdout.flush()
            r = sq.get()
            for k in r:
                cacheMovies["cast"][k]=r[k]
    with open(cachedIndexFile, "w") as cacheFile:
        json.dump(cacheMovies, cacheFile)
 
# let's get started
getMoviesFromS3(url)

with open(movieJsonFile, "wb") as movieFileD:
    movieFileD.write(moviesJson)
