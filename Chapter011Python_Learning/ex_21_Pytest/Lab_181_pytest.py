import pytest


def test_answer():
    assert 3 == 3


@pytest.mark.smoke
def test_answer():
    assert 3 == 3
