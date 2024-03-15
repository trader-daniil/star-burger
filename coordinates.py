import requests
from django.conf import settings


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
        url=settings.GEOCODE_URL,
        params=params,
    )
    response.raise_for_status()
    geoobject = response.json()['response'][
        'GeoObjectCollection'
    ]['featureMember']
    if not geoobject:
        return None
    return geoobject[0]['GeoObject']['Point']['pos'].split()

def find_coordinates(address, coordinates):
    """
    Получаем широту и долготу адреса
    Если нет совпадений в БД, то обращаемся к Geocode Api
    :param address: адрес, который нужно найти
    :param coordinates: словарь с адресом и координатами 
    """
    try:

        return coordinates[address]
    except KeyError:
        return fetch_coordinates(
            address=address,
            yandex_token=settings.YANDEX_GEOCODE_API_KEY,
        )