"""
Build the four data CSVs for the Marathon Majors Course Difficulty study.

Outputs (deterministic via fixed seed):
  data/majors_results.csv   - top-100 men + top-100 women per (course x year)
  data/race_weather.csv     - one row per (course, year) with race-day weather
  data/paired_runners.csv   - within-runner course-pair observations

The Majors results are a compiled / simulated reconstruction calibrated to
publicly known winning times. Each elite athlete is given a 'flat ability'
drawn from a realistic marathon-performance distribution. Race-day times
are produced by:

    time = ability
         + course_penalty[course]         (Boston/NYC slower than flat)
         + weather_penalty[year,course]   (degC / humidity adjustment)
         + race_noise                     (within-race tactical variation)

The course penalties used here are PRIORS used only for synthesis; the
analysis in analysis.py recovers course difficulty from the results
themselves, so any drift away from these priors is informative.

Race dates and weather are anchored to public reality (Boston 2018 storm,
warm Berlin years, etc.). Years 2015-2024 minus 2020 (virtual / cancelled).
"""

import os
import numpy as np
import pandas as pd
from datetime import date

RNG = np.random.default_rng(42)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(os.path.dirname(BASE_DIR), 'data')
os.makedirs(DATA_DIR, exist_ok=True)


# ── Race calendar ─────────────────────────────────────────────
RACE_DATES = {
    'boston':  {2015: '2015-04-20', 2016: '2016-04-18', 2017: '2017-04-17', 2018: '2018-04-16',
                2019: '2019-04-15', 2021: '2021-10-11', 2022: '2022-04-18', 2023: '2023-04-17',
                2024: '2024-04-15'},
    'chicago': {2015: '2015-10-11', 2016: '2016-10-09', 2017: '2017-10-08', 2018: '2018-10-07',
                2019: '2019-10-13', 2021: '2021-10-10', 2022: '2022-10-09', 2023: '2023-10-08',
                2024: '2024-10-13'},
    'nyc':     {2015: '2015-11-01', 2016: '2016-11-06', 2017: '2017-11-05', 2018: '2018-11-04',
                2019: '2019-11-03', 2021: '2021-11-07', 2022: '2022-11-06', 2023: '2023-11-05',
                2024: '2024-11-03'},
    'london':  {2015: '2015-04-26', 2016: '2016-04-24', 2017: '2017-04-23', 2018: '2018-04-22',
                2019: '2019-04-28', 2021: '2021-10-03', 2022: '2022-10-02', 2023: '2023-04-23',
                2024: '2024-04-21'},
    'berlin':  {2015: '2015-09-27', 2016: '2016-09-25', 2017: '2017-09-24', 2018: '2018-09-16',
                2019: '2019-09-29', 2021: '2021-09-26', 2022: '2022-09-25', 2023: '2023-09-24',
                2024: '2024-09-29'},
    'tokyo':   {2015: '2015-02-22', 2016: '2016-02-28', 2017: '2017-02-26', 2018: '2018-02-25',
                2019: '2019-03-03', 2021: '2021-10-17', 2022: '2022-03-06', 2023: '2023-03-05',
                2024: '2024-03-03'},
}

COURSES = ['boston', 'nyc', 'chicago', 'berlin', 'london', 'tokyo']
YEARS = [2015, 2016, 2017, 2018, 2019, 2021, 2022, 2023, 2024]

# Course-difficulty PRIORS in seconds vs flat reference.
# These are used only to synthesize times; the analysis re-estimates them.
COURSE_PENALTY = {
    'berlin':  0,
    'chicago': 12,
    'london':  35,
    'tokyo':   28,
    'nyc':     85,
    'boston':  105,
}

# ── Race weather (anchored to known reality where possible) ───
# Format: (start_temp_c, humidity_pct, dewpoint_c, wind_kph, note)
WEATHER_DATA = {
    ('boston', 2015): (5.0, 75, 1.0, 25, 'cold_rain'),
    ('boston', 2016): (16.0, 55, 7.0, 15, 'warm'),
    ('boston', 2017): (22.0, 50, 10.0, 18, 'warm_humid'),
    ('boston', 2018): (3.9, 95, 3.0, 40, 'driving_rain'),
    ('boston', 2019): (10.0, 80, 6.0, 18, 'mild_humid'),
    ('boston', 2021): (12.0, 65, 5.0, 14, 'fall_race'),
    ('boston', 2022): (12.0, 70, 6.0, 16, 'mild'),
    ('boston', 2023): (15.0, 75, 10.0, 20, 'warm_rain'),
    ('boston', 2024): (10.0, 60, 4.0, 12, 'optimal'),

    ('chicago', 2015): (12.0, 65, 5.0, 14, 'optimal'),
    ('chicago', 2016): (12.0, 75, 7.0, 18, 'optimal_humid'),
    ('chicago', 2017): (14.0, 80, 10.0, 14, 'warm'),
    ('chicago', 2018): (11.0, 80, 7.0, 16, 'mild'),
    ('chicago', 2019): (14.0, 70, 8.0, 12, 'optimal'),
    ('chicago', 2021): (16.0, 60, 8.0, 10, 'warm'),
    ('chicago', 2022): (15.0, 55, 5.0, 12, 'optimal'),
    ('chicago', 2023): (11.0, 70, 5.0, 12, 'optimal'),
    ('chicago', 2024): (12.0, 65, 5.0, 12, 'optimal'),

    ('nyc', 2015): (10.0, 70, 4.0, 18, 'cold_windy'),
    ('nyc', 2016): (13.0, 60, 5.0, 16, 'mild'),
    ('nyc', 2017): (16.0, 55, 7.0, 14, 'warm'),
    ('nyc', 2018): (11.0, 60, 3.0, 15, 'mild'),
    ('nyc', 2019): (12.0, 55, 3.0, 16, 'mild_windy'),
    ('nyc', 2021): (14.0, 50, 4.0, 12, 'optimal'),
    ('nyc', 2022): (16.0, 55, 7.0, 14, 'warm'),
    ('nyc', 2023): (11.0, 65, 4.0, 14, 'mild'),
    ('nyc', 2024): (13.0, 60, 5.0, 12, 'mild'),

    ('london', 2015): (10.0, 75, 5.0, 12, 'optimal'),
    ('london', 2016): (12.0, 70, 6.0, 14, 'optimal'),
    ('london', 2017): (12.0, 65, 5.0, 18, 'mild_windy'),
    ('london', 2018): (23.5, 50, 12.0, 16, 'hot_record_heat'),
    ('london', 2019): (16.0, 60, 8.0, 14, 'warm'),
    ('london', 2021): (12.0, 75, 7.0, 12, 'autumn'),
    ('london', 2022): (12.0, 70, 6.0, 14, 'autumn'),
    ('london', 2023): (10.0, 70, 4.0, 12, 'optimal'),
    ('london', 2024): (13.0, 65, 6.0, 14, 'mild'),

    ('berlin', 2015): (14.0, 70, 8.0, 12, 'optimal'),
    ('berlin', 2016): (15.0, 65, 8.0, 10, 'optimal'),
    ('berlin', 2017): (13.0, 90, 11.0, 18, 'humid'),
    ('berlin', 2018): (15.0, 65, 8.0, 12, 'optimal_kipchoge_WR'),
    ('berlin', 2019): (12.0, 80, 8.0, 10, 'optimal'),
    ('berlin', 2021): (14.0, 65, 7.0, 12, 'optimal'),
    ('berlin', 2022): (18.0, 55, 8.0, 10, 'warm_kipchoge_WR'),
    ('berlin', 2023): (15.0, 60, 7.0, 8, 'optimal_assefa_WR'),
    ('berlin', 2024): (14.0, 65, 7.0, 10, 'optimal'),

    ('tokyo', 2015): (10.0, 50, 0.0, 10, 'cool'),
    ('tokyo', 2016): (8.0, 55, 0.0, 12, 'cool'),
    ('tokyo', 2017): (9.0, 50, -1.0, 14, 'cool'),
    ('tokyo', 2018): (10.0, 70, 5.0, 16, 'mild_rain'),
    ('tokyo', 2019): (8.0, 60, 1.0, 18, 'cool_windy'),
    ('tokyo', 2021): (16.0, 60, 8.0, 8, 'warm_fall'),
    ('tokyo', 2022): (8.0, 50, -1.0, 10, 'cool'),
    ('tokyo', 2023): (9.0, 55, 0.0, 12, 'cool'),
    ('tokyo', 2024): (11.0, 60, 3.0, 10, 'optimal'),
}


def write_weather():
    rows = []
    for (course, year), (t, h, d, w, note) in WEATHER_DATA.items():
        rows.append({
            'course': course,
            'year': year,
            'date': RACE_DATES[course][year],
            'start_temp_c': t,
            'start_humidity': h,
            'start_dewpoint_c': d,
            'start_wind_kph': w,
            'conditions_note': note,
        })
    df = pd.DataFrame(rows).sort_values(['course', 'year']).reset_index(drop=True)
    df.to_csv(os.path.join(DATA_DIR, 'race_weather.csv'), index=False)
    print(f"  ✓ race_weather.csv ({len(df)} rows)")
    return df


# ── Weather penalty model (Maughan / El Helou-style) ──────────
def weather_penalty(temp_c, humidity, wind_kph):
    """Marathon time penalty in seconds vs optimal (~10C, 50% rh, calm)."""
    # Temp: ~0.5% per degC above 10C (Maughan curve), small bonus below 10C floor at 5C
    if temp_c > 10:
        temp_pen = (temp_c - 10) * 0.005   # 0.5% per degC
    elif temp_c < 5:
        temp_pen = (5 - temp_c) * 0.002    # cold penalty (handling/clothes)
    else:
        temp_pen = 0
    # Humidity: ~0.05% per percentage point above 60
    hum_pen = max(0, humidity - 60) * 0.0005
    # Wind: ~0.05% per kph above 15 (rough average; net wind cost in open courses)
    wind_pen = max(0, wind_kph - 15) * 0.0005
    return temp_pen + hum_pen + wind_pen  # multiplicative (fraction of finish time)


# ── Athlete pool ──────────────────────────────────────────────
COUNTRIES_M = ['KEN', 'ETH', 'ERI', 'UGA', 'TZA', 'JPN', 'USA', 'GBR', 'NED', 'NOR',
               'CAN', 'AUS', 'MAR', 'BRA', 'GER', 'ESP', 'ITA', 'FRA', 'BLR', 'BHR']
COUNTRIES_W = ['KEN', 'ETH', 'JPN', 'BHR', 'USA', 'GBR', 'NED', 'GER', 'ITA',
               'CAN', 'AUS', 'POL', 'RUS', 'ISR', 'IRL', 'ESP', 'CHN', 'ROU', 'CZE', 'PRK']


def make_athlete_pool(gender, n):
    """Generate a pool of n athletes with flat-marathon abilities (seconds)."""
    # Distribution anchored on realistic elite reality:
    # M: best ~7270 (~2:01:10), median elite ~7800, sub-2:20 cutoff 8400
    # W: best ~7800 (~2:10), median elite ~8600, sub-2:40 cutoff 9600
    if gender == 'M':
        # right-skewed: log-normal with floor
        floor = 7270
        abilities = floor + RNG.lognormal(mean=5.6, sigma=0.55, size=n)
        abilities = np.clip(abilities, floor, 8400)
        first_names = ['Eliud','Kelvin','Geoffrey','Wilson','Lawrence','Birhanu','Tamirat','Lelisa',
                       'Mosinet','Sisay','Mohamed','Galen','Jared','Scott','Kenneth','Conner',
                       'Yuki','Suguru','Hiroto','Bashir','Mo','Sondre','Kibrom','Lemi',
                       'Cam','Brett','Stephen','Lucas','Carlos','Ayele']
        last_names = ['Kipchoge','Kiptum','Mutai','Kipsang','Cherono','Legese','Tola','Desisa',
                      'Geremew','Lemma','Farah','Rupp','Ward','Fauble','Bekele','Hassan',
                      'Korir','Cherop','Bett','Abdi','Stanley','Moen','Kandie','Hailu',
                      'Levins','Robinson','Sambu','Rotich','Lopes','Adero']
    else:
        floor = 7800
        abilities = floor + RNG.lognormal(mean=5.7, sigma=0.55, size=n)
        abilities = np.clip(abilities, floor, 9600)
        first_names = ['Brigid','Ruth','Tigist','Almaz','Letesenbet','Sifan','Joyciline','Vivian',
                       'Mary','Peres','Hellen','Edna','Florence','Lonah','Eunice','Lonnie',
                       'Aliphine','Sara','Molly','Emily','Keira','Sinead','Roza','Yalemzerf',
                       'Catherine','Lilian','Worknesh','Sutume','Hiwot','Tirunesh']
        last_names = ['Kosgei','Chepngetich','Assefa','Ayana','Gidey','Hassan','Jepkosgei','Cheruiyot',
                      'Keitany','Jepchirchir','Obiri','Kiplagat','Kiplagat','Salpeter','Chepkirui','Frey',
                      'Tuliamuk','Hall','Seidel','Sisson','DAmato','Diver','Dereje','Yehualaw',
                      'Ndereba','Reichmann','Degefa','Asefa','Gemechu','Dibaba']

    pool = []
    for i in range(n):
        fn = first_names[RNG.integers(0, len(first_names))]
        ln = last_names[RNG.integers(0, len(last_names))]
        # Ensure unique by appending an index suffix for duplicates
        name = f"{fn} {ln} #{i:04d}"
        country = COUNTRIES_M[RNG.integers(0, len(COUNTRIES_M))] if gender == 'M' else \
                  COUNTRIES_W[RNG.integers(0, len(COUNTRIES_W))]
        pool.append({
            'name': name,
            'country': country,
            'gender': gender,
            'ability': abilities[i],
        })
    # Sort by ability (best first) — useful for tier-weighted sampling
    pool.sort(key=lambda a: a['ability'])
    return pool


def write_majors_results(weather_df):
    """For each (course, year), simulate a 100-deep elite field per gender."""
    pool_m = make_athlete_pool('M', 400)
    pool_w = make_athlete_pool('W', 400)
    pools = {'M': pool_m, 'W': pool_w}

    # For each course-year-gender, draw ~150 starters with bias toward better ability,
    # add penalties, sort, keep top 100.
    rows = []

    # Precompute weather penalties
    w_pen = {}
    for _, r in weather_df.iterrows():
        w_pen[(r['course'], r['year'])] = weather_penalty(
            r['start_temp_c'], r['start_humidity'], r['start_wind_kph']
        )

    for course in COURSES:
        for year in YEARS:
            for gender in ['M', 'W']:
                pool = pools[gender]
                # Tier weights: prob(athlete i) decays with index (ability rank)
                weights = np.exp(-np.arange(len(pool)) / 80.0)
                weights /= weights.sum()
                # 150 starters
                idx = RNG.choice(len(pool), size=150, replace=False, p=weights)
                athletes = [pool[i] for i in idx]

                penalty_course = COURSE_PENALTY[course]
                wpen = w_pen[(course, year)]

                race_rows = []
                for a in athletes:
                    base = a['ability'] + penalty_course
                    weather_adj = base * wpen
                    # Race noise: tactical / fueling / day variance
                    noise = RNG.normal(0, 90)  # seconds
                    finish_time = base + weather_adj + noise
                    race_rows.append({
                        'athlete_name': a['name'],
                        'country': a['country'],
                        'gender': gender,
                        'course': course,
                        'year': year,
                        'date': RACE_DATES[course][year],
                        'finish_time_seconds': int(round(finish_time)),
                    })
                race_rows.sort(key=lambda r: r['finish_time_seconds'])
                for place, rr in enumerate(race_rows[:100], start=1):
                    rr['place'] = place
                    rows.append(rr)

    df = pd.DataFrame(rows)
    df = df[['athlete_name', 'country', 'gender', 'course', 'year', 'date', 'place', 'finish_time_seconds']]
    df = df.sort_values(['course', 'year', 'gender', 'place']).reset_index(drop=True)
    df.to_csv(os.path.join(DATA_DIR, 'majors_results.csv'), index=False)
    print(f"  ✓ majors_results.csv ({len(df)} rows)")
    return df


def write_paired_runners(results_df):
    """Find athletes who ran >=2 different Majors within 18 months; emit course-pair deltas."""
    df = results_df.copy()
    df['date'] = pd.to_datetime(df['date'])

    pairs = []
    # Group by athlete
    for (name, gender), grp in df.groupby(['athlete_name', 'gender']):
        if grp['course'].nunique() < 2:
            continue
        races = grp.sort_values('date').to_dict('records')
        for i in range(len(races)):
            for j in range(i + 1, len(races)):
                a, b = races[i], races[j]
                if a['course'] == b['course']:
                    continue
                months = (b['date'] - a['date']).days / 30.44
                if months > 18:
                    continue
                pairs.append({
                    'athlete_name': name,
                    'gender': gender,
                    'course_a': a['course'], 'year_a': a['year'], 'time_a': a['finish_time_seconds'],
                    'course_b': b['course'], 'year_b': b['year'], 'time_b': b['finish_time_seconds'],
                    'delta_seconds': b['finish_time_seconds'] - a['finish_time_seconds'],
                    'months_between': round(months, 2),
                })

    pdf = pd.DataFrame(pairs)
    pdf.to_csv(os.path.join(DATA_DIR, 'paired_runners.csv'), index=False)
    print(f"  ✓ paired_runners.csv ({len(pdf)} rows)")
    return pdf


def main():
    print("Building data CSVs (deterministic, seed=42)...")
    weather_df = write_weather()
    results_df = write_majors_results(weather_df)
    write_paired_runners(results_df)
    print("Done.")


if __name__ == '__main__':
    main()
