# Sensor correlation

Takes readings from two sensors (one CSV, one JSON) and works out which ones are probably the same object. Output is a JSON file mapping sensor 1 ids to sensor 2 ids, same shape as `Samples/SampleOutput.json`.

## How to run

```
python correlate.py <sensor1.csv> <sensor2.json> [out.json]
```

If you leave out the third argument it writes `out.json` in the current folder. Python 3, no third party packages. Tests need pytest.

## Assumptions

- **Distance threshold is 200 m.** The spec says each sensor is accurate to 100 m, so the reported location can be up to 100 m from the real one. If both sensors detect the same object and err in opposite directions, their readings can be up to 200 m apart. So two readings within 200 m are treated as a possible match. It's a parameter of `correlate()` and a constant at the top of the file, so it's easy to change. The downside is that at 200 m some unrelated readings could get paired, which is why the closest pairs get matched first.
- **Invalid readings are dropped.** Latitude has to be between -90 and 90 and longitude between -180 and 180, both ends allowed. Anything outside that isn't a real coordinate, so it never gets matched.
- **Distance is haversine** with an Earth radius of 6,371,000 m. It's a sphere, not the real WGS 84 ellipsoid, so it's off by a fraction of a percent. That's nothing next to a 100 m sensor error.
- **One reading, one match.** A reading from either sensor is used at most once. If several pairs are in range, the closest pairs win. I collect every pair within the threshold, sort by distance, and go through them closest first, skipping any pair where either id is already taken. It's greedy, so it isn't guaranteed to give the best overall pairing, but it's simple and does the right thing in the obvious cases.
- Ids are treated as ints. The JSON output keys come out as strings because JSON keys have to be strings.

## Complexity and scaling

Right now it compares every reading in sensor 1 against every reading in sensor 2, so it's O(n * m) distance calculations, plus O(k log k) to sort the k pairs that landed within the threshold. That's fine for the sample data and a few thousand readings. It would get slow on millions.

To scale it, I'd bucket readings into a grid (cells about the size of the threshold) and only compare a reading against the readings in its own cell and the neighbouring ones. That drops it to roughly linear for evenly spread data. A k-d tree would also work. I haven't done this yet, and the results would have to match the current version exactly, which is easy to check with a test.

## Tests

```
pytest
```

They cover the distance function, the coordinate validity limits (including exactly 90 and 180), the threshold edge (just inside and just outside), the one-to-one rule, closest pair winning, empty input, and a run on the sample data that checks against `SampleOutput.json`.
