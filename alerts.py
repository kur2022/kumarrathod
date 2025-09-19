from smartapi import SmartConnect

# Replace with your actual credentials
API_KEY = "ccFD3Nzr"
CLIENT_CODE = "K98607"
PIN = "2014"
SECRET_KEY = "9bbe9b5c-c8f3-4fa2-91c7-62dfd29efa23"

def connect_smartapi():
    obj = SmartConnect(api_key=API_KEY)
    data = obj.generateSession(CLIENT_CODE, PIN, SECRET_KEY)
    access_token = data['data']['access_token']
    obj.setAccessToken(access_token)
    feed_token = obj.getfeedToken()
    return obj, feed_token
