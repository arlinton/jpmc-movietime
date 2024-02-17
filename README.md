# JPMC Movietime API

## Architecture

![Movie Time Architecture](movietime.png "Movie Time Architecture")

## API Docs

### All Movies

 * GET 
   * `curl https://server/movies`

### Search by movie title

 * GET 
   * `curl https://server/movies/titles/<Movie Title>`
   * `curl https://server/movies/titles/Dune`
   * `curl https://server/movies/titles/The%20Terminator`

### Search by movie cast 

 * GET 
   * `curl https://server/movies/cast/<Movie Title>`
   * `curl https://server/movies/cast/Denzel%20Washington`

### Search by movie genre 

 * GET 
   * `curl https://server/movies/genre/<Movie Genre>`
   * `curl https://server/movies/genre/Action`

### Search by movie year 

 * GET 
   * `curl https://server/movies/year/<Movie Year>`
   * `curl https://server/movies/year/1900`
