Planning Platform Architecture
Overview

This repository contains the architecture for a metadata-driven enterprise planning platform designed to support:

supply chain planning

demand forecasting

inventory optimization

scenario simulations

enterprise planning workflows

The platform is designed to be flexible and scalable, allowing organizations to define their own planning models using dynamic dimensions and facts.

The system architecture is inspired by modern planning platforms such as Kinaxis, o9, and Anaplan.

Core Architectural Principles

The platform is built on the following core design principles.

1. Metadata-driven architecture

The platform does not use fixed schemas for business entities.

Instead, users define:

dimensions

attributes

members

Example dimensions:

Product
Location
Customer
Supplier
Channel

Attributes can be defined dynamically.

Example:

Product.brand
Product.category
Location.region

This allows the platform to support many planning models without code changes.

2. Fact-based planning data

Planning data is stored as facts.

A fact represents a measurable value across dimensions and time.

Example fact:

Demand

Example record:

Product: SKU123
Location: Delhi
Week: W10
Demand: 120

Facts will later be stored in a high-performance analytical database.

3. Scenario-based planning

The platform supports scenario simulations.

Scenarios allow planners to test different planning assumptions.

Example scenario structure:

Enterprise Data
│
├ Demand Plan
├ Supply Plan
└ Simulation Scenario

Scenarios inherit data from their parent and only store changes.

This allows fast simulations without copying full datasets.

4. Copy-on-write data versioning

Records are immutable.

When data changes in a scenario:

A new record version is created

The scenario references the new record

The parent scenario remains unchanged

This architecture enables fast scenario creation and efficient storage.

System Architecture

The system uses a microservice architecture.

User Interface
       ↓
API Gateway
       ↓
Microservices
       ↓
Planning Engines
       ↓
Databases

Core services include:

metadata_service
fact_service
scenario_service
query_service
algorithm_service
Repository Structure
planning-platform
│
├ services
│   ├ metadata_service
│   ├ fact_service
│   ├ scenario_service
│   ├ query_service
│   └ algorithm_service
│
├ core
│   ├ scenario_engine
│   ├ cube_engine
│   └ calculation_engine
│
├ database
│   ├ postgres
│   └ clickhouse
│
├ infrastructure
│   ├ docker
│   └ kubernetes
│
├ docs
│
└ README.md
Metadata Service

The metadata_service manages the dynamic data model.

It handles:

dimensions
attributes
dimension_members

Example:

Dimension: Product
Attributes: brand, category
Members: SKU123, SKU124

This service forms the foundation of the platform.

Fact Service (Future)

The fact_service will manage planning data such as:

Demand
Inventory
Production
Orders
Revenue

Facts reference dimension members and time.

Scenario Engine (Future)

The scenario_engine enables:

scenario creation
scenario trees
copy-on-write data
cross-scenario commits

This is the core simulation capability of the platform.

Planning Engine (Future)

The planning engine executes planning algorithms.

Example calculations:

forecast()
inventory balance
supply planning
capacity check

Calculations are executed using a dependency graph.

Technology Stack

Backend:

Python
FastAPI

Metadata database:

PostgreSQL

Analytical storage:

ClickHouse

Cache:

Redis

Infrastructure:

Docker
Kubernetes
Long-Term Vision

The platform aims to become a universal planning engine capable of supporting:

supply chain planning
financial planning
sales planning
workforce planning
network optimization

All powered by a common planning data model and scenario engine.
