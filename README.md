# GMU DAEN690 Capstone Project

## Project Title:	EVALUATION OF MIGRATORY BIRD POPULATION AND HARVEST DATA

**Department of the Interior, U.S. Fish and Wildlife Service, Division of Migratory Bird Management**


### PROBLEM DESCRIPTION
Annually, the Division of Migratory Bird Management (DMBM) collects population and harvest data on migratory game birds, principally ducks, geese, swans, and other webless species including doves, sandhill cranes, rails, coots, gallinules, snipe, and woodcock.  These data are collected and analyzed within DMBM programs and estimates are reported out to the public in annual reports.  Also, these data are made available to the States, the public, and other stakeholders in the form of time-series tables by Flyway, known as “Flyway Data Books” to help inform State and Federal decisions about appropriate annual hunting regulations and other management programs.  Each of the four Flyways has a separate Data Book and set of data tables.  Annually, a practitioner (generally one for each Flyway) receives the current year estimates from our monitoring programs and manually appends the estimates to Flyway-specific Excel time-series tables that go back as far as the 1950s (about 75–100 tables per Flyway) and produces an updated Data Book, generally in a PDF format (see attached example).  The annual task of appending data to time series tables and producing Data Books is time and labor-intensive and can result in data reporting errors and inconsistencies among Flyways for national data that is reported in all four Flyways.

### PROJECT GOALS
Ideally, there would be a seamless flow of data from our game bird monitoring programs that produce annual demographic estimates to a single time-series repository (database) where data can be viewed and queried digitally or online with control over special and temporal extent depending on the applicable management scenario.  This could be an especially large project considering multiple species, years, geographic reference areas (e.g., State, Flyway), types of data (e.g., harvest, population abundance), and types of estimates (e.g., point estimate, variance) from our monitoring programs.  We would like to start with a limited set of data and develop a proof in concept that can later be expanded and applied to all of our available monitoring data.  A suggested starting point is to consider only mallards.  There are two types of data, annual harvest estimates and annual abundance estimates, each from a different monitoring program.  Both of these types of data include examples of the temporal and spatial scales of interest and also the variance that may be available with point estimates for each year/area.  Another possible partition of the project is to consider: 1) flow of data from monitoring programs to a single repository where Flyway-specific Data Books may be produced as PDF documents, and 2) a digital or online database where data can be viewed and queried with control over special and temporal extent depending on the applicable management scenario.  For the later portion, consideration of a dashboard that displays the time-series data of interest (point estimates and variance where available) and some basic summary statistics (e.g., long-term average; 3-, 5-, and 10-year moving averages) would be of interest.

### DATA SETS
1.	Harvest estimates.
2.	Population abundance estimates.
3.	Example time-series file from one of the four Flyways (Excel).
4.	Previous year's Data Book from the Pacific Flyway for reference (pdf).'

### DIRECTORY STRUCTURE

```
DAEN690/                                                   # project documents
|-- Team Wild Ducks Final Presentation.pptx                # presentation
|-- Team Wild Ducks Final Project Report.docx              # report
|-- Team Wild Ducks Final Status Report.pptx               # status report
Data/
|-- FlywayTables.py                                        # Excel table module
|-- HarvestTableGen.py                                     # Harvest table generation script
|-- HunterTableGen.py                                      # Hunter table generation script
|-- + other data files...
Products/                                                  # all final delierables to customer
|-- Python Scripts/                                        # final script deliverables and executables
|-- Visualizations/                                        # all final Tableau deliverables
Working Visualizations/                                     
|-- ...
README.md
```

