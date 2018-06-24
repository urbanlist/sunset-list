import requests
import json

with open('/home/pi/projects/sunset-list/api_key.json', 'r') as f:
    app_key = json.loads(f.read())
    
def load_weather_data():
    sk_access_key = app_key['sk_api_key']
    gis_posion = (127.1073343, 37.2763362)
    result = requests.get('https://api2.sktelecom.com/weather/current/minutely?lon={lon}&lat={lat}&appKey={key}'.format(lon=gis_posion[0],lat=gis_posion[1],key=sk_access_key))
    data = result.json()
    if data['result']['code'] != 9200:
        return None
    
    data = data['weather']['minutely'][0]
    
    # 하늘상태
    sky_status = data['sky']['code']
    # 기온
    temperature = data['temperature']['tc']
    # 강수 타입
    def get_precipitation_type_name(data):
        type_num = str(data['precipitation']['type'])
        if type_num == '0':
            return 'none'
        elif type_num == '1':
            return 'rain'
        elif type_num == '2':
            return 'snow_rain'
        elif type_num == '3':
            return 'snow'
        return None
    precipitation_type = get_precipitation_type_name(data)
    # 풍속 (m/s)
    wind_speed = data['wind']['wspd']
    
    return (sky_status, temperature, precipitation_type, wind_speed)


if __name__ == '__main__':
    # 예제 실행하기
    data = load_weather_data()
    print('하늘 상태: ' + data[0])
    print('기온: ' + data[1])
    print('강수 타입: ' + data[2])
    print('풍속: ' + data[3])