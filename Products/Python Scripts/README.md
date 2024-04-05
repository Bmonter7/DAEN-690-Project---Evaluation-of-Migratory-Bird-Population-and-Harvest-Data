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
2. `--flyway` - Name of the flyway. Options are `Atlantic Flyway, Mississipi Flyway, Central Flyway, Pacific Flyway`. Default is `Atlatnic Flyway`.



