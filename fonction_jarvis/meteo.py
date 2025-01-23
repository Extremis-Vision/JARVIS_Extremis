import requests

def météo(city):
    api_key = 'bb158fe427638ce39503671c8179386d'
    url = f'http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric'
    
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        temperature = data['main']['temp']
        description = data['weather'][0]['description']
        return temperature, description
    else:
        return None, None
    

print(météo("Paris"))