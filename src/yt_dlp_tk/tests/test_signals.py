from __future__ import annotations
from ..signals import signal
from dataclasses import dataclass, field
import pytest

@dataclass
class Car:
    make: str
    year: int
    timer: int
    on_destroyed: signal = field(init=False)

    def __post_init__(self):
        self.on_destroyed = signal('destroyed')

    def move(self):
        while self.timer > 0:
            timer = self.timer
            self.timer -= 1
            yield f"{self.__str__()} blow up counter: {timer}"

        self.on_destroyed.emit()

    def __str__(self) -> str:
        return f"{self.year} {self.make}"

class blower_upper:
    def on_notify(self, sig: str, obj=None, *args, **kw):
        if sig == 'destroyed':
            print(f"{obj} was destroyed")

def test_observer(capsys: pytest.CaptureFixture) -> None:
    mycar = Car("Honda", 2019, 5)
    obv = blower_upper()
    mycar.on_destroyed.connect(obv)

    assert str(mycar.on_destroyed) == 'destroyed'

    with capsys.disabled():
        for msg in mycar.move():
            print(msg)

    mycar.on_destroyed.disconnect(obv)

def test_signal_function(capsys: pytest.CaptureFixture):
    mycar = Car("Ford Explorer", 2016, 5)

    def on_destroyed(obj: object, *args, **kw):
        print(f"{obj} was destroyed")

    mycar.on_destroyed.connect(on_destroyed)

    with capsys.disabled():
        for msg in mycar.move():
            print(msg)

    mycar.on_destroyed.disconnect(on_destroyed)
