# Task 3 — Database Design (SQL & MongoDB)

_Report section. Paste this into the team PDF; the ERD image is `erd_diagram.png`._

## 1. Overview

Task 3 stores the same PJME hourly energy dataset used in Task 1 in **two**
databases — a relational one (MySQL) and a non-relational one (MongoDB) — and
exposes queries over both. The dataset is a single measured variable
(`consumption_mw`) recorded hourly for one region (PJM East), 2002–2018.

## 2. Relational design (MySQL)

We used a **star schema** with three tables (meeting the 3-table minimum):

| Table | Role | Purpose |
|-------|------|---------|
| `regions` | dimension | Describes the grid zone (code, name). Extensible to other PJM zones. |
| `datetime_dim` | dimension | Pre-computed calendar attributes for each timestamp (hour, day, month, year, day_of_week, is_weekend). |
| `energy_readings` | fact | One measured `consumption_mw` per timestamp+region, with FKs to both dimensions. |

**Why this design.** Time-series analysis constantly slices data by calendar
attributes (by month, by weekday, weekend vs weekday). Precomputing those into
`datetime_dim` means queries filter/group on indexed integer columns instead of
re-parsing a datetime on every row. The fact table stays narrow (just the
measurement + two foreign keys), which keeps it fast and normalized — the same
timestamp is stored once even if more regions are added later. A
`UNIQUE (datetime_id, region_id)` key prevents duplicate readings, and indexes on
`full_datetime` and `(year, month)` support the latest-record and date-range
queries.

See **`erd_diagram.png`** (source in `erd_diagram.md`) for the ERD.

## 3. Non-relational design (MongoDB)

The MongoDB collection `energy_readings` stores **one denormalized document per
hourly reading**:

```json
{
  "region": { "code": "PJME", "name": "PJM East" },
  "datetime": "2015-07-20T17:00:00Z",
  "consumption_mw": 55214.0,
  "calendar": {
    "hour": 17, "day": 20, "month": 7, "year": 2015,
    "day_of_week": 0, "is_weekend": false
  },
  "created_at": "2026-07-04T08:00:00Z"
}
```

**Why it differs from SQL.** MongoDB has no joins, so instead of splitting the
region and calendar into separate collections we **embed** them in each document.
Every reading is then self-describing and readable in a single lookup — ideal for
an API that returns one record at a time. The calendar fields are nested under a
`calendar` sub-document for clarity, and we index `datetime` and
`(calendar.year, calendar.month)` to keep the latest-record, date-range, and
monthly-aggregation queries fast. Sample documents: `sample_mongo_documents.json`.

**SQL vs MongoDB trade-off:** the relational model avoids duplication (the region
name is stored once) and enforces integrity via foreign keys; the document model
duplicates that context in every record but reads faster and evolves without
migrations. Both are appropriate — this task demonstrates each.

## 4. Queries (3+ per database)

Both databases answer the same four questions (see `sql_queries.py` /
`mongo_queries.py`; captured output in `query_results.md`):

1. **Latest reading** (required time-series endpoint).
2. **Records within a date range** (required time-series endpoint).
3. **Average consumption by month** (aggregation).
4. **Peak (maximum) consumption reading.**

## 5. How it was built

1. `schema.sql` creates the star schema in MySQL.
2. `sql_loader.py` / `mongo_loader.py` read the real `clean_energy_dataset.csv`
   (145k hourly rows) and populate MySQL and MongoDB respectively.
3. `sql_queries.py` / `mongo_queries.py` run the four queries and write their
   results into `query_results.md`.

Free hosting used: **MySQL on Railway**, **MongoDB on Atlas (M0)**; credentials
live in a local `.env` (see `.env.example`) and are never committed.
