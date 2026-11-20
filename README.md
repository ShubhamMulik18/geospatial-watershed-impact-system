# Geospatial Watershed Impact Analysis System

[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/Frontend-React%2018%20+%20Vite-61DAFB?logo=react&logoColor=black)](https://react.dev)
[![PostgreSQL](https://img.shields.io/badge/Database-PostgreSQL%20+%20PostGIS-336791?logo=postgresql&logoColor=white)](https://postgis.net)
[![Rasterio](https://img.shields.io/badge/Geospatial-Rasterio%20+%20GeoPandas-438440)](https://rasterio.readthedocs.io)
[![PyTest](https://img.shields.io/badge/Tests-Pytest%20+%20Vitest-0A9EDC?logo=pytest&logoColor=white)](https://docs.pytest.org)

An end-to-end, AI-powered Web-GIS platform designed to monitor, measure, and evaluate the environmental impact of watershed management interventions (such as check dams, contour trenches, farm ponds, and percolation tanks) using geotagged field photography and multi-temporal Sentinel-2 multispectral satellite imagery.

---

## Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [System Architecture](#system-architecture)
- [Repository Structure](#repository-structure)
- [Prerequisites](#prerequisites)
- [Step-by-Step Teammate Setup Guide](#step-by-step-teammate-setup-guide)
  - [1. Clone Repository](#1-clone-the-repository)
  - [2. Database Setup (PostgreSQL + PostGIS)](#2-database-setup-postgresql--postgis)
  - [3. Backend Setup (FastAPI)](#3-backend-setup-fastapi)
  - [4. Frontend Setup (React + Vite)](#4-frontend-setup-react--vite)
- [Running the System (Multi-Terminal Guide)](#running-the-system-multi-terminal-guide)
- [End-to-End Workflow & Verification Checklist](#end-to-end-workflow--verification-checklist)
- [Automated Test Suite](#automated-test-suite)
- [Troubleshooting & Common Issues](#troubleshooting--common-issues)
- [Team Git Workflow & Rules](#team-git-workflow--rules)

---

## Overview

Watershed interventions (e.g., check dams, continuous contour trenches, percolation tanks) play a vital role in soil moisture conservation, groundwater recharge, and vegetative regeneration in drought-prone regions. However, evaluating their long-term efficacy historically required extensive manual field surveys.

This system automates watershed impact assessment by combining:
1. **Field Evidence Capture**: Geotagged ground photos with automated EXIF and Windows OCR coordinate/date extraction.
2. **AI Structure Recognition**: Machine learning classifier predicting intervention typology and confidence score.
3. **Multi-temporal Remote Sensing**: Orthorectified Sentinel-2 Level-2A surface reflectance data processing across multiple years (e.g., 2020, 2023, 2026).
4. **Bio-Physical Indicators**: Computation of Normalized Difference Vegetation Index (NDVI) and Modified Normalized Difference Water Index (MNDWI) over a common spatial support grid.
5. **Interactive Web-GIS Dashboard**: Side-by-side synchronized map comparisons, raster color ramps, layer controls, and time-series trend analysis.
6. **Automated Engineering PDF Report**: Publication-ready scientific reporting with statistical aggregations, distribution charts, and spatial maps.

---

## Key Features

- **Automated Field Photo Metadata Extraction**:
  - Automatically parses GPS latitude, longitude, and capture timestamp from image EXIF metadata.
  - Built-in OCR fallback engine for photos with burned-in GPS Map Camera text stamps.
- **AI Intervention Classification**:
  - Predicts watershed intervention structures (e.g., Check Dam, Contour Trench, Farm Pond, Gully Plug, Percolation Tank).
- **Multi-Year Satellite Data Processing**:
  - Cloud and shadow masking using Sentinel-2 Scene Classification Layer (SCL).
  - Common bounding-box alignment and reprojection.
  - Multi-date time-series analysis (Before vs. After or multi-year trends).
- **Rich Results Dashboard**:
  - Quantitative metrics (mean NDVI, surface water area in hectares, percentage change).
  - Synchronized dual-map Leaflet viewer for side-by-side temporal raster comparison.
  - Dynamic indicator toggles (Vegetation vs. Surface Water) and raster opacity controls.
- **Enterprise-Grade Architecture**:
  - Secure session-based user authentication with bcrypt password hashing.
  - Asynchronous background worker queue for compute-heavy geospatial tasks.
  - Automated PDF report builder utilizing ReportLab and Matplotlib.

---

## System Architecture

```mermaid
flowchart TD
    User["Field Officer / Analyst"] -->|Web Browser| Frontend["Frontend (React 18 + Vite + Tailwind + Leaflet)"]
    Frontend -->|REST API / JSON| Backend["FastAPI Backend Server (Port 8000)"]

    Backend -->|Auth & Metadata| DB[("PostgreSQL 15+ with PostGIS")]
    Backend -->|Photo OCR & Metadata| PhotoService["Photo & OCR Service"]
    Backend -->|Structure Classification| AIModule["AI Inference Package (PyTorch / Bundled Model)"]

    Backend -->|Enqueue Job| Worker["Analysis Worker Daemon"]
    Worker -->|Execute Pipeline| Geospatial["Geospatial Processing Engine (Rasterio, GeoPandas, NumPy)"]
    Geospatial -->|Read Surface Reflectance| SatData[("Sentinel-2 Multispectral Tiles")]
    Geospatial -->|NDVI / MNDWI Rasters & PDF| Artifacts["Artifact Storage (/artifacts)"]

    Frontend -->|View Rasters & Download PDF| Backend
```

---

## Repository Structure

```
geospatial-watershed-impact-system/
├── ai/                                # AI classification module
│   ├── config/                        # Class mappings and training config
│   ├── inference/                     # Inference contracts, preprocessing, and predictor
│   ├── models/                        # Bundled PyTorch model weights
│   └── tests/                         # Unit tests for AI inference
├── backend/                           # FastAPI backend server
│   ├── alembic/                       # Database schema migrations
│   ├── app/
│   │   ├── api/routes/                # API routes (auth, photos, datasets, analyses)
│   │   ├── core/                      # Config, security, exceptions, constants
│   │   ├── db/                        # SQLAlchemy session and engine setup
│   │   ├── integrations/              # Adapters for AI and Geospatial engines
│   │   ├── models/                    # SQLAlchemy ORM models (User, Photo, Analysis, etc.)
│   │   ├── schemas/                   # Pydantic data schemas
│   │   ├── services/                  # Business logic (auth, photos, analysis, layers)
│   │   ├── utils/                     # OCR engine, coordinate parsers, date parsers
│   │   └── workers/                   # Analysis worker daemon
│   ├── scripts/                       # Database seeding, user creation, and audit scripts
│   └── tests/                         # Comprehensive PyTest suite (unit, API, integration)
├── frontend/                          # React + TypeScript Web application
│   ├── src/
│   │   ├── components/                # UI components (map, photo, results, layout)
│   │   ├── context/                   # AuthContext and AnalysisContext
│   │   ├── pages/                     # LoginPage, NewAnalysisPage, DashboardPage, etc.
│   │   └── services/                  # Axios/Fetch API client layer
│   └── tests/                         # Vitest test suite
├── geospatial/                        # Core scientific remote sensing package
│   ├── analysis/                      # Change detection and statistical calculation
│   ├── indices/                       # NDVI and MNDWI computation engines
│   ├── outputs/                       # Georeferenced raster generation and PNG previews
│   ├── raster_processing/             # Alignment, clipping, geometry, SCL quality masking
│   ├── reports/                       # ReportLab PDF report generator and charts
│   └── tests/                         # Unit tests for remote sensing pipeline
├── sample_data/                       # Sample test photos and Sentinel-2 satellite tiles
├── pytest.ini                         # Root PyTest configuration
└── .gitignore                         # Strict rules protecting secrets, venv, and cache
```

---

## Prerequisites

Before starting, ensure your workstation has the following installed:

1. **Python**: Version **3.11** to **3.14** (tested with Python 3.14).
2. **Node.js**: Version **18+** or **20+** with `npm` (v9+).
3. **PostgreSQL**: Version **15+** with the **PostGIS** spatial extension installed.
4. **Git**: Latest version.
5. **Operating System**: Windows 10/11, Ubuntu 22.04+, or macOS.

---

## Step-by-Step Teammate Setup Guide

### 1. Clone the Repository

Open your terminal or PowerShell and run:

```bash
git clone https://github.com/ShubhamMulik18/geospatial-watershed-impact-system.git
cd geospatial-watershed-impact-system
```

### 2. Database Setup (PostgreSQL + PostGIS)

1. Ensure the PostgreSQL service is active.
2. Open `psql` or `pgAdmin` and create the `watershed` user and database:

```sql
-- In PostgreSQL terminal (psql -U postgres):
CREATE USER watershed WITH PASSWORD 'watershed';
CREATE DATABASE watershed OWNER watershed;
GRANT ALL PRIVILEGES ON DATABASE watershed TO watershed;

-- Connect to the watershed database and enable PostGIS:
\c watershed
CREATE EXTENSION IF NOT EXISTS postgis;
```

*(Note: If you use a different database name, username, or password, update your `DATABASE_URL` in step 3).*

---

### 3. Backend Setup (FastAPI)

1. Navigate to the backend directory:
   ```powershell
   cd backend
   ```

2. Create and activate a Python virtual environment:
   - **Windows (PowerShell):**
     ```powershell
     python -m venv .venv
     .\.venv\Scripts\Activate.ps1
     ```
   - **Linux / macOS:**
     ```bash
     python3 -m venv .venv
     source .venv/bin/activate
     ```

3. Install required Python packages:
   ```bash
   pip install -r requirements.txt
   ```

4. Create the environment configuration file:
   - Copy the provided `.env.example` to `.env`:
     - **Windows (PowerShell):** `copy .env.example .env`
     - **Linux / macOS:** `cp .env.example .env`
   - Verify the contents of `backend/.env`:
     ```ini
     APP_ENV=development
     DATABASE_URL=postgresql+psycopg://watershed:watershed@localhost:5432/watershed
     CORS_ORIGINS=http://localhost:3000,http://localhost:5173
     ```

5. Run database schema migrations:
   ```bash
   alembic upgrade head
   ```

6. Seed initial satellite datasets (Sentinel-2 tiles for 2020, 2023, 2026):
   ```bash
   python scripts/seed_satellite_datasets.py
   ```

7. Create an initial administrator account:
   ```bash
   python scripts/create_user.py --username admin --password MyPassword123!
   ```

8. Return to the project root:
   ```bash
   cd ..
   ```

---

### 4. Frontend Setup (React + Vite)

1. Navigate to the frontend directory:
   ```powershell
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Configure frontend environment:
   - Copy `.env.example` to `.env`:
     - **Windows (PowerShell):** `copy .env.example .env`
     - **Linux / macOS:** `cp .env.example .env`
   - Ensure `VITE_API_BASE_URL` is set:
     ```ini
     VITE_API_BASE_URL=http://localhost:8000
     VITE_USE_MOCKS=false
     ```

4. Return to the project root:
   ```bash
   cd ..
   ```

---

## Running the System (Multi-Terminal Guide)

To run the complete system locally, open separate terminal windows:

### Terminal 1: Database
Ensure PostgreSQL is running:
- **Windows**: Verify PostgreSQL Service is Running in `services.msc` or run `net start postgresql-x64-16`.
- **Linux**: `sudo systemctl status postgresql`.

### Terminal 2: FastAPI Backend Server
```powershell
cd d:\geospatial-watershed-impact-system\backend
.\.venv\Scripts\Activate.ps1
$env:PYTHONPATH = "d:\geospatial-watershed-impact-system;d:\geospatial-watershed-impact-system\backend"
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
*API Documentation will be available at: `http://127.0.0.1:8000/docs`.*

### Terminal 3: Analysis Worker Daemon
The worker daemon monitors the database for submitted analysis jobs and executes the scientific raster pipelines:
```powershell
cd d:\geospatial-watershed-impact-system\backend
.\.venv\Scripts\Activate.ps1
$env:PYTHONPATH = "d:\geospatial-watershed-impact-system;d:\geospatial-watershed-impact-system\backend"
python -m app.workers.analysis_worker
```

### Terminal 4: Frontend Development Server
```powershell
cd d:\geospatial-watershed-impact-system\frontend
npm run dev
```
*The web interface will launch at: `http://localhost:5173`.*

---

## End-to-End Workflow & Verification Checklist

Once all services are running, verify the application:

1. **User Authentication**:
   - Navigate to `http://localhost:5173/login`.
   - Log in with username: `admin` and password: `MyPassword123!`.
   - Verify you are redirected to the Dashboard.

2. **Upload Field Photograph & Metadata Extraction**:
   - Click **New Analysis** in the sidebar.
   - Upload a test photo (e.g., `sample_data/test_photos/demo_decimal_stamp.jpg`).
   - Verify that **Latitude**, **Longitude**, and **Capture Date** are automatically populated.
   - Observe the **AI Prediction Result** card classifying the structure (e.g., *Contour Trench* or *Check Dam*).

3. **Study Area Selection**:
   - Confirm that the interactive Leaflet map zooms to the photo coordinates.
   - Verify or adjust the polygon bounding box around the intervention site.
   - Click **Confirm Study Area**.

4. **Satellite Dataset & Indicator Selection**:
   - Select comparison datasets (e.g., **2020** vs. **2026** or **2020**, **2023**, and **2026**).
   - Select indicators: **Vegetation Change (NDVI)** and **Surface Water Change (MNDWI)**.
   - Choose comparison mode: **Before / After** or **Multi-date Series**.
   - Click **Start Watershed Analysis**.

5. **Review Analysis Results**:
   - The system transitions to the **Watershed Results Dashboard**.
   - Verify:
     - **Scientific Measurements**: Mean NDVI and Water Area (ha) per observation date.
     - **Before & After Comparison**: Percentage and delta indicators.
     - **Change Visualizations**: Bar charts and multi-date trend graphs.
     - **Year-wise Satellite Impact Comparison**: Side-by-side synchronized Leaflet maps displaying actual NDVI or MNDWI false-color raster overlays.
     - **Layer Controls**: Test the layer selector (NDVI / Surface Water) and opacity slider.

6. **Generate Engineering Analysis Report**:
   - Click **Download Report**.
   - Verify the downloaded multi-page PDF report contains executive summaries, project coordinates, statistical tables, distribution charts, and high-resolution spatial maps.

---

## Automated Test Suite

Before making any pull requests or committing code, run the full test suite across all modules:

### 1. Backend Unit Tests
```powershell
cd backend
.\.venv\Scripts\Activate.ps1
$env:PYTHONPATH = "d:\geospatial-watershed-impact-system;d:\geospatial-watershed-impact-system\backend"
python -m pytest tests/unit
```
*(Expected: 160 passed)*

### 2. Geospatial Remote Sensing Pipeline Tests
```powershell
python -m pytest ../geospatial/tests
```
*(Expected: 19 passed)*

### 3. Backend API & Auth Integration Tests
```powershell
python -m pytest tests/api/test_health.py tests/api/test_photos.py tests/api/test_photo_ocr_upload.py tests/api/test_auth.py
```
*(Expected: 33 passed)*

### 4. Frontend Vitest Suite
```powershell
cd ../frontend
npm test -- --run
```
*(Expected: 54 passed across 14 test files)*

### 5. Frontend Production Build Check
```powershell
npm run build
```
*(Expected: Succeeded with zero TypeScript or packaging errors)*

---

## Troubleshooting & Common Issues

### 1. PostGIS Connection or Spatial Index Error
- **Symptom**: `function st_asgeojson(...) does not exist` or `type geometry does not exist`.
- **Solution**: Connect to PostgreSQL and enable PostGIS in the target database:
  ```sql
  \c watershed
  CREATE EXTENSION IF NOT EXISTS postgis;
  ```

### 2. PROJ_LIB / PROJ_DATA Conflict on Windows
- **Symptom**: `rasterio.errors.CRSError` or PROJ database mismatch warning.
- **Solution**: The system includes automatic PROJ directory resolution in `backend/app/main.py`. If running standalone scripts, ensure your Python environment uses rasterio's bundled proj data:
  ```powershell
  $env:PROJ_LIB = "$((Get-Command python).Source | Split-Path)\..\Lib\site-packages\rasterio\proj_data"
  ```

### 3. Port Already in Use (Port 8000 or 5173)
- **Symptom**: `[Errno 10048] error while attempting to bind on address ('127.0.0.1', 8000)`.
- **Solution**: Identify and terminate the lingering process:
  ```powershell
  # Find process ID:
  netstat -ano | findstr :8000
  # Stop process:
  Stop-Process -Id <PID> -Force
  ```

### 4. PowerShell Virtual Environment Activation Disabled
- **Symptom**: `File ... Activate.ps1 cannot be loaded because running scripts is disabled on this system.`
- **Solution**: Enable script execution for the current user:
  ```powershell
  Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
  ```

### 5. Windows OCR Dependency
- The OCR fallback uses PowerShell's native Windows Runtime OCR API (`backend/app/utils/win_ocr.ps1`). It requires Windows 10/11 with the English language pack installed. On Linux or macOS environments, standard EXIF GPS tags are extracted directly.

---

## Team Git Workflow & Rules

To maintain high code quality and prevent merge conflicts, all team members must follow these rules:

1. **Always Work on Feature Branches**:
   - Never commit directly to `main`.
   - Branch naming convention:
     - `feature/<feature-name>` (e.g., `feature/spectral-moisture-index`)
     - `fix/<bug-description>` (e.g., `fix/map-layer-opacity`)
     - `docs/<topic>` (e.g., `docs/api-guide`)

2. **Sync Before Starting**:
   ```bash
   git checkout main
   git pull origin main
   git checkout -b feature/your-feature-name
   ```

3. **Never Commit Secrets or Local Files**:
   - Never commit `.env`, `.venv/`, credentials, or temporary upload files.
   - The `.gitignore` is pre-configured to block these files. Verify with `git status` before committing.

4. **Verify Tests Before Opening a Pull Request**:
   - Run backend PyTest tests.
   - Run frontend Vitest tests and `npm run build`.
   - Ensure clean formatting with zero trailing whitespace errors.

5. **Commit Message Format**:
   - Use conventional commit messages:
     - `feat: add new environmental index calculation`
     - `fix: resolve raster alignment edge case in SCL masking`
     - `docs: update setup instructions for PostGIS`
     - `test: add unit tests for date parser`
