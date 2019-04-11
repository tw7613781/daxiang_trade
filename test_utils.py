from utils import toNearest

def test_toNearest():
    # exact half way numbers are rounded to the nearest even result
    assert toNearest(1.45, 0.1) == 1.4
    assert toNearest(1.55, 0.1) == 1.6