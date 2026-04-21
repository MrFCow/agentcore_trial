import os
from datetime import datetime
from typing import Optional


class DataConfig:
    _reference_date: Optional[datetime] = None

    @classmethod
    def get_reference_date(cls) -> datetime:
        if cls._reference_date is None:
            cls._reference_date = cls._parse_env_date() or datetime.now()
        return cls._reference_date

    @classmethod
    def set_reference_date(cls, date: datetime) -> None:
        cls._reference_date = date

    @classmethod
    def reset(cls) -> None:
        cls._reference_date = None

    @classmethod
    def _parse_env_date(cls) -> Optional[datetime]:
        env = os.getenv("AGENT_EVAL_REFERENCE_DATE")
        if env:
            return datetime.strptime(env, "%Y-%m-%d")
        return None