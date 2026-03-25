from geopy.geocoders import Nominatim

geolocator = Nominatim(user_agent="crime-vehicle-tracking")


def search_location(query: str):
    try:
        locations = geolocator.geocode(
            query + ", Kerala, India",  # bias results
            exactly_one=False,
            limit=5
        )

        results = []
        if locations:
            for loc in locations:
                results.append({
                    "name": loc.address,
                    "latitude": loc.latitude,
                    "longitude": loc.longitude
                })

        return results

    except Exception:
        return []


def get_coordinates(place_name: str):
    try:
        location = geolocator.geocode(place_name + ", Kerala, India")

        if location:
            return location.latitude, location.longitude

        return None

    except Exception:
        return None