#!/bin/sh
[[ -z $MODE ]] && export MODE="apiserver"
( sleep 120 ;\
  inotifywait -e close_write -m /app --include '.*\.json$' | \
  while read -r stuff ; \
  do \
    killall -HUP gunicorn ; \
  done \
) &

python -m venv /app && \
. /app/bin/activate 

if [[ $MODE == "gencache" ]]
then
  /app/movies-cache.py
elif [[ $MODE == "apiserver" ]]
then
  /app/bin/gunicorn -w 5 --threads 2 movies-api:movieTime --log-level debug
fi
