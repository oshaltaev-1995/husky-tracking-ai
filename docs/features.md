# Features

## Dashboard

The dashboard provides a quick operational overview of the current kennel state.

Current dashboard-oriented functionality includes:

- heatmap
- operational watchlist
- planning blockers
- underused dogs
- overview metrics

The dashboard is intended to help managers quickly identify which dogs require attention and how balanced current operational use has been.

## Dog Management

The dog section stores and displays operational information for each dog.

It includes:

- dog profiles
- operational metadata
- lifecycle and availability statuses
- archive support
- team-builder exclusion flags
- role-related characteristics

This allows the application to treat dogs not just as static entities, but as operational planning objects.

## Daily Entry

The Daily Entry section supports routine daily logging.

It includes:

- save and reload entries by date
- worked / not worked state
- kilometer tracking
- program-related data
- persistent daily records

This feature is one of the key foundations of the system, because many higher-level insights depend on daily worklog quality.

## Team Builder

The Team Builder supports automated team suggestion logic for sled teams.

It includes:

- role-aware dog assignment
- layout based on lead / center / wheel structure
- workload-aware planning support
- risk / eligibility / exclusion logic
- preference for underused dogs
- compact printable team sheet

The generated team layout is designed not only for UI display, but also for operational use and field printing.

## Analytics

The analytics section provides weekly and period-based insight into workload and usage.

Current MVP analytics include:

- total km by week
- worked dogs by week
- high / moderate / underused dogs by week
- average km per worked dog
- period filtering
- week-to-week comparison

This turns daily operational logging into something managers can actually interpret and compare over time.

## Export

The system includes several export formats.

Current export support includes:

- Excel analytics workbook
- CSV raw run log export
- PDF analytics summary
- compact printable team sheet

These exports are important because real operations often still depend on printable or shareable documents.

## Domain logic already implemented

The application includes real planning logic rather than only presentation logic.

Examples include:

- workload visibility
- usage classification
- underuse detection
- planning blockers
- eligibility logic
- exclusion logic
- role-aware team-building structure

This is one of the main reasons the project is stronger than a simple administrative dashboard.

## MVP value

Taken together, these features already form a practical MVP that can:

- store operational data
- expose planning-related status
- summarize weekly and period trends
- support team generation
- generate manager- and field-facing outputs