from common import CITY_PARAMS, CityParams

MAX_SOLAR_DECLINATION = 23.45
EQUATORIAL_CIRCUMFERENCE = 40075.0  # km


def same_sun_altitude(city1: CityParams, city2: CityParams):
    """
    Find the solar declination at which the sun altitude at the zenith is the same in the both cities passed as parameter.

    Returns a tuple with the solar declination and the sun altitude.
    Returns None, None if the solar declination is greater than 23.45 degrees.
    """
    lat1 = city1.lat
    lat2 = city2.lat

    solar_declination = (lat1 + lat2) / 2

    if abs(solar_declination) > MAX_SOLAR_DECLINATION:
        return None, None

    return solar_declination, 90 - abs(lat1 - solar_declination)


def sun_speed_over_equator():
    """
    Calculate the speed of the sun over the equator at a given speed in km/h.
    """
    return EQUATORIAL_CIRCUMFERENCE / 24


if __name__ == "__main__":
    print(same_sun_altitude(CITY_PARAMS['london'], CITY_PARAMS['saopaulo']))
    print(same_sun_altitude(CITY_PARAMS['madrid'], CITY_PARAMS['saopaulo']))
    print(same_sun_altitude(CITY_PARAMS['madrid'], CITY_PARAMS['tokyo']))
    print(sun_speed_over_equator())
