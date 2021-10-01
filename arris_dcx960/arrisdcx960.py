"""Python client for ArrixDCX960."""
import json
from logging import Logger
import logging
import paho.mqtt.client as mqtt
import re

import requests
from .models import ArrixDCX960Session, ArrixDCX960Channel, ArrixDCX960RecordingSingle, ArrixDCX960RecordingShow
from .arrisdcx960box import ArrixDCX960Box
from .exceptions import ArrixDCX960ConnectionError, ArrixDCX960AuthenticationError
from .helpers import make_id

from .const import (
    ONLINE_RUNNING,
    ONLINE_STANDBY,
    MEDIA_KEY_PLAY_PAUSE,
    MEDIA_KEY_STOP,
    MEDIA_KEY_CHANNEL_DOWN,
    MEDIA_KEY_CHANNEL_UP,
    MEDIA_KEY_POWER,
    MEDIA_KEY_ENTER,
    MEDIA_KEY_REWIND,
    MEDIA_KEY_FAST_FORWARD,
    MEDIA_KEY_RECORD,
    COUNTRY_SETTINGS,
)

DEFAULT_PORT = 443

_logger = logging.getLogger(__name__)

class ArrisDCX960:
    """Main class for handling connections with ArrixDCX960 Settop boxes."""
    logger: Logger
    session: ArrixDCX960Session
    def __init__(self, username: str, password: str, country_code: str = "nl") -> None:
        """Initialize connection with ArrixDCX960"""
        self.username = username
        self.password = password
        self.token = None
        self.session = None
        self.settop_boxes = {}
        self.channels = {}
        self._country_code = country_code
        self.channels = {}
        self.country_config = COUNTRY_SETTINGS[self._country_code]
        self.baseUrl = self.country_config["api_url"]
        self._api_url_session =  self.baseUrl + "/session"
        self._api_url_token =  self.baseUrl + "/tokens/jwt"
        self._api_url_channels =  self.baseUrl + "/channels"
        self._api_url_recordings = self.baseUrl + "/networkdvrrecordings"
        self._api_url_authorization =  self.baseUrl + "/authorization"
        self._last_message_stamp = None

    def get_session_and_token(self):
        """Get session and token from ArrixDCX960"""
        self.get_session()
        self._get_token()

    def get_session(self):
        """Get ArrixDCX960 Session information"""
        if self.country_config["use_oauth"]:
            self.get_oauth_session()
        else:
            self.get_default_session()

    def get_default_session(self):
        """Get ArrixDCX960 Session information"""
        payload = {"username": self.username, "password": self.password}
        try:
            response = requests.post(self._api_url_session, json=payload)
        except (Exception):
            raise ArrixDCX960ConnectionError("Unknown connection failure")

        if not response.ok:
            status = response.json()
            _logger.debug(status)
            if status[0]['code'] == 'invalidCredentials':
                raise ArrixDCX960AuthenticationError("Invalid credentials")
            raise ArrixDCX960ConnectionError("Connection failed: " + status)
        else:
            session = response.json()
            _logger.debug(session)
            self.session = ArrixDCX960Session(
                session["customer"]["householdId"], session["oespToken"], session["locationId"], session["username"]
            )
    
    def get_oauth_session(self):
        """Get oAuth Next Session information"""
        try:
            # get authentication details
            session = requests.Session()
            _logger.debug("STEP 1: Get authorization details from " + self._api_url_authorization)
            response = session.get(self._api_url_authorization)
            _logger.debug("STEP 1 - Response text:  " + str(response.text))
            if not response.ok:
                raise ArrixDCX960AuthenticationError("Could not get authorizationUri")
 
            auth = response.json()
            _logger.debug("STEP 1 - Response: " + str(auth))
            authorizationUri = auth["session"]["authorizationUri"]
            authState = auth["session"]["state"]
            authValidtyToken = auth["session"]["validityToken"]

            # follow authorizationUri to get AUTH cookie
            _logger.debug("STEP 2: Get AUTH cookie from: " + authorizationUri)
            response = session.get(authorizationUri)
            if not response.ok:
                raise ArrixDCX960AuthenticationError("Unable to authorize to get AUTH cookie")

            _logger.debug("STEP 2 - Response cookies:" + str(session.cookies.get_dict()))
            
            # login
            username_fieldname = self.country_config["oauth_username_fieldname"]
            pasword_fieldname = self.country_config["oauth_password_fieldname"]
            if self.country_config["oauth_quote_login"]:
                payload = '{"' + username_fieldname + '":"' + self.username + '", "' + pasword_fieldname + '":"'+ self.password + '"}'
            else:
                payload = { username_fieldname: self.username, pasword_fieldname: self.password}    
            
            if self.country_config["oauth_add_accept_header"]:
                headers = {"accept": "*/*"}
            else:
                headers = None
            auth_login_url = self.country_config["oauth_url"]

            _logger.debug("STEP 3: POST login to " + auth_login_url + " with data: " + str(payload))
            response = session.post(auth_login_url, data=payload, allow_redirects=False, headers=headers)
            if not response.ok:
                raise ArrixDCX960AuthenticationError("Response: " + str(response.status_code))
            
            _logger.debug("STEP 3 - Response headers:  " + str(response.headers))
            _logger.debug("STEP 3 - Response text:  " + str(response.text))
            
            # follow redirect url
            redirect_header_name = self.country_config["oauth_redirect_header"]
            url = response.headers[redirect_header_name]
            if len(re.findall(r"authentication_error=true", url)) > 0:
                raise ArrixDCX960AuthenticationError("Unable to login, wrong credentials")
            
            _logger.debug("STEP 4:  Follow redirect " + url)
            response = session.get(url, allow_redirects=False)
            _logger.debug("STEP 4 - Response headers: " + str(response.headers))
            if not response.ok:
                raise ArrixDCX960AuthenticationError("Unable to oauth authorize")
            
            # obtain authorizationCode
            _logger.debug("STEP 5 - Extract authorizationCode")
            url = response.headers["location"]

            codeMatches = re.findall(r"code=(.*)&", url)
            if not len(codeMatches) == 1:
                raise ArrixDCX960AuthenticationError("Unable to obtain authorizationCode")

            authorizationCode = codeMatches[0]
            _logger.debug("STEP 5 - authorizationCode: " + authorizationCode)
            
            # authorize again
            payload = {"authorizationGrant":{"authorizationCode":authorizationCode,"validityToken":authValidtyToken,"state":authState}}
            _logger.debug("STEP 6 - POST auth data with valid code to: " + self._api_url_authorization)
            _logger.debug("STEP 6 - using payload: " + str(payload))
            response = session.post(self._api_url_authorization, json=payload)
            if not response.ok:
                raise ArrixDCX960AuthenticationError("Unable to authorize with oauth code")
                
            _logger.debug("STEP 6 - Response: " + str(response.text))
            auth = response.json()
            refreshToken = auth["refreshToken"]
            username = auth["username"]

            # get OESP code
            payload = {"refreshToken":refreshToken,"username":username}
            _logger.debug("STEP 7 - POST refreshToken request to : " + self._api_url_session)
            _logger.debug("STEP 7 - With payload : " + str(payload))
            response = session.post(self._api_url_session + "?token=true", json=payload)

        except Exception as e:
            _logger.debug("Generic exception: " + str(e))
            raise ArrixDCX960ConnectionError("Unknown connection failure: " + str(e))

        if not response.ok:
            status = response.json()
            _logger.debug(status)
            code = status[0].code
            reason = status[0].reason
            raise ArrixDCX960AuthenticationError("Invalid authorization response - " + code + ": " + reason)
        
        session = response.json()
        _logger.debug(session)
        self.session = ArrixDCX960Session(
            session["customer"]["householdId"], session["oespToken"], session["locationId"], session["username"]
        )
    
    def _register_settop_boxes(self):
        """Get settopxes"""
        jsonResult = self._do_api_call(self._api_url_settop_boxes)
        for box in jsonResult:
            if box["platformType"] == "EOS" or box["platformType"] == "HORIZON":
                box_id = box["deviceId"]
                self.settop_boxes[box_id] = ArrixDCX960Box(box_id, box["settings"]["deviceFriendlyName"], self.session.householdId, self.token, self._country_code, self.mqttClient, self.mqttClientId)

    def _on_mqtt_client_connect(self, client, userdata, flags, resultCode):
        """Handling mqtt connect result"""
        if resultCode == 0:
            client.on_message = self._on_mqtt_client_message
            _logger.debug("Connected to mqtt client.")
            self.mqttClientConnected = True
            client.subscribe(self.session.householdId)
            client.subscribe(self.session.householdId + "/" + self.mqttClientId)
            client.subscribe(self.session.householdId + "/+/status")
            client.subscribe(self.session.householdId + "/+/localRecordings")
            client.subscribe(self.session.householdId + "/+/localRecordings/capacity")
            client.subscribe(self.session.householdId + "/watchlistService")
            client.subscribe(self.session.householdId + "/purchaseService")
            client.subscribe(self.session.householdId + "/personalizationService")
            client.subscribe(self.session.householdId + "/recordingStatus")
            client.subscribe(self.session.householdId + "/recordingStatus/lastUserAction")
            for box_key in self.settop_boxes.keys():
                self.settop_boxes[box_key].register()

        elif resultCode == 5:
            _logger.debug("Not authorized mqtt client. Retry to connect")
            client.username_pw_set(self.session.householdId, self.token)
            client.connect(self._mqtt_broker, DEFAULT_PORT)
            client.loop_start()
        else:
            raise Exception("Could not connect to Mqtt server")

    def _on_mqtt_client_disconnect(self, client, userdata, resultCode):
        """Set state to diconnect"""
        _logger.debug(f"Disconnected from mqtt client: {resultCode}")
        self.mqttClientConnected = False

    def _on_mqtt_client_message(self, client, userdata, message):
        """Handles messages received by mqtt client"""
        jsonPayload = json.loads(message.payload)
        _logger.debug(f'mqtt message received on topic "{message.topic}": {str(jsonPayload)}')
        if "source" in jsonPayload:
            deviceId = jsonPayload["source"]
            if "deviceType" in jsonPayload and jsonPayload["deviceType"] == "STB" and "state" in jsonPayload and jsonPayload["state"] <> "OFFLINE":
                self.settop_boxes[deviceId].update_settopbox_state(jsonPayload)
            if "status" in jsonPayload:
                self.settop_boxes[deviceId].update_settop_box(jsonPayload)

    def _do_api_call(self, url, tries = 0):
        """Executes api call and returns json object"""
        _logger.debug(f'Doing API call with url: {url}')
        if tries > 3:
            raise ArrixDCX960ConnectionError("API call failed. See previous errors.")
        headers = {
            "X-OESP-Token": self.session.oespToken,
            "X-OESP-Username": self.session.username,
        }
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            _logger.debug(f'Raw result: {response.text}')
            return response.json()
        elif response.status_code == 403:
            _logger.warning(f"Api call resultcode was 403. Refreshing token en trying again...")
            self.get_session()
            tries+=1
            return self._do_api_call(url, tries)
        else:
            raise ArrixDCX960ConnectionError("API call failed: " + str(response.status_code))

    def _get_token(self):
        """Get token from ArrixDCX960"""
        jsonResult = self._do_api_call(self._api_url_token)
        self.token = jsonResult["token"]
        _logger.debug("Fetched a token: %s", jsonResult)
        
    def connect(self, enableMqttLogging: bool = False):
        """Get token and start mqtt client for receiving data from ArrixDCX960"""
        self._mqtt_broker = self.country_config["mqtt_url"]
        self.get_session_and_token()
        self._api_url_settop_boxes =  self.country_config["personalization_url_format"].format(household_id=self.session.householdId)
        self.mqttClientId = make_id(30)
        self.mqttClient = mqtt.Client(self.mqttClientId, transport="websockets")
        if enableMqttLogging:
            self.mqttClient.enable_logger(_logger)
        self.mqttClient.username_pw_set(self.session.householdId, self.token)
        self.mqttClient.tls_set()
        self.mqttClient.on_connect = self._on_mqtt_client_connect
        self.mqttClient.on_disconnect = self._on_mqtt_client_disconnect
        self.mqttClient.connect(self._mqtt_broker, DEFAULT_PORT)
        self._register_settop_boxes()
        self.load_channels()
        self.mqttClient.loop_start()

    def _send_key_to_box(self, box_id: str, key: str):
        self.settop_boxes[box_id].send_key_to_box(key)

    def select_source(self, source, box_id):
        """Changes te channel from the settopbox"""
        channel = [src for src in self.channels.values() if src.title == source][0]
        self.settop_boxes[box_id].set_channel(channel.serviceId)

    def pause(self, box_id):
        """Pauses the given settopbox"""
        box = self.settop_boxes[box_id]
        if box.state == ONLINE_RUNNING and not box.info.paused:
            self._send_key_to_box(box_id, MEDIA_KEY_PLAY_PAUSE)

    def play(self, box_id):
        """Resumes the settopbox"""
        box = self.settop_boxes[box_id]
        if box.state == ONLINE_RUNNING and box.info.paused:
            self._send_key_to_box(box_id, MEDIA_KEY_PLAY_PAUSE)

    def stop(self, box_id):
        """Stop the settopbox"""
        box = self.settop_boxes[box_id]
        if box.state == ONLINE_RUNNING:
            self._send_key_to_box(box_id, MEDIA_KEY_STOP)

    def next_channel(self, box_id):
        """Select the next channel for given settop box."""
        box = self.settop_boxes[box_id]
        if box.state == ONLINE_RUNNING:
            self._send_key_to_box(box_id, MEDIA_KEY_CHANNEL_UP)

    def previous_channel(self, box_id):
        """Select the previous channel for given settop box."""
        box = self.settop_boxes[box_id]
        if box.state == ONLINE_RUNNING:
            self._send_key_to_box(box_id, MEDIA_KEY_CHANNEL_DOWN)

    def turn_on(self, box_id):
        """Turn the settop box on."""
        box = self.settop_boxes[box_id]
        if box.state == ONLINE_STANDBY:
            self._send_key_to_box(box_id, MEDIA_KEY_POWER)

    def turn_off(self, box_id):
        """Turn the settop box off."""
        box = self.settop_boxes[box_id]
        if box.state == ONLINE_RUNNING:
            self._send_key_to_box(box_id, MEDIA_KEY_POWER)
            box.turn_off()

    def press_enter(self, box_id):
        """Press enter on the settop box"""
        box = self.settop_boxes[box_id]
        if box.state == ONLINE_RUNNING:
            self._send_key_to_box(box_id, MEDIA_KEY_ENTER)

    def rewind(self, box_id):
        """Rewind the settop box"""
        box = self.settop_boxes[box_id]
        if box.state == ONLINE_RUNNING:
            self._send_key_to_box(box_id, MEDIA_KEY_REWIND)

    def fast_forward(self, box_id):
        """Fast forward the settop box"""
        box = self.settop_boxes[box_id]
        if box.state == ONLINE_RUNNING:
            self._send_key_to_box(box_id, MEDIA_KEY_FAST_FORWARD)

    def record(self, box_id):
        """Record on the settop box"""
        box = self.settop_boxes[box_id]
        if box.state == ONLINE_RUNNING:
            self._send_key_to_box(box_id, MEDIA_KEY_RECORD)

    def is_available(self, box_id):
        box = self.settop_boxes[box_id]
        state = box.state
        return (state == ONLINE_RUNNING or state == ONLINE_STANDBY)

    def get_channel_info(self, channel_id):
        url = f'{self._api_url_channels}/{channel_id}'
        content = self._do_api_call(url)
        return self._create_channel(content)

    def _create_channel(self, channel_data):
        station = channel_data["stationSchedules"][0]["station"]
        serviceId = station["serviceId"]
        streamImage = None
        channelImage = None
        for image in station["images"]:
            if image["assetType"] == "imageStream":
                streamImage = image["url"]
            if image["assetType"] == "station-logo-small":
                channelImage =  image["url"]
        return ArrixDCX960Channel(
                serviceId,
                channel_data["title"],
                streamImage,
                channelImage,
                channel_data["channelNumber"],
            )

    def load_channels(self):
        """Refresh channels list for now-playing data."""
        _logger.debug("loading channels...")
        url = f'{self._api_url_channels}?byLocationId={self.session.locationId}&includeInvisible=true&includeNotEntitled=true&personalised=true&sort=channelNumber'
        content = self._do_api_call(url)
        for channel_dict in content["channels"]:
            channel = self._create_channel(channel_dict)
            self.channels[channel.serviceId] = channel

        for channel in self.country_config["channels"]:

            self.channels[channel["channelId"]] = ArrixDCX960Channel(
                channel["channelId"],
                channel["channelName"],
                None,
                None,
                channel["channelNumber"]
            )

        # self.channels["NL_000074_019507"] = ZiggoChannel(
        #     "NL_000074_019507",
        #     "Videoland",
        #     None,
        #     None,
        #     "151"
        # )
        for box in self.settop_boxes.values():
            box.channels = self.channels

    def get_recordings(self):
        results = []
        json_result = self._do_api_call(self._api_url_recordings)
        recordings = json_result["recordings"]
        for recording in recordings:
            if recording["type"] == "single":
                results.append(self._get_single_recording(recording))
            elif recording["type"] == "season":
                results.append(self._get_show_recording_summary(recording, "parentMediaGroupId"))
            elif recording["type"] == "show":
                results.append(self._get_show_recording_summary(recording, "mediaGroupId"))

        return results

    def _get_single_recording(self, payload):
        _logger.debug("Single Recording Payload:")
        _logger.debug(payload)

        image = None
        if len(payload["images"]) > 0:
            image = payload["images"][0]["url"]

        recording = ArrixDCX960RecordingSingle(payload["recordingId"], payload["title"], image)
        if "seasonNumber" in payload:
            recording.set_season(payload["seasonNumber"])
        else:
            recording.set_season(None)
        if "episodeNumber" in payload:
            recording.set_episode(payload["episodeNumber"])
        else:
            recording.set_episode(None)
        return {
            "type": "recording",
            "recording": recording
        }

    def get_show_recording(self, media_group_id):
        show_url = self._api_url_recordings + f"?byMediaGroupIdForShow={media_group_id}&sort=startTime%7CASC"
        show_payload = self._do_api_call(show_url)

        recordings = show_payload["recordings"]
        example_recording = recordings[0]
        if "numberOfEpisodes" not in example_recording:
            example_recording["numberOfEpisodes"] = 0
        show_recording = ArrixDCX960RecordingShow(media_group_id, example_recording["showTitle"], example_recording["numberOfEpisodes"], example_recording["images"][0]["url"])
        for recording in recordings:
            show_recording.append_child(self._get_single_recording(recording))
        return {
            "type": "show",
            "show": show_recording
        }

    def _get_show_recording_summary(self, recording_payload, group_id):
        show_recording = ArrixDCX960RecordingShow(recording_payload[group_id], recording_payload["title"],recording_payload["numberOfEpisodes"],  recording_payload["images"][0]["url"])
        return {
            "type": "show",
            "show": show_recording
        }

    def play_recording(self, box_id, recording_id):
        self.settop_boxes[box_id].play_recording(recording_id)

    def disconnect(self):
        if not self.mqttClientConnected:
            return
        self.mqttClient.disconnect()
