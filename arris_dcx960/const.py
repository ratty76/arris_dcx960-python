"""Python client for ArrisDCX960."""

# Box states
ONLINE_RUNNING = "ONLINE_RUNNING"
ONLINE_STANDBY = "ONLINE_STANDBY"
UNKNOWN = "UNKNOWN"

BOX_PLAY_STATE_CHANNEL = "linear"
BOX_PLAY_STATE_REPLAY = "replay"
BOX_PLAY_STATE_DVR = "nDVR"
BOX_PLAY_STATE_BUFFER = "reviewbuffer"
BOX_PLAY_STATE_APP = "app"
BOX_PLAY_STATE_VOD = "VOD"

# List with available media keys.
MEDIA_KEY_POWER = "Power"
MEDIA_KEY_ENTER = "Enter"
MEDIA_KEY_ESCAPE = "Escape"  # Not yet implemented

MEDIA_KEY_HELP = "Help"  # Not yet implemented
MEDIA_KEY_INFO = "Info"  # Not yet implemented
MEDIA_KEY_GUIDE = "Guide"  # Not yet implemented

MEDIA_KEY_CONTEXT_MENU = "ContextMenu"  # Not yet implemented
MEDIA_KEY_CHANNEL_UP = "ChannelUp"
MEDIA_KEY_CHANNEL_DOWN = "ChannelDown"

MEDIA_KEY_RECORD = "MediaRecord"
MEDIA_KEY_PLAY_PAUSE = "MediaPlayPause"
MEDIA_KEY_STOP = "MediaStop"
MEDIA_KEY_REWIND = "MediaRewind"
MEDIA_KEY_FAST_FORWARD = "MediaFastForward"

BE_AUTH_URL = "https://login.prd.telenet.be/openid/login.do"

COUNTRY_SETTINGS = {
    "nl": {
        "api_url": "https://web-api-prod-obo.horizon.tv/oesp/v4/NL/nld/web",
        "personalization_url_format": "https://prod.spark.ziggogo.tv/nld/web/personalization-service/v1/customer/{household_id}/devices",
        "mqtt_url": "obomsg.prod.nl.horizon.tv",
        "use_oauth": False,
        "channels": [
        {
            "channelId": "NL_000073_019506",
            "channelName": "Netflix",
            "channelNumber": "150"
        },
        {
            "channelId": "NL_000074_019507",
            "channelName": "Videoland",
            "channelNumber": "151"
        },
        # {
        #     "channelId": "NL_000074_019508",
        #     "channelName": "Youtube",
        #     "channelNumber": "-1"
        # }
        ]
    },
    "ch": {
        "api_url": "https://web-api-prod-obo.horizon.tv/oesp/v3/CH/eng/web",
        "personalization_url_format": "https://prod.spark.upctv.ch/deu/web/personalization-service/v1/customer/{household_id}/devices",
        "mqtt_url": "obomsg.prod.ch.horizon.tv",
        "use_oauth": False,
        "channels": []
    },
    "be-nl": {
        "api_url": "https://web-api-prod-obo.horizon.tv/oesp/v4/BE/nld/web",
        "personalization_url_format": "https://prod.spark.telenettv.be/nld/web/personalization-service/v1/customer/{household_id}/devices",
        "mqtt_url": "obomsg.prod.be.horizon.tv",
        "use_oauth": True,
        "oauth_username_fieldname": "j_username",
        "oauth_password_fieldname": "j_password",
        "oauth_add_accept_header": False,
        "oauth_url": "https://login.prd.telenet.be/openid/login.do",
        "oauth_quote_login": False,
        "oauth_redirect_header": "Location",
        "channels": [
        {
            "channelId": "netflix",
            "channelName": "Netflix",
            "channelNumber": "600"
        },
        {
            "channelId": "youtube",
            "channelName": "Youtube",
            "channelNumber": "-1"
        }
        ]
    },
    "be-nl-preprod": {
        "api_url": "https://web-api-preprod-obo.horizon.tv/oesp/v4/BE/nld/web",
        "personalization_url_format": "https://preprod.spark.telenettv.be/nld/web/personalization-service/v1/customer/{household_id}/devices",
        "mqtt_url": "obomsg.preprod.be.horizon.tv",
        "use_oauth": True,
        "oauth_username_fieldname": "j_username",
        "oauth_password_fieldname": "j_password",
        "oauth_add_accept_header": False,
        "oauth_url": "https://login.prd.telenet.be/openid/login.do",
        "oauth_quote_login": False,
        "oauth_redirect_header": "Location",
        "channels": [
        {
            "channelId": "netflix",
            "channelName": "Netflix",
            "channelNumber": "600"
        },
        {
            "channelId": "youtube",
            "channelName": "Youtube",
            "channelNumber": "-1"
        }
        ]
    },
    "be-fr": {
        "api_url": "https://web-api-prod-obo.horizon.tv/oesp/v4/BE/fr/web",
        "personalization_url_format": "https://prod.spark.telenettv.be/fr/web/personalization-service/v1/customer/{household_id}/devices",
        "mqtt_url": "obomsg.prod.be.horizon.tv",
        "use_oauth": True,
        "oauth_username_fieldname": "j_username",
        "oauth_password_fieldname": "j_password",
        "oauth_add_accept_header": False,
        "oauth_url": "https://login.prd.telenet.be/openid/login.do",
        "oauth_quote_login": False,
        "oauth_redirect_header": "Location",
        "channels": []
    },
    "at": {
        "api_url": "https://prod.oesp.magentatv.at/oesp/v4/AT/deu/web",
        "personalization_url_format": "https://prod.spark.magentatv.at/deu/web/personalization-service/v1/customer/{household_id}/devices",
        "mqtt_url": "obomsg.prod.at.horizon.tv",
        "use_oauth": False,
        "channels": []
    },
    "gb": {
        "api_url": "https://web-api-prod-obo.horizon.tv/oesp/v4/GB/eng/web/",
        "personalization_url_format": "https://prod.spark.virginmedia.com/eng/web/personalization-service/v1/customer/{household_id}/devices",
        "mqtt_url": "obomsg.prod.gb.horizon.tv",
        "use_oauth": True,
        "oauth_username_fieldname": "username",
        "oauth_password_fieldname": "credential",
        "oauth_add_accept_header": True,
        "oauth_url": "https://id.virginmedia.com/rest/v40/session/start?protocol=oidc&rememberMe=true",
        "oauth_quote_login": True,
        "oauth_redirect_header": "x-redirect-location",
        "channels": []
    },
    "ie": {
        "api_url": "https://prod.oesp.virginmediatv.ie/oesp/v4/IE/eng/web",
        "personalization_url_format": "https://prod.spark.virginmediatv.ie/eng/web/personalization-service/v1/customer/{householdId}/devices",
        "mqtt_url": "obomsg.prod.ie.horizon.tv/mqtt",
        "use_oauth": False,
        "channels": []
    },
    "pl": {
        "api_url": "https://web-api-pepper.horizon.tv/oesp/v4/PL/pol/web",
        "personalization_url_format": "https://prod.spark.upctv.pl/pol/web/personalization-service/v1/customer/{householdId}/devices",
        "mqtt_url": "obomsg.prod.pl.horizon.tv/mqtt",
        "use_oauth": False,
        "channels": []
    },
    "hu": {
        "api_url": "https://web-api-pepper.horizon.tv/oesp/v4/HU/HUN/web",
        "personalization_url_format": "https://prod.spark.upctv.hu/HUN/web/personalization-service/v1/customer/{householdId}/devices", #guessed
        "mqtt_url": "obomsg.prod.hu.horizon.tv/mqtt",
        "use_oauth": False,
        "channels": []
    },
    "de": {
        "api_url": "https://web-api-pepper.horizon.tv/oesp/v4/DE/DEU/web",
        "personalization_url_format": "https://prod.spark.upctv.de/DEU/web/personalization-service/v1/customer/{householdId}/devices", #guessed
        "mqtt_url": "obomsg.prod.de.horizon.tv/mqtt",
        "use_oauth": False,
        "channels": []
    },
    "cz": {
        "api_url": "https://web-api-pepper.horizon.tv/oesp/v4/CZ/ces/web/",
        "personalization_url_format": "https://prod.spark.upctv.cz/ces/web/personalization-service/v1/customer/{householdId}/devices", #guessed
        "mqtt_url": "obomsg.prod.cz.horizon.tv/mqtt",
        "use_oauth": False,
        "channels": []
    },
    "sk": {
        "api_url": "https://web-api-pepper.horizon.tv/oesp/v4/sk/slk/web/",
        "personalization_url_format": "https://prod.spark.upctv.sk/SLK/web/personalization-service/v1/customer/{householdId}/devices",#guessed
        "mqtt_url": "obomsg.prod.sk.horizon.tv/mqtt",
        "use_oauth": False,
        "channels": []
    },
    "ro": {
        "api_url": "https://web-api-pepper.horizon.tv/oesp/v4/ro/ron/web/",
        "personalization_url_format": "https://prod.spark.upctv.ro/ron/web/personalization-service/v1/customer/{householdId}/devices",#guessed
        "mqtt_url": "obomsg.prod.ro.horizon.tv/mqtt",
        "use_oauth": False,
        "channels": []
    }
}
