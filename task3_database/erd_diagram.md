# ERD — Relational schema (star schema)

GitHub renders the Mermaid diagram below directly. A rendered `erd_diagram.png`
is also included for pasting into the PDF report.

```mermaid
erDiagram
    regions ||--o{ energy_readings : "has"
    datetime_dim ||--o{ energy_readings : "timestamps"

    regions {
        int region_id PK
        varchar region_code "UNIQUE (e.g. PJME)"
        varchar region_name
        varchar description
    }

    datetime_dim {
        int datetime_id PK
        datetime full_datetime "UNIQUE"
        tinyint hour
        tinyint day
        tinyint month
        smallint year
        tinyint day_of_week
        boolean is_weekend
    }

    energy_readings {
        int reading_id PK
        int datetime_id FK
        int region_id FK
        float consumption_mw
        timestamp created_at
    }
```

**Relationships**

- `regions (1) —— (many) energy_readings` — one region has many hourly readings.
- `datetime_dim (1) —— (many) energy_readings` — one timestamp has one reading
  per region (enforced by the `UNIQUE (datetime_id, region_id)` key on the fact table).
- `energy_readings` is the **fact table**; `regions` and `datetime_dim` are the
  **dimension tables**. This star layout keeps measurements small and lets us
  filter/aggregate by any calendar attribute without re-parsing timestamps.
