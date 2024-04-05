## Table Generation Script User Guide

`HarvestTableGen.exe` and `HunterTableGen.exe` are Windows executable files used to generate data tables for the different Flyway Data Books.
Both of these files can ran directly in a Windows prompt console as commands. Both of these script executables are equipped with a full documented ommandline interface.

Perform the following steps to execute a script (`HarvestTableGen.exe` or `HunterTableGen.exe`):
1. Download the script and save to a local directory, such as the `Documents` folder.
2. In Windows, search by typing `cmd` in the Windows search box and open the Windows Prompt console tool.
3. In console, change directory to the directory with the downloaded script executable.
4. Execute the script by typing the name of the script along with valid arguments and options.

### HarvestTableGen.exe

For usage instructions, execute the following command in console:

`HarvestTableGen.exe --help`

Usage intructions will be printed on screen with all available options.

The path to the CSV harvest dataset must be passed in as an argument to the scripts.
`HarvestTableGen.exe WingData.csv`

Optional "options" follow the filename argument. Available options include:
1. `--help` - including this option will print the script usage instructions.
2. `--flyway` - Name of the flyway. Options are `Atlantic Flyway, Mississipi Flyway, Central Flyway, Pacific Flyway`. E.g `--flyway="Pacific Flyway"`. Default is `Atlatnic Flyway`.
3. `--season` - Season range to generate. Use the notation <START>:<END>. E.g. `--seaons="1999:2021"`. Default is ALL.
4. `--species_name` - A comma seperated list of species or grouping of species to generate tables. Multiple species can be combined together into a named group using the notation <GROUP_NAME>:(<SPECIES#1>, <SPECIES#2>, <SPECIES#3>). E.g. `--species_name="Duck:(Mallard|American Black Duck|Wigeon)"`. Values are case sensitive. Default is ALL.
5. `--species_aou` - A comma seperated list of species AOU or grouping of AOU to generate tables. Multiple species can be combined together into a named group using the notation <GROUP_NAME>:(<AOU#1>, <AOU#2>, <AOU#3>). E.g. `--species_aou="Duck:(ABDU|AGWT|AMWI|COGO|BAGO),BBWD,STEI"`. Values are case sensitive. Default is ALL. If both Species and Species AOU options are used, Species AOU will take precedent. Default is ALL.

#### Example Usage

Generate harvest data tables for Pacific Flyway with seasons from 1999 to 2022 for each species name Mallard, Widgeon:

`HarvestTableGen.exe WingData.csv --flyway="Pacific Flyway" --seasons="1999:2022" --species_name="Mallard,Wigeon'`

Generate harvest data tables for Atlantic Flyway for all seasons in the dataset for each species name Mallard, Widgeon:

`HarvestTableGen.exe WingData.csv --flyway="Atlantic Flyway" --species_name="Mallard,Wigeon'`

Generate harvest data tables for Atlantic Flyway for all seasons in the dataset for a "Duck" group and other species, using species AOU:

`HarvestTableGen.exe WingData.csv --flyway="Atlantic Flyway" --species_aou="Duck:(ABDU|AGWT|AMWI|COGO|BAGO),BBWD,STEI"`







