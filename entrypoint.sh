#!/bin/sh
[[ -z $MODE ]] && export MODE="apiserver"
python -m venv /app && \
. /app/bin/activate 

if [[ $MODE == "gencache" ]]
then
  /app/movies-cache.py
elif [[ $MODE == "apiserver" ]]
then
  ( sleep 120 ;\
    inotifywait -e close_write -m /app --include '.*\.json$' | \
    while read -r stuff ; \
    do \
      killall -HUP gunicorn ; \
    done \
  ) &
  /app/bin/gunicorn -w 1 --threads 1 movies-api:movieTime -b 0.0.0.0:8000 --log-level debug
fi
