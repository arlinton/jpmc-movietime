#!/usr/bin/env python
import json
import orjson
import os
from flask import Flask

#
# Looking to query by:
#  - Movie Year
#  - Movie Title
#  - Cast Member in Movie
#  - Movie Genre
#

movieLastModified = None
movies = None
moviesJson = None
cachedMovies = dict()
cachedIndexFile = "/data/movie-query-cache-index.json"
movieJsonFile = "/data/movie-copy.json"

movieTime = Flask(__name__)

def loadUp():
    print("[INFO] Loading Up!")
    global cachedMovies
    global moviesJson
    global movies
    global movieLastModified
    if os.path.isfile(cachedIndexFile):
        with open(cachedIndexFile) as cachedIndexFileD:
            cachedMovies = json.load(cachedIndexFileD)
    if "last-modified" in cachedMovies:
        movieLastModified = cachedMovies["last-modified"]
        if os.path.isfile(movieJsonFile):
            with open(movieJsonFile) as movieJsonFileD:
                movies = json.load(movieJsonFileD)
            moviesJson = orjson.dumps(movies)

def cacheCheck():
    global cachedMovies
    global moviesJson
    global movies
    global movieLastModified
    if os.path.isfile(cachedIndexFile):
        with open(cachedIndexFile) as cachedIndexFileD:
            cachedMovies = json.load(cachedIndexFileD)
    if "last-modified" in cachedMovies:
        if ( movieLastModified != cachedMovies["last-modified"] ):
            if os.path.isfile(movieJsonFile):
                with open(movieJsonFile) as movieJsonFileD:
                    movies = json.load(movieJsonFileD)
                moviesJson = orjson.dumps(movies)

def getMovieResult(index):
    result = []
    for i in index:
        result.append(movies[i])
    return result

@movieTime.errorhandler(404)
def princessInAnotherCastle(e):
    return "The Princess is in another Castle"

@movieTime.errorhandler(500)
def ouchIse(e):
    return "Ouch! Something is wrong."

@movieTime.route('/movies/year/<string:key>')
def getMovieYear(key):
    try: 
        return orjson.dumps(getMovieResult(cachedMovies["year"][str(key)]))
    except:
        return orjson.dumps([])

@movieTime.route('/movies/title/<string:key>')
def getMovieTitles(key):
    try: 
        return orjson.dumps(getMovieResult(cachedMovies["titles"][str(key)]))
    except:
        return orjson.dumps([])

@movieTime.route('/movies/cast/<string:key>')
def getMovieCast(key):
    try: 
        return orjson.dumps(getMovieResult(cachedMovies["cast"][str(key)]))
    except:
        return orjson.dumps([])

@movieTime.route('/movies/genre/<string:key>')
def getMovieGenre(key):
    try: 
        return orjson.dumps(getMovieResult(cachedMovies["genres"][str(key)]))
    except:
        return orjson.dumps([])

@movieTime.route('/movies')
def getAllMovies():
    try: 
        return moviesJson
    except:
        return orjson.dumps([])
loadUp()
