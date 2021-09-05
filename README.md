[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
![Build Status](https://github.com/alguerre/TrackEditorWeb/actions/workflows/python-app.yml/badge.svg)
![Coverage](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/alguerre/8064b57379b6b83061b9c28f6b950594/raw/coverage.json)
![Python](https://img.shields.io/badge/python-3.9-blue.svg)

[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=alguerre_TrackEditorWeb&metric=alert_status)](https://sonarcloud.io/dashboard?id=alguerre_TrackEditorWeb)
[![Maintainability Rating](https://sonarcloud.io/api/project_badges/measure?project=alguerre_TrackEditorWeb&metric=sqale_rating)](https://sonarcloud.io/dashboard?id=alguerre_TrackEditorWeb)
[![Security Rating](https://sonarcloud.io/api/project_badges/measure?project=alguerre_TrackEditorWeb&metric=security_rating)](https://sonarcloud.io/dashboard?id=alguerre_TrackEditorWeb)

# TrackEditorWeb
This is an online tool to manipulate your GPS track files, like GPX. 
You can use it to execute operations such as: combine tracks, add timestamp, cut, split, visualize, ... 
And perzonalize own track!

This is the web verion of the desktop tool [TrackEditor](https://github.com/alguerre/TrackEditor/actions). 
It is not only a migration from desktop app to web, but the format in which this tool will be maintained. 


## Repository organization
- **TrackEditorWeb**: contains django configuration
- **TrackApp**: main app of the web, defines the layout, login/register modules, combining tracks, insert timestamp...
- **editor**: track editor app
- manage.py: django script to launch the application
- requirements.txt: list of python packages dependencies 

## Getting started (for developers)
Proposed for windows users.

1. Download and install [Python 3.9](https://www.python.org/downloads/release/python-396/)
2. Download and install [Pycharm Community](https://www.jetbrains.com/es-es/pycharm/download/#section=windows)
3. [Enable WSL 2 and load Ubuntu](https://docs.microsoft.com/es-es/windows/wsl/install-win10)
4. Downoad and install [Docker Desktop](https://www.docker.com/products/docker-desktop)
5. Launch PostgreSQL database in Docker
   - Start Docker Desktop
   - Open your Ubuntu WSL 2. Run ```wsl```in your powershell.
   - Run ```which docker``` command, it should return a string like ```/usr/bin/docker/```
   - Create postgres image
   ```
   sudo docker pull postgres:13.2-alpine
   ```
   - Create postgres container
   ```
   sudo docker run \
   -p 5432:5432 \
   --name postgres132 \
   -v /home/postgres132:/var/lib/postgresql/data \
   -e POSTGRES_PASSWORD=postgres \
   -d postgres:13.2-alpine
   ```
   - Create table
   ```
   sudo docker exec -it postgres132 psql -U postgres
   postgres=# CREATE DATABASE track_db;
   postgres=# exit
   ```
   
6. Load project in Pycharm
    - Start Pycharm
    - Click _Get from VCS_
    - Use Git as _Version control_
    - Set URL https://github.com/alguerre/TrackEditorWeb
    - Click _clone_

7. Install required dependencies
    - Tools -> Sync Python Requirements ...
    - A Python interpreter may need to be specified. But you installed Python3 3.9 in step 1, so it should be displayed to be selected.

8. Run server
    - Right click on _manage.py -> Modify Run Configuration_
    - Name: runserver
    - Parameters: runserver
    - Right click on _manage.py -> runserver_
    - Django server is ready! You can visit the link 
    
## Web development course
[CS50’s Web Programming with Python and JavaScript](https://cs50.harvard.edu/web/2020/)
    
