# Formative 1: Working with Time Series Data

Group assignment (team of 3–4) focused on **time-series data preprocessing**, **exploratory analysis**, **machine learning**, and **database/API integration**. This repository uses the [Hourly Energy Consumption](https://www.kaggle.com/datasets/robikscube/hourly-energy-consumption) dataset from Kaggle (PJM East hourly load).

## Assignment overview

Working with Time Series Data aims to strengthen data preprocessing and database skills, including relational (**MySQL**) and non-relational (**MongoDB**) databases.

As a group, choose a time-series dataset from Kaggle (e.g. energy demand, stock prices, traffic volume) that includes:

- A clear timestamp/date column
- A meaningful prediction target (forecasting or classification)
- Multiple measurable variables over time

**Selected dataset:** Hourly Energy Consumption (`PJME_hourly.csv`) — timestamp (`Datetime`), target (`PJME_MW`), and derived temporal features over time.

---

## Task 1: Time-series Preprocessing and Exploratory Analysis

### A. Understanding the dataset

Demonstrate a strong understanding of the dataset through exploratory data analysis, including but not limited to:

- What is the time range of the dataset?
- What is the frequency/granularity?
- Are there missing values? How were they handled, and why was that methodology selected?
- Statistical distribution of numerical columns
- etc.

### B. Analytical questions

Come up with **at least 5 analytical questions** about the dataset and perform analysis to answer them. Examples:

- Does the series have an increasing/decreasing trend?
- Do external variables correlate with the target over time?
- Are there lag effects (e.g., sales today related to the previous 7 days)?
- etc.

**Requirements:**

- Include **at least two questions** that require **lagged features** and **moving averages**
- For each analytical question: provide **at least 1 visualization** and a **detailed interpretation** of the findings

### C. Training a model

- Select a model (classical ML such as linear regression, or deep learning such as LSTM) to predict the target variable
- Perform **hyperparameter tuning**
- Produce an **experiment table** comparing **at least 2 different experiments**

### Current progress (Task 1)

| Component | Status |
|-----------|--------|
| A. Dataset understanding & EDA | In progress (`Formative_1.ipynb`) |
| B. Analytical questions (5+, incl. 2 lag/MA) | Pending |
| C. Model training & experiment table | Pending |

**Implemented so far** (`Formative_1.ipynb`):

- Data loading via `kagglehub`
- Timestamp conversion, chronological sorting, duplicate removal
- Missing value interpolation
- Temporal feature extraction (`Hour`, `Day`, `Month`, `Year`, `DayOfWeek`)
- EDA visualizations: distribution, time series, box plot, correlation heatmap, daily/monthly trends, hourly and weekly patterns
- Outlier analysis (IQR method)
- Export to `clean_energy_dataset.csv`

---

## Task 2: Design Databases (SQL and MongoDB)

Using the same time-series dataset, design and implement:

### Relational database (MySQL)

- Minimum **3 tables**
- **ERD diagram**
- **SQL schema scripts**

### MongoDB

- **Collection design**
- **Sample documents**

### Queries

For each database implementation, perform **at least three queries**. Provide the queries and their results.

| Component | Status |
|-----------|--------|
| MySQL schema (3+ tables) + ERD | Pending |
| MongoDB collection design | Pending |
| Queries (3+ per database) | Pending |

---

## Task 3: Create Endpoints for CRUD and Time-Series Queries

Create CRUD operations (**POST**, **GET**, **PUT**, **DELETE**) for both databases implemented in Task 2.

### Required query endpoints

- **Latest record**
- **Records by date range**

CRUD operations must be implemented for **both SQL and MongoDB**.

| Component | Status |
|-----------|--------|
| MySQL CRUD + time-series endpoints | Pending |
| MongoDB CRUD + time-series endpoints | Pending |

---

## Task 4: Create a Prediction/Forecast Script

Consolidate all previous tasks into a script that:

1. **Fetches** a time series record from your API
2. **Preprocesses** the data (using the same pipeline as Task 1)
3. **Loads** the trained model
4. **Makes** a prediction/forecast

| Component | Status |
|-----------|--------|
| End-to-end forecast script | Pending |

---

## Dataset

**Hourly Energy Consumption** — PJM East (`PJME`) hourly load in megawatts (MW).

| Property | Value |
|----------|-------|
| Source | [Kaggle: robikscube/hourly-energy-consumption](https://www.kaggle.com/datasets/robikscube/hourly-energy-consumption) |
| File used | `PJME_hourly.csv` |
| Records | 145,366 hourly observations |
| Date range | 2002-01-01 → 2018-08-03 |
| Frequency | Hourly |
| Target variable | `PJME_MW` (energy consumption in MW) |

## Project structure

```
Formative 1/
├── Formative_1.ipynb          # Task 1: preprocessing & EDA
├── clean_energy_dataset.csv   # Generated after running the notebook
└── README.md
```

## Requirements

- Python 3.8+
- [Jupyter Notebook](https://jupyter.org/) or [Google Colab](https://colab.research.google.com/)
- MySQL and MongoDB (Tasks 2–4)

Python packages used in the notebook:

```
pandas
numpy
matplotlib
seaborn
kagglehub
```

Install dependencies:

```bash
pip install pandas numpy matplotlib seaborn kagglehub jupyter
```

### Kaggle authentication

The notebook loads data via `kagglehub`. Configure your Kaggle API credentials before running:

1. Create an API token from [Kaggle Account → API](https://www.kaggle.com/settings/account).
2. Place `kaggle.json` in `~/.kaggle/` (Linux/macOS) or `%USERPROFILE%\.kaggle\` (Windows).

Alternatively, run the notebook in **Google Colab**, which can cache the dataset automatically.

## Usage

1. Clone or download this repository.
2. Install the dependencies above.
3. Open and run all cells in `Formative_1.ipynb`:

```bash
jupyter notebook Formative_1.ipynb
```

4. After execution, the cleaned dataset is saved as `clean_energy_dataset.csv` in the project directory.

## Output schema

| Column | Type | Description |
|--------|------|-------------|
| `Datetime` | datetime | Timestamp (hourly) |
| `PJME_MW` | float | Energy consumption (MW) |
| `Hour` | int | Hour of day (0–23) |
| `Day` | int | Day of month |
| `Month` | int | Month (1–12) |
| `Year` | int | Year |
| `DayOfWeek` | int | Day of week (0 = Monday) |

Final shape: **(145,366 rows × 7 columns)**

## Key findings (Task 1 EDA)

- Consumption shows clear **daily**, **weekly**, and **seasonal** patterns.
- Peak usage tends to occur during typical business hours; lower usage appears overnight and on weekends.
- The time series is continuous at hourly intervals after cleaning.
- Outliers are present but retained for analysis; downstream modeling can decide whether to cap or filter them.

## License

The dataset is subject to [Kaggle's terms of use](https://www.kaggle.com/datasets/robikscube/hourly-energy-consumption). Code is provided for educational purposes as part of an ML Pipeline formative assessment.
