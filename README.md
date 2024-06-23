# vsTC2: TotalConnect 2.0 API Client

`vsTC2` is a Python client for interfacing with the TotalConnect 2.0 API, allowing you to authenticate, retrieve locations, partitions, zones, and alarm status information. It also includes functionality to poll zones and notify ZoneMinder of zone triggers.

## Features

- Authenticate with TotalConnect 2.0 API
- Retrieve locations, partitions, zones, and alarm status
- Poll zones for changes and notify ZoneMinder
- Flask web server to expose zones and alarm status via API

## Installation

1. Clone the repository:
    ```sh
    git clone https://github.com/vainsoftgames/vstc2.git
    cd vstc2
    ```

2. Create and activate a virtual environment (optional but recommended):
    ```sh
    python3 -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3. Install dependencies:
    ```sh
    pip install -r requirements.txt
    ```

## Usage

### Initial Setup

1. Import and initialize the `vsTC2` class with your TotalConnect 2.0 credentials:
    ```python
    from vstc2 import vsTC2

    username = 'your_username'
    password = 'your_password'
    app_id = 'your_app_id'
    app_version = 'your_app_version'

    client = vsTC2(username, password, app_id, app_version)
    ```

2. Authenticate with the API:
    ```python
    client.authenticate()
    ```

### Retrieving Data

1. Get locations:
    ```python
    locations = client.get_locations()
    print(locations)
    ```

2. Get partitions for a location:
    ```python
    location_id = 'your_location_id'
    partitions = client.get_partitions(location_id)
    print(partitions)
    ```

3. Get zones for a location and partition:
    ```python
    zones, last_updated_timestamp_ticks = client.get_zones(location_id, partition_id=1)
    print(zones)
    ```

### Polling Zones

1. Start polling zones:
    ```python
    client.start_polling_thread(location_id, partition_id=1, interval=10)
    ```

### Running the Flask Server

1. Run the Flask server to expose zones and alarm status via API:
    ```python
    client.run_server()
    ```

2. Access the API endpoints:
    - Zones: `http://localhost:5001/zones`
    - Alarm Status: `http://localhost:5001/alarm_status`
    - Default: `http://localhost:5001/`

## Contributing

1. Fork the repository
2. Create a new branch (`git checkout -b feature-branch`)
3. Make your changes
4. Commit your changes (`git commit -am 'Add new feature'`)
5. Push to the branch (`git push origin feature-branch`)
6. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [TotalConnect 2.0 API](https://rs.alarmnet.com/TC21API/TC2.asmx/)
- [Flask](https://flask.palletsprojects.com/)
- [xmltodict](https://github.com/martinblech/xmltodict)
- [requests](https://requests.readthedocs.io/en/latest/)

