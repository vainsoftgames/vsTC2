import requests
import xmltodict
import json
import time
from datetime import datetime
from flask import Flask, jsonify
from threading import Thread

class vsTC2:
	API_URL = "https://rs.alarmnet.com/TC21API/TC2.asmx/";
	usercodes = { 'default': '1234' };

	def __init__(self, username, password, app_id, app_version):
		self.username = username;
		self.password = password;
		self.app_id = app_id;
		self.app_version = app_version;
		self.token = None;
		
		self.zones = {};
		self.partitions = {};
		self.panel_status = {}
		self.last_updated_timestamp_ticks = 0
		
		self.app = Flask(__name__)
		self.setup_routes()

	def xml_to_json(self, xml_string):
		try:
			data_dict = xmltodict.parse(xml_string);
			json_data = json.loads(json.dumps(data_dict));
			return self.remove_at_prefix(json_data);
		except Exception as e:
			print(f"Error converting XML to JSON: {e}");
			return None;

	def remove_at_prefix(self, json_data):
		if isinstance(json_data, dict):
			return {k.lstrip('@'): self.remove_at_prefix(v) for k, v in json_data.items()}
		elif isinstance(json_data, list):
			return [self.remove_at_prefix(item) for item in json_data]
		else:
			return json_data

	def callAPI(self, request, payload=False, method='POST'):
		url = self.API_URL + request
		headers = {
			"Content-Type": "application/x-www-form-urlencoded",
			'Accept': 'application/json'
		}

		response = requests.post(url, data=payload, headers=headers);
		if response.status_code == 200:
			try:
				response_data = self.xml_to_json(response.text);
				key = list(response_data)[0]
				result_code = response_data.get(key, {}).get('ResultCode')
				
				if result_code == '0':
					return response_data;
				elif result_code == '4101':
					print("Session expired, re-authenticating...")
					self.authenticate()
					payload["SessionID"] = self.token
					return self.callAPI(request, payload, method)  # Retry the request
				else:
					print(f"Failed to {request}: {result_code} - {response_data.get(key, {}).get('ResultData')}")
			except Exception as e:
				print(f"Failed to parse response: {e}")
		else:
			print(f"Failed to {request}: {response.status_code} - {response.text}");
			
		return None;


	def authenticate(self):
		payload = {
			"Username": self.username,
			"Password": self.password,
			"ApplicationID": self.app_id,
			"ApplicationVersion": self.app_version
		}
		response_data = self.callAPI("AuthenticateUserLogin", payload);

		if response_data:
			self.token = response_data.get('AuthenticateLoginResults', {}).get('SessionID')
			print(f"Session Token: {self.token}")
			return True;
		else:
			return False;



	def get_locations(self):
		if not self.token:
			print("You must authenticate first.")
			return

		payload = {
			"SessionID": self.token,
            "ApplicationID": self.app_id,
			"ApplicationVersion": self.app_version
		}
		response_data = self.callAPI("GetSessionDetails", payload)

		if response_data:
			locations = response_data.get('SessionDetailResults', {}).get('Locations', {}).get('LocationInfoBasic', []);
			
			if isinstance(locations, dict):  # Only one location
				locations = [locations]
			
			return locations;
		else:
			return False;


	

	def get_partitions(self, location_id, partition_id=0):
		if not self.token:
			print("You must authenticate first.")
			return

		payload = {
			"SessionID": self.token,
			"LocationID": location_id,
			"PartitionID": partition_id,
			"LastSequenceNumber": 0,
			"LastUpdatedTimestampTicks": 0
		}
		response_data = self.callAPI("GetPanelMetaDataAndFullStatusEx", payload)

		if response_data:
			print(response_data);
			partitions = response_data.get('PanelMetadataAndStatusResultsEx', {}).get('PanelMetadataAndStatus', {}).get('Partitions', {}).get('PartitionInfo')
			
			if partitions:
				self.process_alarm_status(partitions);
			
			return partitions



	def process_alarm_status(self, partitions):
		if partitions:
			if isinstance(partitions, dict):  # Only one partition
				partitions = [partitions]

			self.partitions = {}  # Initialize or clear the partition status dictionary

			for partition in partitions:
				partition_id = partition.get('PartitionID', 'N/A')
				arming_state = partition.get('ArmingState', 'N/A')
				status = self.determine_partition_status(arming_state)
				self.partitions[partition_id] = status
				print(f"Partition ID: {partition_id}, Status: {status}")


	def get_alarm_status(self, location_id, partition_id=1):
		if not self.token:
			print("You must authenticate first.")
			return
			
		payload = {
			"SessionID": self.token,
			"LocationID": location_id,
			"PartitionID": partition_id,
			"LastSequenceNumber": 0,
			"LastUpdatedTimestampTicks": last_updated_timestamp_ticks
		}
		
		response_data = self.callAPI("GetPanelMetaDataAndFullStatusEx", payload)
		if response_data:
			partitions = response_data.get('PanelMetadataAndStatusResultsEx', {}).get('PanelMetadataAndStatus', {})
			self.update_panel_status(metadata_status);
			
			partitions = metadata_status.get('Partitions', {}).get('PartitionInfo')
			if partitions:
				self.process_alarm_status(partitions);
		else:
			print("Failed to retrieve partition statuses. Response data is None.")

	def update_panel_status(self, metadata_status):
		# Process panel status for battery and AC
		self.panel_status['IsInACLoss'] = metadata_status.get('IsInACLoss', 'false').lower() == 'true'
		self.panel_status['IsInLowBattery'] = metadata_status.get('IsInLowBattery', 'false').lower() == 'true'
	

	
	def get_zones(self, location_id, partition_id=1, last_updated_timestamp_ticks=0):
		if not self.token:
			print("You must authenticate first.")
			return None, last_updated_timestamp_ticks
			
		payload = {
			"SessionID": self.token,
			"LocationID": location_id,
			"PartitionID": partition_id,
			"LastSequenceNumber": 0,
			"LastUpdatedTimestampTicks": last_updated_timestamp_ticks
		}
		
		response_data = self.callAPI("GetPanelMetaDataAndFullStatusEx", payload)
		
		if response_data:
			metadata_status = response_data.get('PanelMetadataAndStatusResultsEx', {}).get('PanelMetadataAndStatus', {})
			self.update_panel_status(metadata_status);
			# print(metadata_status);
			zones = metadata_status.get('Zones', {}).get('ZoneInfo')
			

			new_last_updated_timestamp_ticks = int(metadata_status.get('LastUpdatedTimestampTicks', last_updated_timestamp_ticks));
			
			partitions = metadata_status.get('Partitions', {}).get('PartitionInfo')
			if partitions:
				self.process_alarm_status(partitions);
			
			if zones is None:
				print("No zones found for the given location and partition.")
				return [], new_last_updated_timestamp_ticks

			# Only one zone
			if isinstance(zones, dict):
				zones = [zones]
				
			triggered_zones = []
			for zone in zones:
				formatted_zone = self.format_zone(zone)
				self.zones[formatted_zone['ID']] = formatted_zone

				if last_updated_timestamp_ticks > 0 and formatted_zone['Status'] != 0:
					formatted_zone['LastTriggeredTime'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
					triggered_zones.append(formatted_zone)
					self.notify_zoneminder(formatted_zone['ID'])
					print(f"Zone ID: {formatted_zone['ID']}, Zone Description: {formatted_zone['Description']}, Zone Status: {formatted_zone['Status']}", end='\n\n\n')

			if last_updated_timestamp_ticks > 0:
				return triggered_zones, new_last_updated_timestamp_ticks
			else:
				return self.zones, new_last_updated_timestamp_ticks
		else:
			print("Failed to retrieve zones. Response data is None.")
			return [], last_updated_timestamp_ticks
		
	
	def get_events(self, location_id, device_id, filter_class, max_records, event_type_filter, show_hidden, start_datetime, end_datetime):
		if not self.token:
			print("You must authenticate first.")
			return
		
		url = self.API_URL + "GetEvents"
		headers = {
			"Content-Type": "application/x-www-form-urlencoded",
			"Accept": "application/xml"
		}
		
		# Ensure the datetime format is correct
		try:
			start_datetime = datetime.strptime(start_datetime, "%Y-%m-%dT%H:%M:%S").strftime("%Y-%m-%dT%H:%M")
			end_datetime = datetime.strptime(end_datetime, "%Y-%m-%dT%H:%M:%S").strftime("%Y-%m-%dT%H:%M")
		except ValueError as e:
			print(f"Invalid date format: {e}")
			return

		payload = {
			"SessionID": self.token,
			"LocationID": location_id,
			"DeviceID": device_id,
			"FilterClass": filter_class,
			"MaxRecords": max_records,
			"EventTypeFilter": event_type_filter,
			"ShowHidden": show_hidden,
			"StartDateTime": start_datetime,
			"EndDateTime": end_datetime,
			"DateFormat": 0,
			"TimeFormat": 0,
			"SortOrder": 0,
			"LastEventIdReceived": 0,
			"LastSequenceNumber": 0
		}

		# Print the payload for debugging
		print(f"Payload: {payload}")

		response = requests.post(url, data=payload, headers=headers)

		if response.status_code == 200:
			response_data = self.xml_to_json(response.text)
			return response_data
		else:
			print(f"Failed to retrieve events: {response.status_code} - {response.text}")
			return None
		
	

	def poll_zones(self, location_id, partition_id=0, interval=10):
		while True:
			print(f"Checking zones @ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} for location {location_id} and partition {partition_id}...")
			triggered_zones, self.last_updated_timestamp_ticks = self.get_zones(location_id, partition_id, self.last_updated_timestamp_ticks);
			if triggered_zones:
				print(f"Triggered Zones : {triggered_zones}");
			else:
				print(f"No Zones Triggered")
			time.sleep(interval);

	# Static Methods
	@staticmethod
	def notify_zoneminder(zone_id):
		url = f"https:///example.com/api/webhook_zm.php?zone={zone_id}"
		try:
			response = requests.get(url)
			if response.status_code == 200:
				print(f"Successfully notified ZoneMinder for zone {zone_id}")
			else:
				print(f"Failed to notify ZoneMinder for zone {zone_id}: {response.status_code} - {response.text}")
		except Exception as e:
			print(f"Error notifying ZoneMinder for zone {zone_id}: {e}")

	@staticmethod
	def format_zone(zone):
		return {
			'ID': int(zone.get('ZoneID', '0')),
			'Description': zone.get('ZoneDescription', ''),
			'Status': int(zone.get('ZoneStatus', '0')),
			'MaskDisabled': zone.get('MaskDisabled', 'false').lower() == 'true',
			'PartitionID': int(zone.get('PartitionID', '0')),
			'BatteryLevel': int(zone.get('BatteryLevel', '-1')),
			'SignalStrength': int(zone.get('SignalStrength', '-1')),
			'LastTriggeredTime': zone.get('LastTriggeredTime', '')
		}

	@staticmethod
	def determine_partition_status(arming_state):
		status_mapping = {
            '10202': 'Armed Stay',
            '10201': 'Armed Away',
            '10203': 'Armed Night',
            '10200': 'Disarmed'
        }
		return status_mapping.get(arming_state, 'Unknown')

	# Threading
	def start_polling_thread(self, location_id, partition_id=0, interval=10):
		poll_thread = Thread(target=self.poll_zones, args=(location_id, partition_id, interval))
		poll_thread.daemon = True
		poll_thread.start()

	# Web Server
	def setup_routes(self):
		@self.app.route('/zones', methods=['GET'])
		def get_zones_status():
			return jsonify(self.zones)

		@self.app.route('/alarm_status', methods=['GET'])
		def get_alarm_status():
			return jsonify(self.partitions)
			
		@self.app.route('/', methods=['GET'])
		def get_default():
			return jsonify({
				'partitions'	: self.partitions,
				'zones'			: self.zones,
				'panel_status'	: self.panel_status
			});

	def run_server(self, port=5001):
		self.app.run(host='0.0.0.0', port=port)
