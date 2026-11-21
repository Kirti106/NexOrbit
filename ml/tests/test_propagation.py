from datetime import datetime, timezone

import pytest
from sgp4.api import Satrec, jday


LINE1 = "1 00005U 58002B   00179.78495062  .00000023  00000-0  28098-4 0  4753"
LINE2 = "2 00005  34.2682 348.7242 1859667 331.7664  19.3264 10.82419157413667"


def test_vanguard_reference_position():
    satellite = Satrec.twoline2rv(LINE1, LINE2)
    epoch = satellite.jdsatepoch + satellite.jdsatepochF
    jd = epoch + 309.67110720001529 / 1440
    fr = jd - int(jd)
    error, position, _ = satellite.sgp4(jd - fr, fr)
    assert error == 0
    assert abs(position[0] - -3754.2514743216166) < 2e-5
    assert abs(position[1] - 7876.346817439062) < 2e-5
    assert abs(position[2] - 4719.220856478582) < 2e-5
