import click
import re
import pandas as pd
import numpy as np
import FlywayTables
from openpyxl import Workbook
import pandas as pd
import sys


''' ########### FUNCTIONS: Printing Output ########### '''

def print_info(output_str):
    click.echo("[INFO] " + str(output_str))

def print_error(output_str):
    click.echo("[ERROR] " + str(output_str))

def print_fatal_exit(output_str):
    click.echo("[FATAL] " + str(output_str))
    click.echo("[FATAL] Exiting now...")
    sys.exit()


''' ########### FUNCTIONS: Parsing and Validating User Inputs ###########'''

def validate_column_names(df):
    '''Checks if the dataset columns are going to work with the script code. '''

    ALLOWED_COLNAMES = ['mgmt_unit', 'season', 'survey_state', 'sp_group_estimated', 'sp_group_surveyed', \
                        'bag_per_hunter', 'active_hunters', 'days_hunted']
    print_info('Validating dataset column names. Expected column names='+str(ALLOWED_COLNAMES))
    for ac in ALLOWED_COLNAMES:
        if ac not in df.columns:
            print_error('Dataset is missing column name ['+ac+'] that is required for calculation and generation. \
                        Please provide CSV dataset with the following column names='+str(ALLOWED_COLNAMES))
            print_error('Found column names in dataset='+str(df.columns))
            return False

    return True


''' ########### FUNCTIONS: Calculate Harvest Data Total for Data Tables ########### '''

def find_next_year_ending_in_0_or_5(year):
    while year % 5 != 0:
        year += 1
    return year

# Define a function to sum values by year for a specified flyway
def sum_values_by_flyway(df, flyway, season_start, season_end, species_group, aggregate_on):
    flyway_df = df[
        (df['mgmt_unit'] == flyway) &
        (df['sp_group_estimated'] == species_group) &
        (df['season'] >= season_start) &
        (df['season'] <= season_end)
    ].copy()

    # Check if table_value is 'bag_per_hunter' to determine rounding
    if aggregate_on != 'bag_per_hunter':
        # If table_value is not 'bag_per_hunter', round to nearest hundred
        flyway_df[aggregate_on] = np.round(flyway_df[aggregate_on], -2)
    else:
        # If table_value is 'bag_per_hunter', round to one decimal place
        flyway_df[aggregate_on] = np.round(flyway_df[aggregate_on], 1)

    yearly_sum = flyway_df.groupby('season')[aggregate_on].sum()

    return yearly_sum


def calc_tabledata_for_species_group(df, flyway, season_start, season_end, species_group, aggregate_on):
    # Filter for Atlantic Flyway from first_year (1999) to last_year(2020) for Ducks
    
    df_hunt = df[
        (df['mgmt_unit'] == flyway) &
        (df['sp_group_estimated'] == species_group) &
        (df['season'] >= 1999) &
        (df['season'] <= 2021)
    ].copy()

    


    # Round the active_hunters to the nearest hundred for Atlantic Flyway
    # Apply rounding only if table_value does not equal bag_per_hunter
    if aggregate_on != ' ':
        df_hunt[aggregate_on] = np.round(df_hunt[aggregate_on], -2)
    else: #hunting date
        # If table_value equals bag_per_hunter round to 1 decimal place
        df_hunt[aggregate_on] = np.round(df_hunt[aggregate_on], 1)

    # Aggregate table value (active_hunters or hunt days) by year for the Atlantic Flyway
    atlantic_totals = df_hunt.groupby(['season', 'survey_state'])[aggregate_on].sum().reset_index()
    # Convert values to integers
    if aggregate_on != 'bag_per_hunter':
        # Convert values to integers only if table_value is not 'bag_per_hunter'
        atlantic_totals[aggregate_on] = atlantic_totals[aggregate_on].astype(int)
    else:
        # 'bag_per_hunter' leave as is
        print_info('For values of bag_per_hunter leave as is')

    #create pivot tables
    atlantic_pivot = atlantic_totals.pivot(index='season', columns='survey_state', values=aggregate_on).fillna(0)
    
    af_totals = sum_values_by_flyway(df, 'AF', season_start, season_end, species_group, aggregate_on)
    mf_totals = sum_values_by_flyway(df, 'MF', season_start, season_end, species_group, aggregate_on)
    pf_totals = sum_values_by_flyway(df, 'PF', season_start, season_end, species_group, aggregate_on)
    cf_totals = sum_values_by_flyway(df, 'CF', season_start, season_end, species_group, aggregate_on)
    ak_totals = sum_values_by_flyway(df, 'AK', season_start, season_end, species_group, aggregate_on)
    us_totals = af_totals.add(mf_totals, fill_value=0).add(pf_totals, fill_value=0).add(cf_totals, fill_value=0).add(ak_totals, fill_value=0)


    # Merge the totals with the Atlantic Flyway DataFrame
    atlantic_pivot['AF'] = af_totals
    atlantic_pivot['MF'] = mf_totals
    atlantic_pivot['PF'] = pf_totals
    atlantic_pivot['CF'] = cf_totals
    atlantic_pivot['US'] = us_totals

    #values should be integers unless the table value is bag_per hunter
    should_convert_to_int = aggregate_on != 'bag_per_hunter'

    if should_convert_to_int:
        atlantic_pivot['AF'] = atlantic_pivot['AF'].fillna(0).astype(int)
        atlantic_pivot['MF'] = atlantic_pivot['MF'].fillna(0).astype(int)
        atlantic_pivot['PF'] = atlantic_pivot['PF'].fillna(0).astype(int)
        atlantic_pivot['CF'] = atlantic_pivot['CF'].fillna(0).astype(int)
        atlantic_pivot['US'] = atlantic_pivot['US'].fillna(0).astype(int)

    # Fill missing values with 0
    atlantic_pivot.fillna(0, inplace=True)

    
    # Calculate dynamic time period averges
    # Calculate the first period's end year to end with 0 or 5
    first_period_end_year = find_next_year_ending_in_0_or_5(season_start)

    # Initialize time periods dictionary
    time_periods = {}
    if first_period_end_year > season_start:
        time_periods[f"{season_start}-{first_period_end_year}"] = (season_start, first_period_end_year)

    # generate subsequent 5-year periods
    start_year = first_period_end_year + 1
    while start_year <= season_end:
        end_year = start_year + 4
        if end_year > season_end or (end_year % 10 != 0 and end_year % 10 != 5):
            end_year = find_next_year_ending_in_0_or_5(season_end)
            if end_year > season_end:
                end_year = season_end
        period_label = f'{start_year}-{end_year}'
        time_periods[period_label] = (start_year, end_year)
        start_year = end_year + 1

    # Ensure 'Season' is a column
    atlantic_pivot.reset_index(inplace=True)

    # Sort the data by year first (numeric only)
    atlantic_pivot['season'] = atlantic_pivot['season'].astype(str)
    numeric_years = atlantic_pivot[atlantic_pivot['season'].str.isnumeric()].copy()
    numeric_years['season'] = numeric_years['season'].astype(int)
    numeric_years.sort_values(by='season', inplace=True)

    # Calculate averages for each time period and create a DataFrame for them
    averages_rows = []
    for label, (start_year, end_year) in time_periods.items():
        # Select the data for the time period
        
        period_data = numeric_years[(numeric_years['season'] >= start_year) & (numeric_years['season'] <= end_year)]

        # Calculate the mean for each column
        averages = period_data.mean().round(0).fillna(0).astype(int)  # Round to 0 decimal places
        averages['season'] = label  # Set the label for the averages row
        averages_rows.append(averages)

    # Convert the averages list of series to a DataFrame
    averages_df = pd.DataFrame(averages_rows)

    return (numeric_years, averages_df)

def calc_harvest_tabledata_multiple_groups(df, flyway, season_start, season_end, group_list, aggregate_on):
    ''' Interate through a list of groups to generate a list of harvest table data results.'''
    data_results_arr = []
    for sp in group_list:
        print_info("Calculating harvest data for group: "+sp)
        results = calc_tabledata_for_species_group(df, flyway, season_start, season_end, sp, aggregate_on)
        data_results_arr.append((sp, flyway, results[0], results[1]))
    return data_results_arr


''' ########### FUNCTIONS: Excel Table Generation ########### '''

def generate_excel_workbook_for_multiple_groups(table_data_results_list):
    # Creating a new workbook
    wb = Workbook()

    # Removing the default 'Sheet'
    del wb['Sheet']

    for result in table_data_results_list:
        group_name = result[0]
        flyway = result[1]
        hunter_estimate_data = result[2]
        period_averages = result[3]

        asterisk_text_list = ['* Preliminary Estimate', \
                              '** For flyway estimates prior to 2015 please see the flyway-specific databook']
        

        table_title = 'Estimates of '+str(group_name)+' in the '+flyway
        # table_title = ''
        FlywayTables.create_table_to_ws(wb, hunter_estimate_data, period_averages, asterisk_text_list, table_title, group_name)
            
        workbook_name = flyway+' Hunter Data Tables.xlsx'
        wb.save(workbook_name)
    print_info('Completed Excel workbook file ['+workbook_name+']')

''' ########### MAIN FUNCTION ########### '''

@click.command()
@click.argument('filename', required=1, type=click.Path(exists=True))
@click.option('--flyway', default='AF', help='Name of the flyway. Options are AF, MF, CF, and PF. \
                Default is "AF". Value is case sensitive.')
@click.option('--seasons', default='all', help='Season range to generate. Use the notation <START>:<END>. E.g. 1999:2021. Default is ALL.')
@click.option('--species_group', default='all', help='A comma seperated list of species groups to generate tables. Possible values \
              are [brant, ducks, geese, sea ducks]. E.g. --species_group=brant,ducks,geese,sea ducks. \
              Values are case sensitive. Default is ALL.')
@click.option('--aggregate_on', default='active_hunters', help='The column name contain the value to perform aggregation on. Available options are \
              [active_hunters, bag_per_hunter, days_hunted]. The type of table generated is based on this parameter. Default is active_hunters.')
def main(flyway, seasons, species_group, aggregate_on, filename):
    print("")
    ALLOWED_AGGREGATE_ON_COL = ['active_hunters', 'bag_per_hunter', 'days_hunted']
    sdf = pd.read_csv(filename)
    print_info('Dataset '+filename+' is now stored in a Pandas Dataframe.') 
    print_info('Dataset column names='+str(sdf.columns))

    if (seasons != 'all'):
        if (re.match(r"^\d{4}:\d{4}$", seasons)):
            seasons = seasons.split(':')
            seasons = (int(seasons[0]), int(seasons[1]))
        else:
            print_fatal_exit("Invalid season parameter value. Please refer to --help for more information.")
    else: 
        all_seasons = sdf['season'].unique()
        all_seasons.sort()
        seasons = (int(all_seasons[0]), int(all_seasons[-1]))

    if (species_group == 'all'):
        species_group = sdf['sp_group_estimated'].unique()
    
    print_info('Processed input parameters:')
    print_info(flyway)
    print_info(seasons)
    print_info(species_group)
    print_info('Aggregate On: '+ aggregate_on)

    # Validating aggregate_on parameter value
    if aggregate_on.lower() not in ALLOWED_AGGREGATE_ON_COL:
        print_fatal_exit("Invalid aggregate_on parameter value ["+aggregate_on+"]. Please refer to --help for more information.")

    big_results = calc_harvest_tabledata_multiple_groups(sdf, flyway, seasons[0], seasons[1], species_group,  aggregate_on)
    # Genernating Excel workbook tables from all results.
    generate_excel_workbook_for_multiple_groups(big_results)


if __name__ == '__main__':
    ''' Program entry point '''
    main()