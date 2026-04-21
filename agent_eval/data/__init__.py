from .factory import FlightDataStoreFactory
from .builder import BuilderOptions
from .config import DataConfig
from .store import FlightDataStore, Flight, Route, Passenger, Booking, FareClass, FareRule

flight_store = FlightDataStoreFactory.create()

__all__ = [
    "FlightDataStoreFactory",
    "BuilderOptions",
    "DataConfig",
    "flight_store",
    "Flight",
    "Route",
    "Passenger",
    "Booking",
    "FareClass",
    "FareRule",
]