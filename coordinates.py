import requests
from environs import Env


env = Env()
env.read_env()

YANDEX_GEOCODE_API_KEY = env('YANDEX_GEOCODE_API_KEY')
GEOCODE_URL = 'https://geocode-maps.yandex.ru/1.x'


def fetch_coordinates(address, yandex_token):
    """
    Примнимает адрес и возращает lat и lon
    :param address: адрес, который нужно найти
    :param yandex_token: ваш токен для доступа к Yandex Geocode
    """
    params = {
        'geocode': address,
        'apikey': yandex_token,
        'format': 'json',
    }
    response = requests.get(
        url=GEOCODE_URL,
        params=params,
    )
    response.raise_for_status()
    geoobject = response.json()['response'][
        'GeoObjectCollection'
    ]['featureMember']
    if not geoobject:
        return None
    return geoobject[0]['GeoObject']['Point']['pos'].split()
