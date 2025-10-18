MCA Insights Engine

Date: October 18, 2025, 10:39 PM IST
Author: [srikar pilla]
Description: A Python-based application to consolidate, analyze, and enrich MCA company master data from data.gov.in, focusing on five RoC jurisdictions (Maharashtra, Gujarat, Delhi, Tamil Nadu, and Karnataka). This tool detects daily changes, enriches records with web data, and provides an interactive dashboard for insights.
Overview
The MCA Insights Engine is designed to process state-wise MCA data, detect changes over time, enrich records with public web information, and offer a conversational interface for querying the dataset. It supports two processing modes: multi-day snapshots (for change detection) and single snapshot (for initial data loading). The solution includes a backend processing script (process.py) and a Streamlit-based dashboard (app.py).
Features

Data Consolidation: Merges and normalizes MCA data from multiple states into a canonical master dataset.
Change Detection: Identifies new incorporations, deregistrations, status changes, and capital updates between snapshots.
Data Enrichment: Scrapes public web data (e.g., directors and sectors) from ZaubaCorp to enhance changed records.
Interactive Dashboard: Provides a web interface for exploring data, analyzing changes, searching companies, and chatting with the dataset.
Automated Summaries: Generates detailed reports with statistics and state-wise activity.

Requirements

Python: 3.9 or higher
Dependencies:

pandas (for data manipulation)
numpy (for numerical operations)
requests (for web scraping)
beautifulsoup4 (for HTML parsing)
streamlit (for the dashboard)
plotly (for visualizations)


Installation:
pip install pandas numpy requests beautifulsoup4 streamlit plotly



Directory Structure
   MCA_Insights_Engine/
│
├── data/
│   ├── raw/              # Raw MCA data files (CSV/Excel)
│   │   ├── day1/         # Day 1 snapshot (ie delhi.csv,gujarat.csv)
│   │   ├── day2/         # Day 2 snapshot
│   │   └── day3/         # Day3 snapshot 
│   ├── processed/        # Processed master datasets│ 
│   ├── enriched/         # Enriched company data
│   └── summaries/        # Summary reports
│
├── process.py            # Data processing and enrichment script
├── app.py                # Streamlit dashboard
└── README.md             # This file
Initial Setup

Clone or Create Project Directory:
mkdir MCA_Insights_Engine
cd MCA_Insights_Engine

Install Dependencies:
Run the installation command above to ensure all required packages are available.
Prepare Data:

Place raw MCA data files in data/raw/. For multi-day processing, use data/raw/day1/ and data/raw/day2/ with state-wise files (e.g., maharashtra.csv, gujarat.csv).
Filenames should contain state keywords (e.g., "maharashtra", "gujarat") for automatic state detection.
Example structure:
textdata/raw/day1/maharashtra.csv
data/raw/day1/gujarat.csv
data/raw/day2/maharashtra.csv
data/raw/day2/gujarat.csv



Run Processing Script:
python process.py

This generates processed files in data/processed/, change logs in data/changes/, enriched data in data/enriched/, and summaries in data/summaries/.


Launch Dashboard:
streamlit run app.py

Access the dashboard at http://localhost:8501.



Architecture
+-----------------------------------------------------+
|               MCA Insights Engine                    |
+-----------------------------------------------------+

+-----------------------------------------------------+
|            1. Data Input Layer                       |
|-----------------------------------------------------|
|  +------------------------+  +---------------------+ |
|  | Raw Data Files         |  | day1/ and day2/     | |
|  | (CSV/Excel)            |  | Folders             | |
|  +------------------------+  +---------------------+ |
|  +------------------------+                         |
|  | State-wise Files       |                         |
|  | (e.g., maharashtra.csv)|                         |
|  +------------------------+                         |
|  [Data: CIN, CompanyName, etc. | Up to 1.77M records] |
+-----------------------------------------------------+
         ↓ (Raw CSV)
+-----------------------------------------------------+
|            2. Data Processing Layer                 |
|-----------------------------------------------------|
|  +------------------------+  +---------------------+ |
|  | Load Module            |  | Clean Module        | |
|  | (Chunks of 200k rows)  |  | (Dask Parallel)     | |
|  +------------------------+  +---------------------+ |
|  +------------------------+  +---------------------+ |
|  | Standardize Module     |  | Merge Module        | |
|  | (Canonical Mapping)    |  | (State Concat)      | |
|  +------------------------+  +---------------------+ |
|  +------------------------+  +---------------------+ |
|  | Change Detection       |  | Enrichment Module   | |
|  | (New, Dereg, Status)   |  | (ZaubaCorp Scrape)  | |
|  +------------------------+  +---------------------+ |
|  +------------------------+                         |
|  | Summary Module         |                         |
|  | (Text Reports)         |                         |
|  +------------------------+                         |
|  +------------------------+                         |
|  | Output Files           |                         |
|  | (master_dataset.csv,   |                         |
|  |  changes.csv,          |                         |
|  |  enriched.csv,         |                         |
|  |  summary.txt)          |                         |
|  +------------------------+                         |
|  [Tech: Pandas, Dask, requests]                    |
+-----------------------------------------------------+
         ↓ (Cleaned/Changes Dataframe)
+-----------------------------------------------------+
|            3. Presentation Layer                    |
|-----------------------------------------------------|
|  +------------------------+  +---------------------+ |
|  | Dashboard              |  | Search              | |
|  | (Metrics, Charts)      |  | (CIN/Name Query)    | |
|  +------------------------+  +---------------------+ |
|  +------------------------+  +---------------------+ |
|  | Change Analysis        |  | AI Chat             | |
|  | (Change Viz)           |  | (Query Responses)   | |
|  +------------------------+  +---------------------+ |
|  [Tech: Streamlit, Plotly]                         |
|  [Access: http://localhost:8501]                   |
+-----------------------------------------------------+

Components

Data Processor (process.py):

Purpose: Handles data ingestion, cleaning, merging, change detection, enrichment, and summary generation.
Class: RealDataProcessor encapsulates logic for file loading, standardization, and enrichment.
Methods:

load_file: Loads CSV/Excel files with encoding flexibility.
standardize_columns: Maps and normalizes column names.
clean_data: Validates and cleans data (e.g., CIN, dates, capital).
merge_states: Combines state-wise data.
detect_changes: Identifies differences between snapshots.
enrich_company: Scrapes web data for enrichment.




Dashboard (app.py):

Purpose: Provides an interactive interface using Streamlit.
Pages:

Dashboard: Displays metrics and state-wise distribution.
Search Companies: Filters by name, state, status, and year.
Change Analysis: Visualizes changes with enriched data.
AI Chat: Offers rule-based conversational querying.


Functions: load_master_data, load_changes, process_query for data handling and query processing.



Data Flow

Input: Raw MCA data files from data/raw/.
Processing: process.py cleans, merges, detects changes, enriches, and saves outputs.
Output: Processed datasets, change logs, enriched data, and summaries in respective directories.
Interaction: app.py loads processed data and provides a web interface for analysis and querying.

Workflow
Processing Workflow (process.py)

Initialization:

Creates a RealDataProcessor instance with the data/raw/ path.
Defines column mappings and state patterns for the 5 RoC jurisdictions.


Data Loading:

Detects folder structure (multi-day or direct files).
Loads each file, assigning a state based on filename keywords (e.g., "maharashtra").


Data Cleaning and Merging:

Standardizes column names and fills missing columns with NaN.
Cleans data (e.g., removes duplicates, parses dates, converts capital to numeric).


Change Detection (Multi-Day Mode):

Compares day1 and day2 snapshots.
Logs new incorporations, deregistrations, status changes, and capital updates.


Enrichment:

Scrapes ZaubaCorp for the first 5 changed records (or 5 initial records in single mode).
Extracts directors and NIC codes, saving to enriched_companies.csv.


Summary Generation:

Creates a text report with statistics and state-wise activity.


Output:

Saves master datasets, changes, enriched data, and summaries to respective directories.



Dashboard Workflow (app.py)

Data Loading:

Caches and loads master_dataset.csv, dayX_changes.csv, and enriched_companies.csv.


User Interaction:

Users navigate pages via the sidebar.
Queries are processed with process_query for conversational responses.


Visualization and Output:

Displays metrics, charts, tables, and downloadable change logs.



Enrichment Logic
Approach
The enrichment process enhances changed company records with public web data from ZaubaCorp, a reliable source for Indian company information. It focuses on directors and industry sectors (via NIC codes) to provide actionable insights.
Implementation (enrich_company in process.py)

URL Construction:

Generates a slug from the company name (e.g., "RELIANCE-INDUSTRIES" from "Reliance Industries").
Combines with CIN to form a ZaubaCorp URL (e.g., https://www.zaubacorp.com/company/RELIANCE-INDUSTRIES/U36998MH1993PTC074288).
Uses regex to clean special characters and spaces: re.sub(r'[^A-Z0-9 ]', '', company_name.upper()) followed by re.sub(r'\s+', '-', slug).strip('-').


Web Scraping:

Sends an HTTP GET request with a User-Agent header to mimic a browser.
Handles timeouts (10 seconds) and checks for a 200 status code.
Parses HTML with BeautifulSoup.


Data Extraction:

Directors: Searches for a table following a "director" heading. Extracts DIN, name, designation, and appointment date from each row (up to 4 columns).
Sector: Looks for a paragraph containing "NIC Code" and extracts the value.
Returns a dictionary with directors (semicolon-separated list) and sector, defaulting to "Not available" if not found.


Limitation:

Processes only the first 5 records to avoid rate limiting by ZaubaCorp.
Skips failed requests (e.g., 404, timeouts) with logging.



Example Output
For CIN U36998MH1993PTC074288 (SAMPLES CORPORATE GIFTING):

DIRECTORS: "PURANDAR RAI VITTAL (DIN: 00705910, Director, Appointed: 1995-07-10); MANMOHAN RAI (DIN: 00706135, Director, Appointed: 1993-10-10)"
ENRICHED_SECTOR: "3699"

Challenges and Mitigations

Rate Limiting: Limited to 5 records; could add time.sleep(2) between requests or use proxies for scalability.
Website Structure Changes: Relies on ZaubaCorp’s current HTML layout; may break if redesigned. Mitigation: Flexible heading search and error logging.
Data Accuracy: Depends on ZaubaCorp’s data; no validation beyond parsing.

Usage Notes

Data Format: Input files should have columns like CIN, CompanyName, CompanyStatus, etc. See column_mapping in process.py for details.
Testing: Use sample data (e.g., 100 records) to verify functionality before scaling.
Enhancements: Consider integrating an LLM API (e.g., via xAI’s Grok) for true AI-powered querying in the chat interface.

Troubleshooting

No Data Processed: Ensure files are in data/raw/ and contain state keywords.
Encoding Errors: Check file encoding (try UTF-8 or Latin-1).
Web Scraping Fails: Verify internet connection or ZaubaCorp accessibility; adjust timeout if needed.
Dashboard Not Loading: Confirm Streamlit is installed and data files exist.