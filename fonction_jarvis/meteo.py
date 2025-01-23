import requests

def météo(city):
    api_key = 'bb158fe427638ce39503671c8179386d'
    url = f'http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric'
    
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        liste = {}
        liste["temperature"] = data['main']['temp']
        liste["description"] = data['weather'][0]['description']
        liste["humiditer"] = data['main']["humidity"]
        liste["temp_max"] = data['main']["temp_max"]
        liste["temp_min"] = data['main']["temp_min"]

        return liste
    else:
        return None
    
