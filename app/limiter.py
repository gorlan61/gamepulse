from slowapi import Limiter
from slowapi.util import get_remote_address

# İstemci IP adresine göre oran sınırlaması (Rate Limiting) yapar.
limiter = Limiter(key_func=get_remote_address)
