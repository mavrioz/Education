# jbc -*- coding: utf-8 -*-
"""
Created on Thu Oct 29 12:34:23 2020

@author: laura.tracey
"""

import pandas as pd
from os import listdir
from os.path import isfile, join
import re
from datetime import datetime, timedelta
import numpy as np

# import Northern Ireland data


def get_nireland_data(filepath: str):

    onlyfiles = [f for f in listdir(filepath) if isfile(join(filepath, f))]
    files = pd.DataFrame(onlyfiles, columns=["filename"])
    files["filedate"] = files["filename"].str.findall(r"\d+")
    files["filedate"] = (
        files["filedate"]
        .astype("str")
        .str.replace("[", "")
        .str.replace("]", "")
        .str.replace("'", "")
        .str.replace(", 2", "")
        .str.replace(", 1", "")
    )
    files = files.replace("", np.nan, regex=True)
    files["filedate"] = pd.to_datetime(files["filedate"], format="%d%m%y")
    latest_file = files[files["filedate"] == max(files["filedate"])]["filename"]
    latest_file = latest_file.to_string(index=False).strip()
    print(latest_file)
    NI_dash = pd.read_excel(filepath + latest_file, sheet_name="Individual Tests - LGD")
    # Sum positive and negative cases over ages and gender for each date and LTLA
    NI_tests = NI_dash.groupby(["Date of Sample", "LGD"], as_index=False).agg(
        {"Positive Individuals": "sum", "Negative Individuals": "sum"}
    )
    # rename columns
    NI_tests = NI_tests.rename(
        {
            "Date of Sample": "date",
            "LGD": "LTLA",
            "Positive Individuals": "positive_tests",
            "Negative Individuals": "negative_tests",
        },
        axis="columns",
    )
    # drop first row containing a string
    NI_tests.drop(NI_tests.index[0], inplace=True)
    NI_tests["total_tests"] = NI_tests["positive_tests"] + NI_tests["negative_tests"]
    # Add da identifier column
    NI_tests["da"] = "Northern Ireland"
    return NI_tests


def get_scotland_data(filepath: str):

    onlyfiles = [f for f in listdir(filepath) if isfile(join(filepath, f))]
    files = pd.DataFrame(onlyfiles, columns=["filename"])
    files["filedate"] = files["filename"].str.findall(r"\d+")
    files["filedate"] = files["filedate"].astype("str").str.replace("[", "").str.replace("]", "").str.replace("'", "")
    files = files.replace("", np.nan, regex=True)
    files["filedate"] = pd.to_datetime(files["filedate"], format="%d%m%Y")
    latest_file = files[files["filedate"] == max(files["filedate"])]["filename"]
    latest_file = latest_file.to_string(index=False).strip()
    print(latest_file)
    # import positive and negative Scotland data
    scot_pos = pd.read_excel(filepath + latest_file, sheet_name="UKGov Positive Tests")
    scot_neg = pd.read_excel(filepath + latest_file, sheet_name="UKGov Negative Tests")
    # Unpivot and replace na's with 0's
    scot_pos_up = pd.melt(scot_pos, id_vars=["SpecimenDate"], var_name="LTLA", value_name="positive_tests")

    scot_pos_up = scot_pos_up.fillna(0)
    scot_neg_up = pd.melt(scot_neg, id_vars=["SpecimenDate"], var_name="LTLA", value_name="negative_tests")
    scot_neg_up = scot_neg_up.fillna(0)
    # Merge dataframes
    scot_tests = pd.merge(scot_pos_up, scot_neg_up, on=["SpecimenDate", "LTLA"])
    scot_tests = scot_tests.rename({"SpecimenDate": "date"}, axis="columns")
    # remove grand total row from date column
    scot_tests = scot_tests[~scot_tests["date"].isin(["Grand Total", "Total"])]
    # Check for nulls which indicate mismatched LTLA's and dates between tables
    null_check = scot_tests.isna().sum()
    print(null_check)
    # Create new columns
    scot_tests["total_tests"] = scot_tests["positive_tests"] + scot_tests["negative_tests"]
    scot_tests["da"] = "Scotland"
    return scot_tests


def get_wales_data(link: int = 1):
    # Import wales data
    if link == 1:
        wales_tests = pd.read_excel(
            "http://www2.nphs.wales.nhs.uk:8080/CommunitySurveillanceDocs.nsf/3dc04669c9e1eaa880257062003b246b/77fdb9a33544aee88025855100300cab/$FILE/Rapid%20COVID-19%20surveillance%20data.xlsx",
            "Tests by specimen date",
            parse_dates=["Specimen date"],
        )
    elif link == 2:
        wales_tests = pd.read_excel(
            "https://www2.nphs.wales.nhs.uk/CommunitySurveillanceDocs.nsf/61c1e930f9121fd080256f2a004937ed/4e819921339b96308025861d004a8769/$FILE/Rapid%20COVID-19%20surveillance%20data.xlsx",
            "Tests by specimen date",
            parse_dates=["Specimen date"],
        )
    else:
        raise ValueError("Error: please select link 1 or 2")

    # rename columns
    wales_tests = wales_tests.rename(
        {
            "Specimen date": "date",
            "Local Authority": "LTLA",
            "Cases (new)": "positive_tests",
            "Testing episodes (new)": "total_tests",
        },
        axis="columns",
    )
    wales_tests["negative_tests"] = "Data Unavailable"
    wales_tests["da"] = "Wales"
    wales_tests = wales_tests[["date", "LTLA", "positive_tests", "negative_tests", "total_tests", "da"]]
    wales_tests["date"] = pd.to_datetime(wales_tests["date"])
    return wales_tests


def summarise_data(excel_file: str, filepath: str):
    """
    Imports all england pos/neg/void data files
    """
    print(excel_file)
    filepath = filepath
    the_date = re.search("pillar2_testing_(.*)_CabOff", excel_file).group(1)
    the_data = pd.read_excel(filepath + excel_file, header=None)
    for i, row in the_data.iterrows():
        if row.notnull().all():
            data = the_data.iloc[(i + 1) :].reset_index(drop=True)
            data.columns = list(the_data.iloc[i])
            break
    the_data = data
    the_date = the_date.rstrip("_")
    if "Jan" in the_date:
        the_data["date"] = datetime.strptime(the_date + "_2021", "%d_%b_%Y") - timedelta(days=3)
    else:
        the_data["date"] = datetime.strptime(the_date + "_2020", "%d_%b_%Y") - timedelta(days=3)
    return the_data


def get_england_data():
    # Import England data
    eng_data = pd.read_csv(
        "https://api.coronavirus.data.gov.uk/v2/data?areaType=ltla&metric=uniqueCasePositivityBySpecimenDateRollingSum&metric=uniquePeopleTestedBySpecimenDateRollingSum&format=csv"
    )
    utla_ltla_mapping = pd.read_excel("data/utla_ltla_mapping.xlsx")

    london = utla_ltla_mapping[utla_ltla_mapping["UTLA code"] == "E09000001"]
    london["LTLACodeData"] = "E09000012"
    london = london.merge(eng_data, left_on="LTLACodeData", right_on="areaCode", how="left")
    london = london.drop(["UTLA code", "UTLA name", "LTLACodeData", "areaCode", "areaName"], axis=1)
    london = london.rename({"LTLA code": "areaCode", "LTLA name": "areaName"}, axis=1)

    df = pd.concat([london, eng_data])
    df["da"] = "England"
    df_las = df.sort_values(by=["areaCode", "date"])
    df_las = df_las.rename(
        {
            "uniquePeopleTestedBySpecimenDateRollingSum": "Sum of Tests",
            "uniqueCasePositivityBySpecimenDateRollingSum": "la_positivity_rate",
        },
        axis=1,
    )
    df_las["Sum of Positive"] = (df_las["la_positivity_rate"] / 100) * df_las["Sum of Tests"]
    df_las["la_positivity_rate_7_day_diff"] = df_las["la_positivity_rate"] - df_las["la_positivity_rate"].shift(7)
    df_las_final = df_las[
        [
            "date",
            "da",
            "areaName",
            "Sum of Positive",
            "Sum of Tests",
            "la_positivity_rate",
            "la_positivity_rate_7_day_diff",
        ]
    ].rename(
        {
            "areaName": "LTLA",
            "Sum of Positive": "weekly_positive_tests",
            "Sum of Tests": "weekly_total_tests",
            "la_positivity_rate": "weekly_positivity_rate",
            "la_positivity_rate_7_day_diff": "perc_point_diff_7_days",
        },
        axis=1,
    )
    df_las_final["LTLA"] = np.where(
        df_las_final["LTLA"] == "Cornwall and Isles of Scilly",
        "Cornwall",
        np.where(df_las_final["LTLA"] == "Hackney and City of London", "Hackney", df_las_final["LTLA"]),
    )
    df_las_final["positive_tests"] = np.nan
    df_las_final["negative_tests"] = np.nan
    df_las_final["total_tests"] = np.nan
    return df_las_final


# Regions data
MANCHESTER_CITY_REGION = [
    "Manchester",
    "Bolton",
    "Bury",
    "Stockport",
    "Tameside",
    "Trafford",
    "Wigan",
    "Salford",
    "Rochdale",
    "Oldham",
]

LIVERPOOL_CITY_REGION = ["Liverpool", "Knowsley", "Wirral", "St. Helens", "Sefton", "Halton"]

LANCASHIRE = [
    "Blackburn with Darwen",
    "Blackpool",
    "Burnley",
    "Chorley",
    "Fylde",
    "Hyndburn",
    "Lancaster",
    "Pendle",
    "Preston",
    "Ribble Valley",
    "Rossendale",
    "South Ribble",
    "West Lancashire",
    "Wyre",
]


# Create function to add shift of 7 days (starting at today)
def sum_of_prev_days(days: int, df, column: str):
    """
    Function takes number of days to sum together and dataframe
    """
    sum = 0
    for i in range(0, days):
        sum = sum + df[column].shift(i)
    return sum


def region_aggregation(REGION, df, region_name: str):
    region = df[df.LTLA.isin(REGION)].groupby(["date"], as_index=False).sum()
    region["la_positivity_rate"] = region["weekly_positive_tests"] / region["weekly_total_tests"] * 100
    region.sort_values(by=["date"], inplace=True)
    region["weekly_positivity_rate"] = region["la_positivity_rate"].interpolate(method="linear")
    # region["interpolation_line"] = np.where(region['la_positivity_rate'].isna(), "Yes", np.nan)
    region["perc_point_diff_7_days"] = region["weekly_positivity_rate"] - region["weekly_positivity_rate"].shift(7)
    region = region.drop(["la_positivity_rate"], axis=1)
    region["LTLA"] = region_name
    return region


def england_tiers_func(tier: str, df, tiers_df):
    tier_col = "LTLA19_Name"
    tiers_data = df[df.LTLA.isin(tiers_df[tier_col])].groupby(["date"], as_index=False).sum()
    tiers_data["la_positivity_rate"] = tiers_data["weekly_positive_tests"] / tiers_data["weekly_total_tests"] * 100
    tiers_data.sort_values(by=["date"], inplace=True)
    tiers_data["weekly_positivity_rate"] = tiers_data["la_positivity_rate"].interpolate(method="linear")
    # tiers_data["interpolation_line"] = np.where(tiers_data['la_positivity_rate'].isna(), "Yes", np.nan)
    tiers_data["perc_point_diff_7_days"] = tiers_data["weekly_positivity_rate"] - tiers_data[
        "weekly_positivity_rate"
    ].shift(7)
    tiers_data = tiers_data.drop(["la_positivity_rate"], axis=1)
    tiers_data["LTLA"] = tier
    return tiers_data


def scotland_level_func(Scotland_level: str, df, level_df):
    level = df[df.LTLA.isin(level_df["Local authority area"])].groupby(["date"], as_index=False).sum()
    level["weekly_positivity_rate"] = level["weekly_positive_tests"] / level["weekly_total_tests"] * 100
    level["perc_point_diff_7_days"] = level["weekly_positivity_rate"] - level["weekly_positivity_rate"].shift(7)
    level["LTLA"] = Scotland_level
    return level


def join_da_data(ni_filepath: str, scot_filepath: str, wales_link: int):
    # Append the tables together
    tests = get_nireland_data(ni_filepath).append(get_scotland_data(scot_filepath))
    tests = tests.append(get_wales_data(wales_link))
    # Sort columns
    tests["date"] = pd.to_datetime(tests["date"])
    tests = tests.sort_values(by=["LTLA", "date"])
    # Create new columns which are sum of 7 previous values
    tests["weekly_positive_tests"] = sum_of_prev_days(7, tests, "positive_tests")
    tests["weekly_total_tests"] = sum_of_prev_days(7, tests, "total_tests")
    # drop NANs
    tests.dropna(subset=["weekly_positive_tests", "weekly_total_tests"], inplace=True)
    # drop zeroes...
    tests = tests[tests["weekly_total_tests"] != 0]
    tests["weekly_positivity_rate"] = (tests["weekly_positive_tests"] / tests["weekly_total_tests"]) * 100
    # Create column to calculate change in positivity rate
    tests["perc_point_diff_7_days"] = tests["weekly_positivity_rate"] - tests["weekly_positivity_rate"].shift(7)
    eng_data = get_england_data()
    tests = pd.concat([eng_data, tests])
    return tests, eng_data


def group_calculations(geography, df):
    if geography == "da":
        df = df.groupby(["date", "da"], as_index=False).sum()
    elif geography == "UK":
        df = df
        df["weekly_positive_tests"] = np.where(
            (df.LTLA == "England") & (df.weekly_positive_tests == 0), np.nan, df.weekly_positive_tests
        )
        df["weekly_total_tests"] = np.where(
            (df.LTLA == "England") & (df.weekly_total_tests == 0), np.nan, df.weekly_total_tests
        )
        df = df.assign(da=geography)
        df["weekly_positive_tests"] = df["weekly_positive_tests"].interpolate(method="linear")
        df["weekly_total_tests"] = df["weekly_total_tests"].interpolate(method="linear")
        df = df.groupby(["da", "date"], as_index=False).sum()
    else:
        # df["weekly_positive_tests"] = np.where((df.LTLA == 'England') & (df.weekly_positive_tests == 0), np.nan, df.weekly_positive_tests)
        # df["weekly_total_tests"] = np.where((df.LTLA == 'England') & (df.weekly_total_tests == 0), np.nan, df.weekly_total_tests)
        df = df.assign(da=geography)
        df["weekly_positive_tests"] = pd.to_numeric(df["weekly_positive_tests"]).interpolate(method="linear")
        df["weekly_total_tests"] = pd.to_numeric(df["weekly_total_tests"]).interpolate(method="linear")
        df = df.groupby([geography, "da", "date"], as_index=False).sum()

    df["la_positivity_rate"] = df["weekly_positive_tests"] / df["weekly_total_tests"] * 100
    if geography != "UK":
        df.sort_values(by=[geography, "date"], inplace=True)
    else:
        df.sort_values(by=["date"], inplace=True)
    df["weekly_positivity_rate"] = df["la_positivity_rate"].interpolate(method="linear")
    # df["interpolation_line"] = np.where(df['la_positivity_rate'].isna(), "Yes", np.nan)
    df["perc_point_diff_7_days"] = df["weekly_positivity_rate"] - df["weekly_positivity_rate"].shift(7)
    df = df.drop(["la_positivity_rate"], axis=1)
    if geography != "UK":
        df["LTLA"] = df[geography]
    else:
        df["LTLA"] = df["da"]

    return df


def get_final_positivity_data(ni_filepath: str, scot_filepath: str, wales_link: int, jbc_path: str, ltla_list: list):
    utla_ltla_mapping = pd.read_excel("data/utla_ltla_mapping.xlsx")

    # Tier data
    england_tiers = pd.read_excel(jbc_path)
    # se_emergency_tiers = pd.read_excel("data/se_emergency_tiers.xlsx")
    extra_tiers = pd.read_excel("data/extra_ltlas.xlsx")
    #    scotland_tiers = pd.read_excel("data/scot_tiers.xlsx")
    #    scotland_level_one = scotland_tiers[scotland_tiers['Protection level']=='Level 1']
    #    scotland_level_two = scotland_tiers[scotland_tiers['Protection level']=='Level 2']
    #    scotland_level_three = scotland_tiers[scotland_tiers['Protection level']=='Level 3']
    england_tiers = england_tiers.rename(columns={"Tier_Name": "Tier Name"})
    england_tier_1 = england_tiers[england_tiers["Tier Name"] == "Tier 1"]
    england_tier_2 = england_tiers[england_tiers["Tier Name"] == "Tier 2"]
    england_tier_3 = england_tiers[england_tiers["Tier Name"] == "Tier 3"]
    england_tier_4 = england_tiers[england_tiers["Tier Name"] == "Tier 4"]

    matched_data, regions_data = join_da_data(
        ni_filepath=ni_filepath, scot_filepath=scot_filepath, wales_link=wales_link
    )

    england_totals = pd.read_csv(
        "https://api.coronavirus.data.gov.uk/v2/data?areaType=nation&areaCode=E92000001&metric=uniqueCasePositivityBySpecimenDateRollingSum&metric=uniquePeopleTestedBySpecimenDateRollingSum&format=csv"
    )
    england_totals = england_totals.drop(["areaType", "areaCode"], axis=1).rename(
        {
            "areaName": "da",
            "uniqueCasePositivityBySpecimenDateRollingSum": "weekly_positivity_rate",
            "uniquePeopleTestedBySpecimenDateRollingSum": "weekly_total_tests",
        },
        axis=1,
    )
    england_totals["weekly_positive_tests"] = (england_totals["weekly_positivity_rate"] / 100) * england_totals[
        "weekly_total_tests"
    ]
    england_totals["perc_point_diff_7_days"] = england_totals["weekly_positive_tests"] - england_totals[
        "weekly_positive_tests"
    ].shift(7)
    england_totals["positive_tests"] = np.nan
    england_totals["total_tests"] = np.nan
    england_totals["LTLA"] = "England"
    england_totals["date"] = pd.to_datetime(england_totals["date"])

    national = group_calculations(geography="da", df=matched_data[matched_data["da"] != "England"])
    # [~matched_data.LTLA.isin(['Aylesbury Vale',
    #                                                             'Chiltern',
    #                                                             'South Bucks',
    #                                                             'Wycombe'])])
    national = pd.concat([england_totals, national])

    uk = group_calculations(geography="UK", df=national)

    region_data = pd.read_csv(
        "https://api.coronavirus.data.gov.uk/v2/data?areaType=region&metric=uniqueCasePositivityBySpecimenDateRollingSum&metric=uniquePeopleTestedBySpecimenDateRollingSum&format=csv"
    )
    region_data = region_data.drop(["areaType", "areaCode"], axis=1).rename(
        {
            "areaName": "LTLA",
            "uniqueCasePositivityBySpecimenDateRollingSum": "weekly_positivity_rate",
            "uniquePeopleTestedBySpecimenDateRollingSum": "weekly_total_tests",
        },
        axis=1,
    )
    region_data["weekly_positive_tests"] = (region_data["weekly_positivity_rate"] / 100) * region_data[
        "weekly_total_tests"
    ]

    region_data["LTLA"] = np.where(
        region_data.LTLA.isin(["East Midlands", "West Midlands"]),
        "Midlands",
        np.where(
            region_data.LTLA.isin(["Yorkshire and The Humber", "North East"]),
            "North East and Yorkshire",
            region_data.LTLA,
        ),
    )

    region_data = region_data.groupby(["LTLA", "date"], as_index=False).sum()

    region_data["weekly_positivity_rate"] = np.where(
        region_data.LTLA.isin(["Midlands", "North East and Yorkshire"]),
        region_data.weekly_positive_tests / region_data.weekly_total_tests * 100,
        region_data.weekly_positivity_rate,
    )
    region_data["da"] = "England"
    region_data["date"] = pd.to_datetime(region_data["date"])

    # regions_data = regions_data.merge(utla_ltla_mapping, left_on = 'LTLA',
    #                                   right_on="LTLA name", how='left').merge(
    #                                        england_tiers,
    #                                        left_on = 'LTLA code',
    #                                        right_on = 'LTLA19_ONS_Code', how = 'left')

    # se_emergency_matched = se_emergency_tiers.merge(matched_data,
    #                                        right_on = 'LTLA',
    #                                        left_on = 'LTLA19_Name', how = 'inner')

    # df_se = group_calculations(geography="JBC_Area_Name", df = se_emergency_matched)
    # df_se['LTLA'] = df_se['JBC_Area_Name']
    extra_tiers_matched = extra_tiers.merge(matched_data, right_on="LTLA", left_on="LTLA19_Name", how="inner")

    df_extra = group_calculations(geography="JBC_Area_Name", df=extra_tiers_matched)
    df_extra["LTLA"] = df_extra["JBC_Area_Name"]

    max_eng_date = max(region_data.date)
    # df_utlas = group_calculations(geography = 'UTLA name', df = regions_data)
    # df_reg = group_calculations(geography = 'Region_ONS_Name', df = regions_data)
    # ~regions_data.LTLA.isin(['Aylesbury Vale',
    #                                                                                       'Chiltern',
    #                                                                                       'South Bucks',
    #                                                                                       'Wycombe'])])

    matched_data["Tier Name"] = np.where(
        matched_data.LTLA.isin(england_tier_1["LTLA19_Name"]),
        "Tier 1",
        np.where(
            matched_data.LTLA.isin(england_tier_2["LTLA19_Name"]),
            "Tier 2",
            np.where(
                matched_data.LTLA.isin(england_tier_3["LTLA19_Name"]),
                "Tier 3",
                np.where(matched_data.LTLA.isin(england_tier_4["LTLA19_Name"]), "Tier 4", "No Tier"),
            ),
        ),
    )
    #                        np.where(
    #                                matched_data.LTLA.isin(scotland_level_one['Local authority area']),
    #                                "Scotland - Level 1",
    #                                np.where(
    #                                        matched_data.LTLA.isin(scotland_level_two['Local authority area']),
    #                                        "Scotland - Level 2",
    #                                        np.where(
    #                                                matched_data.LTLA.isin(scotland_level_three['Local authority area']),
    #                                                "Scotland - Level 3",
    #                                                "No Tier"))))))
    tier_one = england_tiers_func("Tier 1", df=matched_data, tiers_df=england_tier_1)
    tier_two = england_tiers_func("Tier 2", matched_data, england_tier_2)
    tier_three = england_tiers_func("Tier 3", matched_data, england_tier_3)
    tier_four = england_tiers_func("Tier 4", matched_data, england_tier_4)

    jbc_reg_data = matched_data.merge(england_tiers, left_on="LTLA", right_on="LTLA19_Name", how="left")

    grouped_tiers = (
        england_tiers[["JBC_Area_Name", "Tier Name", "LTLA19_Name"]]
        .groupby(["JBC_Area_Name", "Tier Name"], as_index=False)
        .count()
    )
    multiple_tiers = grouped_tiers.groupby("JBC_Area_Name", as_index=False).count()
    multiple_tiers = multiple_tiers[multiple_tiers["Tier Name"] > 1]

    # jbc_reg_data['JBC_Area_Name'] = np.where(jbc_reg_data.JBC_Area_Name.isin(multiple_tiers['JBC_Area_Name']),
    #                                          jbc_reg_data['JBC_Area_Name'] + " - " + jbc_reg_data["Tier Name_x"],
    #                                          jbc_reg_data['JBC_Area_Name'])

    jbc_tiers = (
        jbc_reg_data[["JBC_Area_Name", "Tier Name_x"]].drop_duplicates().rename({"Tier Name_x": "Tier Name"}, axis=1)
    )

    # filter out city of london ashackney and city of london are merged in cornavirus dataset. avoid double counting.
    df_jbc_reg = group_calculations(
        geography="JBC_Area_Name", df=jbc_reg_data[jbc_reg_data["LTLA"] != "City of London"]
    ).merge(jbc_tiers, on="JBC_Area_Name", how="left")

    df_jbc_reg["LTLA"] = df_jbc_reg["JBC_Area_Name"]

    #    edge_data = pd.read_excel("data/LTLA_edge_cases.xlsx")
    #    edge_data = matched_data.merge(edge_data,
    #                                      left_on = "LTLA",
    #                                      right_on = "Local Authority",
    #                                      how = "left")
    #
    #    edge_group = group_calculations(geography = "Edge case area", df = edge_data)

    # scotland_level_one = scotland_tiers[scotland_tiers['Protection level']=='Level 1']
    # scotland_level_two = scotland_tiers[scotland_tiers['Protection level']=='Level 2']
    # scotland_level_three = scotland_tiers[scotland_tiers['Protection level']=='Level 3']
    # level_one = scotland_level_func('Scotland - Level 1',matched_data,scotland_level_one)
    # level_two = scotland_level_func('Scotland - Level 2',matched_data,scotland_level_two)
    # level_three = scotland_level_func('Scotland - Level 3',matched_data,scotland_level_three)

    add_ltlas = regions_data[regions_data.LTLA.isin(ltla_list)]

    final_data = pd.concat([df_jbc_reg, region_data])
    # final_data = pd.concat([df_se, final_data])
    # final_data = pd.concat([df_extra, final_data])
    # final_data = pd.concat([tier_one,final_data])
    # final_data = pd.concat([tier_two,final_data])
    # final_data = pd.concat([tier_three,final_data])
    # final_data = pd.concat([tier_four, final_data])
    # final_data = pd.concat([edge_group, final_data])
    final_data = pd.concat([national, final_data])
    final_data = pd.concat([uk, final_data])
    final_data = pd.concat([add_ltlas, final_data])
    final_data["date"] = pd.to_datetime(final_data["date"])
    final_data = final_data[final_data["date"] <= max_eng_date]
    filter_las = {"NULL", "Unknown", "Unnamed: 1"}
    final_data = final_data[~final_data.LTLA.isin(filter_las)]
    matched_data["date"] = pd.to_datetime(matched_data["date"])
    matched_data = matched_data[matched_data["date"] <= max_eng_date]
    return final_data, matched_data
    # positivity_data = pd.concat([level_two,positivity_data])
    # positivity_data = pd.concat([level_three,positivity_data])


# manc = region_aggregation(MANCHESTER_CITY_REGION,positivity_data,"Greater Manchester")
# lpool = region_aggregation(LIVERPOOL_CITY_REGION,positivity_data,"Liverpool City Region")
# lanc = region_aggregation(LANCASHIRE,positivity_data,"Lancashire")

# positivity_data = pd.concat([lanc,positivity_data])
# positivity_data = pd.concat([lpool,positivity_data])
# positivity_data = pd.concat([manc,positivity_data])
