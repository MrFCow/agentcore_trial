from contextlib import contextmanager
from datetime import datetime
from typing import Generator, Optional

from .builder import FlightDataStoreBuilder, BuilderOptions
from .config import DataConfig
from .store import FlightDataStore


class FlightDataStoreFactory:
    @staticmethod
    def create(options: BuilderOptions = None) -> FlightDataStore:
        builder = FlightDataStoreBuilder(options)
        return builder.build()

    @staticmethod
    @contextmanager
    def isolated(reference_date: Optional[datetime] = None) -> Generator[FlightDataStore, None, None]:
        original = DataConfig._reference_date
        try:
            if reference_date:
                DataConfig.set_reference_date(reference_date)
            else:
                DataConfig.reset()
            store = FlightDataStoreFactory.create()
            yield store
        finally:
            DataConfig.reset()
            if original:
                DataConfig.set_reference_date(original)