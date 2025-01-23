import requests

def météo(city):
    api_key = '567e1f8cb838f5f2ed71e8ca6281e700'
    url = f'http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric'
    
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        temperature = data['main']['temp']
        description = data['weather'][0]['description']
        return temperature, description
    else:
        return None, None