# 🏷️ E-Commerce Data Warehouse

> A production-grade SQL data warehouse built on the Medallion Architecture pattern — transforming messy retail CSV into clean, analytics-ready tables inside PostgreSQL, orchestrated with Python and containerized infrastructure.

---

## 🚨 The Problem

E-commerce teams are drowning in dirty data. Raw transaction logs from online retail systems are riddled with missing customer IDs, negative quantities (returns), inconsistent date formats, and corrupted string values. Running analytics directly on these files means:
    - **Marketing** can't reliably identify top customers or revenue trends.
    - **Finance** gets wrong numbers because `Quantity` contains returns mixed with sales.
    - **Analysts** waste hours debugging type errors instead of delivering insights.

## 💡 The Solution

This project builds a single source of truth by ingesting raw e-commerce data into a structured PostgreSQL warehouse using the Medallion Architecture (Bronze → Silver → Gold). Each layer progressively cleans, conforms, and models the data so downstream teams can query with confidence.

Key business questions this warehouse answers:

    - Who are our top 10 customers by lifetime revenue?
    - What are the monthly sales trends broken down by country?
    - Which products drive the most revenue vs. volume?
    - How is transaction volume distributed geographically?

---

## 🏗️ Architecture Overview

---

## 🛠️ Tech Stack

| Layer | Technology | Purpose |
| :--- | :--- | :--- |
| **Database** | PostgreSQL 14+ | Warehouse engine, containerized via Docker |
| **Language** | Python 3.12+ | Ingestion pipelines and orchestration logic |
| **Package Manager** | uv | Fast, modern Python dependency management |
| **DB Driver** | psycopg2 | High-performance PostgreSQL adapter with copy_expert() |
| **Config** | python-dotenv | Secure credential management via .env files |
| **Code Quality** | Ruff | Blazing-fast linting and formatting |
| **Infrastructure** | Docker | Isolated, reproducible database environment |
| **Orchestration** | Apache Airflow | Scheduled DAGs for recurring ETL runs |

---

## 📂 Project Structure

---

## ⚖️ Design Decisions & Trade-Offs

---

## 🚀 Getting Started

---

## 🏅 Medallion Pipeline Stages
