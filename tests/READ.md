# Test Suite Organization

The test suite is grouped by the responsibility being verified.

## Unit tests

`unit/` tests reusable `wavesim` components in isolation:

- harmonic analysis;
- material maps and geometry operations;
- monitor configuration and sampling;
- source profiles, envelopes, and injection order.

Run only this group with:

```powershell
python -m unittest discover -s tests/unit -t . -v
```

## Scenario tests

`scenarios/` verifies the configuration, geometry, numerical constraints, and
headless propagation behavior of each official simulation scenario.

```powershell
python -m unittest discover -s tests/scenarios -t . -v
```

## Validation tests

`validation/` contains cross-cutting regression, public-API, phase-validation,
and visualization checks.

```powershell
python -m unittest discover -s tests/validation -t . -v
```

Run the complete suite from the repository root with:

```powershell
python -m unittest discover -s tests -t . -v
```
