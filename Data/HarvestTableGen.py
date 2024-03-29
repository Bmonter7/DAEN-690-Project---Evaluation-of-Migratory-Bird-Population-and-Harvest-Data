import click
import re
import pandas as pd
import numpy as np
import FlywayTables
from openpyxl import Workbook
import pandas as pd
import sys



''' ########### FUNCTIONS: Parsing and Validating User Inputs ###########'''

def validate_column_names(df):
    '''Checks if the dataset columns are going to work with the script code. '''
    ALLOWED_COLNAMES = ['flyway_name', 'Season', 'state', 'harvest_weight', 'species_name', 'species_aou']
    print_info('Validating dataset column names. Expected column names='+str(ALLOWED_COLNAMES))
    for ac in ALLOWED_COLNAMES:
        if ac not in df.columns:
            print_error('Dataset is missing column name ['+ac+'] that is required for calculation and generation. \
                        Please provide CSV dataset with the following column names='+str(ALLOWED_COLNAMES))
            print_error('Found column names in dataset='+str(df.columns))
            return False

    return True

def extract_colname_opt(option_input):
    ''' DEPRECATED '''
    if (option_input is not None and option_input != 'all'):
        m = re.match(r"^(.+)\/\/(.*)$", option_input)
        if (m is None):
            return (option_input)
        if (m is not None and len(m.groups()) == 2):
            return (m.group(1), m.group(2))
        else:
            return ('all')
    return ('all')
              

def extract_option_groups_n_species(option_input):
    ''' Parse and extract group and species from option input for species or species_aou. '''
    groups = {}
    if (option_input is not None and option_input != 'all'):
        option_input = option_input.split(',')
        option_input = [x.strip() for x in  option_input if len(x) > 0]
        # print(option_input)
        if (len(option_input) <= 0):
            print_fatal_exit("Invalid species input entered. Please refer to --help for more information.")
            return None
        for ac in option_input:
            results = re.search(r"^(.+):\((.+)\).*$", ac)
            if (results is None):
                groups[ac] = ac
            elif (results is not None and len(results.groups()) == 2):
                splts = results.group(2).split('|')
                splts = [x.strip() for x in  splts if len(x) > 0]
                if (len(splts) > 0):
                    groups['is_'+results.group(1)] = splts
                
    if (len(groups) <= 0):
        print_fatal_exit("Invalid species input entered. Please refer to --help for more information.")
        return None
    return groups

''' ########### FUNCTIONS: Mapping species AOU codes to species names ########### '''

def create_species_aou_to_name_dictionary(df):
    lookup_table = df[['species_aou', 'species_name']].drop_duplicates()
    # Convert the lookup table to a dictionary for faster lookup
    aou_to_name_dict = pd.Series(lookup_table.species_name.values,index=lookup_table.species_aou).to_dict()
    return aou_to_name_dict

def aou_to_species_name(species_aou, mapping_dict):
    """
    Convert a list of AOU codes to species names using aou_to_name_dict .
    
    :param species_aou: List of AOU codes or a single AOU code.
    :param mapping_dict: A dictionary mapping AOU codes to species names.
    :return: List of species names or a single species name.
    """
    # Handling both single codes and lists of codes
    if isinstance(species_aou, list):
        return [mapping_dict.get(aou, 'Unknown') for aou in species_aou]
    else:
        return mapping_dict.get(species_aou, 'Unknown')


''' ########### FUNCTIONS: Calculate Harvest Data Total for Data Tables ########### '''

def add_new_col_groups(df, selected_species_groups_n_species, selected_species_colname):
    ''' Creates a new is_* column for each defined group of species.'''
    new_groups = [(x, selected_species_groups_n_species[x]) for x in selected_species_groups_n_species if not isinstance(selected_species_groups_n_species[x], str)]
    species = [x for x in selected_species_groups_n_species if isinstance(selected_species_groups_n_species[x], str)]
    group_colnames = []
    for ng in new_groups:
        df[ng[0]] = df[selected_species_colname].apply(lambda x: 1 if x in ng[1] else 0)
        group_colnames.append(ng[0])
        print_info('Group ['+ng[0]+'] has '+str(df["is_Duck"].sum())+' values.')
    return (df, group_colnames, species)
    

# Sum harvest weights by flyway for the species
def aggregate_harvest_by_flyway(df, flyway, season_start, season_end, species_or_group, selected_species_colname):
    ''' Sum harvest weights by flyway for a species or group of species. '''
    flyway_df = df[
        (df['flyway_name'] == flyway) &
        (df['Season'] >= season_start) &
        (df['Season'] <= season_end)
    ]
    if (species_or_group and species_or_group.startswith('is_')):
        flyway_df = flyway_df[flyway_df[species_or_group] == 1]
    else:
        flyway_df = flyway_df[flyway_df[selected_species_colname] == species_or_group]

    flyway_df['harvest_weight'] = np.round(flyway_df['harvest_weight'], -2)
    yearly_sum = flyway_df.groupby('Season')['harvest_weight'].sum().astype(int)

    return yearly_sum


def aggregate_harvest_by_species_by_flyway(df, flyway, season_start, season_end, species_or_group, selected_species_colname):
    ''' Sums the harvest by species or group and by flyway and by state. '''

    flyway_df = df[
        (df['flyway_name'] == flyway) &
        (df['Season'] >= season_start) &
        (df['Season'] <= season_end)
    ]
    if (species_or_group and species_or_group.startswith('is_')):
        print_info('Calculating for group '+species_or_group)
        flyway_df = flyway_df[flyway_df[species_or_group] == 1]
    else:
        flyway_df = flyway_df[flyway_df[selected_species_colname] == species_or_group]

    # Round the harvest_weight to the nearest hundred
    flyway_df['harvest_weight'] = np.round(flyway_df['harvest_weight'], -2)

    # Aggregate and pivot the data
    flyway_totals = flyway_df.groupby(['Season', 'state'])['harvest_weight'].sum().reset_index()
    flyway_pivot = flyway_totals.pivot(index='Season', columns='state', values='harvest_weight').fillna(0)
    # Ensure 'harvest_year' is a column
    flyway_pivot.reset_index(inplace=True)
    return flyway_pivot


def calc_harvest_tabledata_by_species(df, flyway, season_start, season_end, species_or_group, selected_species_colname):
    ''' Calculates the complete harvest table data by species. '''

    total_species_data = aggregate_harvest_by_species_by_flyway(df, flyway, season_start, season_end, species_or_group, selected_species_colname)

    # Flyways including Alaska
    ALL_FLYWAYS = ['Atlantic Flyway', 'Mississippi Flyway', 'Pacific Flyway', 'Central Flyway', 'Alaska']

    # Compute totals for each flyway and sum for US total
    flyway_totals = {flyway: aggregate_harvest_by_flyway(df, flyway, season_start, season_end, species_or_group, selected_species_colname) for flyway in ALL_FLYWAYS}
    us_totals = pd.concat(flyway_totals.values(), axis=1).fillna(0).sum(axis=1).astype(int)

    print_info("Calculating flyway sum data for species: "+species_or_group)
    # Merge the totals with the main total_species_data 
    total_species_data = join_np_arrays(total_species_data, flyway_totals['Atlantic Flyway'], 'AF')
    total_species_data = join_np_arrays(total_species_data, flyway_totals['Mississippi Flyway'], 'MF')
    total_species_data = join_np_arrays(total_species_data, flyway_totals['Pacific Flyway'], 'PF')
    total_species_data = join_np_arrays(total_species_data, flyway_totals['Central Flyway'], 'CF')
    total_species_data = join_np_arrays(total_species_data, flyway_totals['Alaska'], 'AK')
    total_species_data = join_np_arrays(total_species_data, us_totals, 'US')
   

    print_info("Calculating time period averages data for species: "+species_or_group)
    # Calculate time period averages
    time_period_averages = calc_time_period_averages(total_species_data, season_start, season_end)

    # Returning both the species totals and time period averages data
    return (total_species_data, time_period_averages)

def join_np_arrays(a_df, b_arr, flyway_colname):
    ''' Joins a dataframe colume with a np array. '''
    new_col = []
    for index, row in a_df.iterrows():
        season = int(row['Season'])
        if (season in b_arr):
            new_col.append(b_arr[int(row['Season'])])
        else:
            new_col.append(0)
    a_df[flyway_colname] = new_col
    return a_df

def calc_harvest_tabledata_multiple_species(df, flyway, season_start, season_end, species_or_group_list, selected_species_colname):
    ''' Interate through a list of groups or species to generate a list of harvest table data results.'''
    
    data_results_arr = []
    species_name = None
    for sp in species_or_group_list:
        if (sp and sp.startswith('is_')):
            # Removing the is_ part from the group.
            species_name = sp[3:]
        elif (sp and selected_species_colname == 'species_aou'and sp.startswith('is_') is False):
            species_name = aou_to_species_name(sp, create_species_aou_to_name_dictionary(df))
        else:
            species_name = sp
       
        print_info("Calculating harvest data for species: "+species_name)
        results = calc_harvest_tabledata_by_species(df, flyway, season_start, season_end, sp, selected_species_colname)
        data_results_arr.append((species_name, flyway, results[0], results[1]))
    return data_results_arr

''' ########### FUNCTIONS: Calculate Harvest Data Time Period Averages for Data Tables ########### '''

def find_next_year_ending_in_0_or_5(year):
    ''' Determine the next year ending in 0 or 5 for time period end.'''
    while year % 5 != 0:
        year += 1
    return year

def calc_time_period_averages(species_pivot, first_year, last_year):
    ''' Caclulate time periods and their averages for data table. '''
    # Calculate the first period's end year to end with 0 or 5
    first_period_end_year = find_next_year_ending_in_0_or_5(first_year)

    # Initialize time periods dictionary
    time_periods = {}
    if first_period_end_year > first_year:
        time_periods[f"{first_year}-{first_period_end_year}"] = (first_year, first_period_end_year)

    # generate subsequent 5-year periods
    start_year = first_period_end_year + 1
    while start_year <= last_year:
        end_year = start_year + 4
        if end_year > last_year or (end_year % 10 != 0 and end_year % 10 != 5):
            end_year = find_next_year_ending_in_0_or_5(last_year)
            if end_year > last_year:
                end_year = last_year
        period_label = f'{start_year}-{end_year}'
        time_periods[period_label] = (start_year, end_year)
        start_year = end_year + 1

    # Fill missing values with 0 and convert to int
    species_pivot.fillna(0, inplace=True)
    species_pivot = species_pivot.astype(int)

    # Sort the data by year first (numeric only)
    species_pivot['Season'] = species_pivot['Season'].astype(str)
    numeric_years = species_pivot[species_pivot['Season'].str.isnumeric()]
    numeric_years['Season'] = numeric_years['Season'].astype(int)
    numeric_years.sort_values(by='Season', inplace=True)

    # Calculate averages for each time period and create a DataFrame for them
    averages_rows = []
    for label, (start_year, end_year) in time_periods.items():
        # Select the data for the time period
        period_data = numeric_years[(numeric_years['Season'] >= start_year) & (numeric_years['Season'] <= end_year)]

        # Calculate the mean for each column
        averages = period_data.mean().round(0)  # Round to 0 decimal places
        averages['Season'] = label  # Set the label for the averages row
        averages_rows.append(averages)

    # Convert the averages list of series to a DataFrame
    averages_df = pd.DataFrame(averages_rows)
    return averages_df


''' ########### FUNCTIONS: Excel Table Generation ########### '''

def generate_excel_workbook_for_multiple_species(table_data_results_list):
    # Creating a new workbook
    wb = Workbook()

    # Removing the default 'Sheet'
    del wb['Sheet']

    for result in table_data_results_list:
        species_name = result[0]
        flyway = result[1]
        harvest_estimate_data = result[2]
        period_averages = result[3]

        asterisk_text_list = ['* Preliminary Estimate', \
                              '** For flyway estimates prior to 2015 please see the flyway-specific databook']
        

        table_title = 'Estimates of '+species_name+' Harvest in the '+flyway
        FlywayTables.create_table_to_ws(wb, harvest_estimate_data, period_averages, asterisk_text_list, table_title, species_name)
            
        workbook_name = flyway+' Tables.xlsx'
        wb.save(workbook_name)
    print_info('Completed Excel workbook file ['+workbook_name+']')


''' ########### FUNCTIONS: Printing Output ########### '''

def print_info(output_str):
    click.echo("[INFO] " + str(output_str))

def print_error(output_str):
    click.echo("[ERROR] " + str(output_str))

def print_fatal_exit(output_str):
    click.echo("[FATAL] " + str(output_str))
    click.echo("[FATAL] Exiting now...")
    sys.exit()




''' ########### MAIN FUNCTION ########### '''

@click.command()
@click.argument('filename', required=1, type=click.Path(exists=True))
@click.option('--flyway', default='Atlantic Flyway', help='Name of the flyway. Options are Atlantic Flyway, Mississipi Flyway, \
                Central Flyway, Pacific Flyway. Default is "Atlatnic Flyway".')
@click.option('--seasons', default='all', help='Season range to generate. Use the notation <START>:<END>. E.g. 1999:2021. Default is ALL.')
@click.option('--species_name', default='all', help='A comma seperated list of species or grouping of species to generate tables. \
              Multiple species can be combined together into a named group using the notation \
              <GROUP_NAME>:(<SPECIES#1>, <SPECIES#2>, <SPECIES#3>). E.g. "Duck:(Mallard|American Black Duck|Wigeon)". \
              Values are case sensitive. Default is ALL.')
@click.option('--species_aou', default='all', help='A comma seperated list of species AOU or grouping of AOU to generate tables. \
              sMultiple species can be combined together into a named group using the notation <GROUP_NAME>:(<AOU#1>, <AOU#2>, <AOU#3>). \
              E.g. "Duck:(ABDU|AGWT|AMWI|COGO|BAGO),BBWD,STEI". \
              Values are case sensitive. Default is ALL. \
              If both Species and Species AOU options are used, Species AOU will take precedent. Default is ALL.')
# @click.option('--columns', default=None, help='A comma seperated list of custom column name mappings to overwrite the default. \
#               Use the mapping notation <Column Key>:<Column Name>. Values are case sensitive. \
#               Default column keys and names are "season,flyway_name,state,species_name,species_aou,harvest_weight".')
def main(flyway, seasons, species_name, species_aou, filename):

    print_info("###### Welcome to Harvest Table Generation #######")

    # Processing and parsing options
    sdf = pd.read_csv(filename)
    print_info('Dataset '+filename+' is now stored in a Pandas Dataframe.') 
    print_info('Dataset column names='+str(sdf.columns))

    if (validate_column_names(sdf) == False):
        print_fatal_exit('Invalid column name(s) in dataset.')
        sys.exit()

    if (seasons != 'all'):
            if (re.match(r"^\d{4}:\d{4}$", seasons)):
                seasons = seasons.split(':')
                seasons = (int(seasons[0]), int(seasons[1]))
            else:
                print_fatal_exit("Invalid season parameter. Please refer to --help for more information.")
    else: 
        all_seasons = sdf['Season'].unique()
        all_seasons.sort()
        seasons = (int(all_seasons[0]), int(all_seasons[-1]))

    

    selected_species_groups_n_species = None
    selected_species_colname = None
    selected_species_list = []
    
    if (species_aou != 'all'):
        selected_species_groups_n_species = extract_option_groups_n_species(species_aou)
        selected_species_colname = 'species_aou'
        # Add new groups, if any.
        sdf, new_groups, species = add_new_col_groups(sdf, selected_species_groups_n_species, selected_species_colname)
        selected_species_list =  new_groups + species
    elif (species_name != 'all'):
        selected_species_groups_n_species = extract_option_groups_n_species(species_name)
        selected_species_colname = 'species_name'
        # Add new groups, if any.
        sdf, new_groups, species = add_new_col_groups(sdf, selected_species_groups_n_species, selected_species_colname)
        selected_species_list =  new_groups + species
    else:
        selected_species_colname = 'species_aou'
        selected_species_list = sdf[selected_species_colname].unique()
        # Remove nan values
        selected_species_list = selected_species_list[~pd.isnull(selected_species_list)]

    # Cleaning: update 'species_aou' and 'species_name' where 'aou_number' equals 1722
    sdf.loc[sdf['AOU_number'] == 1722, ['species_aou', 'species_name']] = 'MCGO', 'Minima Cackling Goose'

    

    # Printing parsed input options
    print_info('Processed input parameters:')
    print_info('--Seasons='+str(seasons))
    print_info('--Flyway='+flyway)
    print_info('--Selected Species='+str(selected_species_list))
    print_info('--Selected Species Column='+str(selected_species_colname))

    big_results = calc_harvest_tabledata_multiple_species(sdf, flyway, seasons[0], seasons[1], selected_species_list,  selected_species_colname)

    # Genernating Excel workbook tables from all results.
    generate_excel_workbook_for_multiple_species(big_results)


if __name__ == '__main__':
    ''' Program entry point '''
    main()