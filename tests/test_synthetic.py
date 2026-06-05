"""Synthetic generator tests: determinism, schema, calibration shape."""

from lp_reit_lab.synthetic import generate_listings


def test_deterministic_given_seed():
    assert generate_listings(50, seed=123).equals(generate_listings(50, seed=123))


def test_schema_and_synthetic_flag():
    df = generate_listings(30, seed=1)
    assert len(df) == 30
    assert df["synthetic"].all()
    for col in ["property_id", "neighborhood", "beds", "price",
                "est_monthly_rent", "hoa_monthly", "latitude", "longitude"]:
        assert col in df.columns


def test_three_bedroom_is_dominant():
    df = generate_listings(500, seed=7)
    assert (df["beds"] == 3).mean() > 0.5


def test_economics_are_positive():
    df = generate_listings(100, seed=2)
    assert (df["price"] > 0).all()
    assert (df["est_monthly_rent"] > 0).all()
    assert (df["hoa_monthly"] >= 150).all()
