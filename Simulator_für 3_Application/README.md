# Container Simulator
This is the home of the container simulator application.
The simulator can 
- read a given geojson-file.
- enhance the positional data with timestamp, temperature and humidity.
- be configured to change temperature and humidity according to a given simulation profile.
- send the data using HTTP to a server-application providing a RESTful-API.

## Requirements
- Check if `python` 3.10.x and higher is installed:
    ```shell
    python --version
    Python 3.12.3
    ```
- Check if `pip` is installed:
    ```shell
    pip --version
    pip 24.0
    ```
- Check that you have installed a Python-IDE like
  - [PyCharm Professional Edition](https://www.jetbrains.com/de-de/pycharm/download/other.html)
  - [Visual Studio Code](https://code.visualstudio.com/) with [Python Extension](https://code.visualstudio.com/docs/languages/python)

## Installation
To run this simulator on your local machine use the following guide:
- Clone the repo.
- Create a virtual environment.
  ```shell
  python -m venv ./venv
  ```
- Activate [virtual environment](https://docs.python.org/3/library/venv.html).
  ```shell
  source ./venv/bin/activate
  ```
- Install dependencies.
    ```
    pip install -r requirements.txt
    ```
  
## Usage
Start with the Help-Message:

```shell
python simulator.py --help
usage: simulator.py [-h] [--config CONFIG] file

positional arguments:
  file                  the geojson file to use

options:
  -h, --help            show this help message and exit
  --config CONFIG, -c CONFIG
                        configuration file, default "configuration.ini"
```

**Important**: Check the configuration file first, if the application does not run as expected.

## Tools

It is easy to record and use your own tracks. But in the end, the tracks must be converted into the [GeoJSON format](https://geojson.org/). 
This is the format that the simulator can read and parse.

### GPS Tracker Tools:
- [Geo Tracker for Android](https://geo-tracker.org/en)
- [Geo Tracker for iOS](https://geo-tracker.org/en/ios): Beta Version only!

### Converter Tools:
- [MyGeodata Converter](https://mygeodata.cloud/converter/): Free Web Application able to convert various formats.

### Viewer Tools:
- [KML, KMZ Viewer with Drive](https://kmlviewer.nsspot.net/): Free online tool to view KML, KMZ files.
- [Google My Maps](https://www.google.com/maps/d/): Create own maps with Google Maps.


