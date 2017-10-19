# Manual Installation
install python3 and virtualenv
```
virtualenv -p python3 env
```

activate env and install requirements using
```
source env/bin/activate
pip install -r requirements.txt
```

# Examples usage

the command is
```
python loader.py [command]
```
this runs loader in foreground, load interval could be set in loader.conf

to see list of available commands run
```
python loader.py
```

example for Docker usage
```
docker-compose run loaders python loader.py 
```

in the docker container supervisor configured to run all implemented parsers and calc-summary command
logs for all are writing to /var/log/supervisor/

to see list of log files run
```
docker-compose exec loaders ls -l /var/log/supervisor/
```
to tail some log file run
```
docker-compose exec loaders tail -f -n 20 /var/log/supervisor/loader_imot.log
```
