from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True, order=True)
class AdvPLDate:
    ordinal: int = 0

    def __post_init__(self):
        if self.ordinal and not date(100, 1, 1).toordinal() <= self.ordinal <= date(2999, 12, 31).toordinal():
            raise ValueError("Data fora do intervalo 01/01/0100 a 31/12/2999")

    @classmethod
    def from_date(cls, value):
        return cls(value.toordinal())

    @classmethod
    def from_iso(cls, value):
        if value is None or value == "":
            return cls()
        if isinstance(value, cls):
            return value
        return cls.from_date(date.fromisoformat(value))

    @property
    def value(self):
        return date.fromordinal(self.ordinal) if self.ordinal else None

    def __str__(self):
        return self.value.isoformat() if self.ordinal else ""

    def shift(self, days):
        ordinal = self.ordinal + days
        if ordinal < 0:
            raise ValueError("Data fora do intervalo suportado")
        if ordinal:
            date.fromordinal(ordinal)
        return AdvPLDate(ordinal)
