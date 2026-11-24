import json
import math
from pathlib import Path

import pytest

import correlate

HERE = Path(__file__).parent
METRES_PER_DEGREE_LAT = 111_195


def reading(id_, lat, lon):
    return {"id": id_, "latitude": lat, "longitude": lon}


def north_of(r, metres, id_):
    """A new reading `metres` north of r."""
    return reading(id_, r["latitude"] + metres / METRES_PER_DEGREE_LAT, r["longitude"])


def test_distance_one_degree_of_latitude():
    a = reading(1, 0.0, 0.0)
    b = reading(2, 1.0, 0.0)
    assert correlate.distance_m(a, b) == pytest.approx(METRES_PER_DEGREE_LAT, abs=200)


def test_distance_to_self_is_zero():
    a = reading(1, 51.5, -114.4)
    assert correlate.distance_m(a, a) == pytest.approx(0, abs=1e-6)


def test_distance_across_the_antimeridian_is_short():
    a = reading(1, 0.0, 179.9999)
    b = reading(2, 0.0, -179.9999)
    assert correlate.distance_m(a, b) < 50


def test_sample_data_matches_sample_output():
    s1 = correlate.load_sensor1(HERE / "Samples" / "SampleData1.csv")
    s2 = correlate.load_sensor2(HERE / "Samples" / "SampleData2.json")
    expected = {int(k): v for k, v in json.load(open(HERE / "Samples" / "SampleOutput.json")).items()}
    assert correlate.correlate(s1, s2, 100) == expected


def test_loaders_return_same_shape():
    s1 = correlate.load_sensor1(HERE / "Samples" / "SampleData1.csv")
    s2 = correlate.load_sensor2(HERE / "Samples" / "SampleData2.json")
    for r in s1 + s2:
        assert isinstance(r["id"], int)
        assert isinstance(r["latitude"], float)
        assert isinstance(r["longitude"], float)


def test_invalid_latitude_is_rejected():
    assert not correlate.is_valid(reading(1, 95.0, 10.0))
    assert not correlate.is_valid(reading(1, -90.1, 10.0))
    assert correlate.is_valid(reading(1, 90.0, 10.0))


def test_invalid_longitude_is_rejected():
    assert not correlate.is_valid(reading(1, 10.0, 200.0))
    assert not correlate.is_valid(reading(1, 10.0, -180.5))
    assert correlate.is_valid(reading(1, 10.0, 180.0))


def test_invalid_readings_never_appear_in_the_result():
    bad1 = reading(1, 95.0, 10.0)
    bad2 = reading(2, 95.0, 10.0)
    assert correlate.correlate([bad1], [bad2], 100) == {}


def test_same_id_in_both_sensors_does_not_cause_a_match():
    s1 = [reading(1, 51.0, -114.0)]
    s2 = [reading(1, 40.0, 10.0)]
    assert correlate.correlate(s1, s2, 100) == {}


def test_readings_just_inside_and_outside_the_threshold():
    a = reading(1, 51.0, -114.0)
    inside = north_of(a, 90, 10)
    outside = north_of(a, 110, 11)
    assert correlate.correlate([a], [inside], 100) == {1: 10}
    assert correlate.correlate([a], [outside], 100) == {}


def test_each_reading_is_used_at_most_once():
    a1 = reading(1, 51.0, -114.0)
    a2 = north_of(a1, 40, 2)
    b = north_of(a1, 10, 10)  # closer to a1 than to a2
    result = correlate.correlate([a1, a2], [b], 100)
    assert result == {1: 10}


def test_closest_pair_wins():
    a = reading(1, 51.0, -114.0)
    far = north_of(a, 80, 10)
    near = north_of(a, 20, 11)
    assert correlate.correlate([a], [far, near], 100) == {1: 11}


def test_empty_input():
    assert correlate.correlate([], [], 100) == {}
    assert correlate.correlate([reading(1, 0.0, 0.0)], [], 100) == {}


def test_real_data_runs_and_only_uses_valid_readings():
    s1 = correlate.load_sensor1(HERE / "SensorData1.csv")
    s2 = correlate.load_sensor2(HERE / "SensorData2.json")
    result = correlate.correlate(s1, s2, 200)
    valid1 = {r["id"] for r in s1 if correlate.is_valid(r)}
    valid2 = {r["id"] for r in s2 if correlate.is_valid(r)}
    assert set(result) <= valid1
    assert set(result.values()) <= valid2
    assert len(set(result.values())) == len(result)
