# validate-data — H002 freeze inputs (2026-07-06)

Generated 2026-07-06T18:40:42+00:00 by [scripts/validate_h002_inputs.py](../scripts/validate_h002_inputs.py). Provenance: [ingest_manifest.json](processed/_provenance/ingest_manifest.json); invariants: [expectations.yaml](expectations.yaml). Drift vs prior snapshot: N/A (first vintage).

## cook_county sales_panel

- **PASS** sales pandera schema: 137189 rows
- **PASS** sales PK unique (pin, sale_date, sale_price)
- **PASS** sales arms-length floor
- **PASS** sales CAs in {6,7,8}

```
       col      n  missing          dtype                 min                 max                                                    top5
 sale_date 137189        0 datetime64[us] 1999-01-01 00:00:00 2026-05-26 00:00:00                                                     NaN
sale_price 137189        0          int64               10158           313581161                                                     NaN
  latitude 137189        0        float64        41.887609864       41.9614273781                                                     NaN
 longitude 137189        0        float64      -87.6776546149      -87.6127207621                                                     NaN
     class 137189        0            str                 NaN                 NaN 299(112526), 211(6709), 295(4909), 278(2812), 206(1545)
```

## chicago_permits

- **PASS** permits pandera schema: 182489 rows
- **PASS** permits PK unique (id)
- **PASS** permits CA null-or-target: null share 0.361
- **PASS** permits date ordering (application <= issue) where both present: tolerating <1% upstream entry reversals (expectations.yaml)

```
           col      n  missing          dtype                 min                 max                         top5
    issue_date 182489        0 datetime64[us] 2006-01-03 00:00:00 2026-07-03 00:00:00                          NaN
 reported_cost 182489     6640        float64                 0.0        6666666666.0                          NaN
community_area 182489    65857            str                 NaN                 NaN 8(60545), 6(28502), 7(27585)
      latitude 182489      493        float64   41.64471651864612   42.02264512084514                          NaN
     longitude 182489      493        float64   -87.9144616549066  -87.52468242947461                          NaN
```

## cps_boundaries

- **PASS** boundary vintage file count: found 40
- **PASS** boundary structural gates (all 40)

elementary features/vintage: min 356, max 409; high_school: min 49, max 135

## isbe_report_card

- **PASS** ISBE file count: found 32
- **PASS** ISBE data files match config sha pins (20/20)
