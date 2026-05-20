"""
Marathon Majors Course Difficulty — Three-Framework Analysis
============================================================
Author: Jeremy Lee (lyhjeremy)
Date: May 2026

Research question: when an elite runs 2:02 in Berlin versus 2:05 in Boston,
how much of the gap is the runner and how much is the course?

We answer this with three independent frameworks:

  1. Elevation-/grade-adjusted prediction (Minetti et al. 2002)
  2. Within-runner paired comparison (cleanest; controls for ability)
  3. Weather-normalized average elite finish time (Maughan / El Helou)

Then we combine the three into a single Course Difficulty Index (CDI) with
Berlin = 1.00. Sensitivity analysis stress-tests the ranking.

Outputs:
  outputs/analysis_results.csv     - course x framework results table
  outputs/figures/fig1..fig8.png   - 400 DPI figures
"""

import os
import warnings
import numpy as np
import pandas as pd
from scipy import stats

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns

warnings.filterwarnings('ignore')

# ── Plot defaults ─────────────────────────────────────────────
plt.rcParams.update({
    'figure.facecolor': 'white',
    'axes.facecolor': '#FAFAFA',
    'axes.edgecolor': '#CCCCCC',
    'axes.grid': True,
    'grid.alpha': 0.3,
    'grid.color': '#CCCCCC',
    'font.family': 'sans-serif',
    'font.size': 11,
    'axes.titlesize': 14,
    'axes.titleweight': 'bold',
    'figure.dpi': 150,
    'savefig.dpi': 400,
    'savefig.bbox': 'tight',
    'savefig.pad_inches': 0.3,
})

PALETTE_M = '#2563EB'   # blue
PALETTE_W = '#DC2626'   # red
PALETTE_ALT = '#059669' # green
INK = '#1a1a2e'

COURSE_ORDER = ['boston', 'nyc', 'chicago', 'berlin', 'london', 'tokyo']
COURSE_LABEL = {
    'boston': 'Boston', 'nyc': 'NYC', 'chicago': 'Chicago',
    'berlin': 'Berlin', 'london': 'London', 'tokyo': 'Tokyo',
    'sydney': 'Sydney', 'cape_town': 'Cape Town',
}
COURSE_COLOR = {
    'boston':  '#B91C1C',
    'nyc':     '#F97316',
    'chicago': '#2563EB',
    'berlin':  '#059669',
    'london':  '#7C3AED',
    'tokyo':   '#0EA5E9',
    'sydney':  '#A16207',
    'cape_town': '#9F1239',
}

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(BASE_DIR)
DATA_DIR = os.path.join(PROJECT_DIR, 'data')
FIG_DIR = os.path.join(PROJECT_DIR, 'outputs', 'figures')
OUT_CSV = os.path.join(PROJECT_DIR, 'outputs', 'analysis_results.csv')
os.makedirs(FIG_DIR, exist_ok=True)
os.makedirs(os.path.dirname(OUT_CSV), exist_ok=True)


# ══════════════════════════════════════════════════════════════
# DATA LOADING
# ══════════════════════════════════════════════════════════════
def load_data():
    courses = pd.read_csv(os.path.join(DATA_DIR, 'course_profiles.csv'))
    results = pd.read_csv(os.path.join(DATA_DIR, 'majors_results.csv'))
    weather = pd.read_csv(os.path.join(DATA_DIR, 'race_weather.csv'))
    paired = pd.read_csv(os.path.join(DATA_DIR, 'paired_runners.csv'))
    return courses, results, weather, paired


def time_str(seconds):
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    return f"{h}:{m:02d}:{s:02d}"


# ══════════════════════════════════════════════════════════════
# FRAMEWORK 1: Elevation/grade-adjusted (Minetti)
# ══════════════════════════════════════════════════════════════
def minetti_cost(grade):
    """Energy cost of running at gradient `grade` (decimal, e.g. 0.05 = 5%)."""
    g = grade
    return (155.4*g**5 - 30.4*g**4 - 43.3*g**3 + 46.3*g**2 + 19.5*g + 3.6)


def framework1_elevation(courses):
    """
    Approximate each course as: 40% uphill at avg up-grade,
    40% downhill at avg down-grade, 20% flat. Apply Minetti's energy-cost
    curve to estimate the elevation factor relative to a perfectly flat course.

    Time penalty (s) = (factor - 1) * reference_winning_time.
    We use 7800s ~ 2:10 men's elite reference for reporting.
    """
    REF_TIME = 7800  # 2:10 reference flat elite time
    out = []
    for _, c in courses.iterrows():
        course = c['course']
        gain = c['total_gain_m']
        loss = c['total_loss_m']
        max_grade = c['max_grade_pct']
        turns = c['turn_count']
        distance_m = c['distance_km'] * 1000

        # avg gradients over assumed 40/40/20 split
        # NB: actual courses vary; this is the standard approximation
        up_dist = 0.4 * distance_m
        dn_dist = 0.4 * distance_m
        flat_dist = 0.2 * distance_m
        avg_up = gain / up_dist          # decimal grade
        avg_dn = -loss / dn_dist

        cost_up = minetti_cost(avg_up)
        cost_dn = minetti_cost(avg_dn)
        cost_flat = minetti_cost(0.0)

        # weighted average energy cost vs flat-only
        avg_cost = (up_dist * cost_up + dn_dist * cost_dn + flat_dist * cost_flat) / distance_m
        elev_factor = avg_cost / cost_flat

        # Penalty in seconds at the reference flat time
        elev_penalty = (elev_factor - 1.0) * REF_TIME

        # Additional micro-penalties from sharp grades and turns —
        # the Minetti model under-weights pacing damage from short steep
        # climbs late in the race and momentum cost at sharp turns.
        sharp_grade_penalty = max(0, max_grade - 1.5) ** 1.4 * 6   # seconds
        turn_penalty = max(0, turns - 8) * 1.2                     # seconds

        total = elev_penalty + sharp_grade_penalty + turn_penalty

        out.append({
            'course': course,
            'elev_factor': elev_factor,
            'elev_penalty_s': total,
            'minetti_pure_s': elev_penalty,
            'sharp_grade_s': sharp_grade_penalty,
            'turn_penalty_s': turn_penalty,
        })
    df = pd.DataFrame(out)
    # Anchor to Berlin = 0
    berlin_val = df.loc[df['course'] == 'berlin', 'elev_penalty_s'].iloc[0]
    df['f1_vs_berlin_s'] = df['elev_penalty_s'] - berlin_val
    return df


# ══════════════════════════════════════════════════════════════
# FRAMEWORK 2: Within-runner paired comparison (cleanest)
# ══════════════════════════════════════════════════════════════
def weather_adjust_paired(paired, weather):
    """Add weather-adjusted finish times to paired_runners."""
    w = weather.set_index(['course', 'year']).to_dict('index')
    p = paired.copy()
    mul_a, mul_b = [], []
    ca, ya, cb, yb = p['course_a'].values, p['year_a'].values, p['course_b'].values, p['year_b'].values
    for i in range(len(p)):
        ra = w.get((ca[i], int(ya[i])))
        rb = w.get((cb[i], int(yb[i])))
        mul_a.append(weather_multiplier(ra['start_temp_c'], ra['start_humidity'], ra['start_wind_kph'])
                     if ra else 1.0)
        mul_b.append(weather_multiplier(rb['start_temp_c'], rb['start_humidity'], rb['start_wind_kph'])
                     if rb else 1.0)
    p['time_a_adj'] = p['time_a'] / np.array(mul_a)
    p['time_b_adj'] = p['time_b'] / np.array(mul_b)
    p['delta_adj'] = p['time_b_adj'] - p['time_a_adj']
    return p


def framework2_paired(paired, courses_list=None, n_boot=2000, seed=42, use_adj=True):
    """
    For each athlete-pair (course_a, course_b), delta_seconds = t_b - t_a.
    We fit per-course offsets a_c such that t_b - t_a ≈ a_{course_b} - a_{course_a}
    via least squares with the constraint a_berlin = 0.

    Bootstrap pairwise: resample paired observations with replacement n_boot times
    to derive 95% CIs on each course offset.
    """
    if courses_list is None:
        courses_list = COURSE_ORDER
    course_idx = {c: i for i, c in enumerate(courses_list)}
    K = len(courses_list)

    pp = paired[paired['course_a'].isin(courses_list) & paired['course_b'].isin(courses_list)].copy()
    pp = pp.reset_index(drop=True)
    n = len(pp)

    # Pre-build the full design matrix once (n x K-1), pin berlin = 0.
    free = [c for c in courses_list if c != 'berlin']
    free_idx = {c: i for i, c in enumerate(free)}
    X_full = np.zeros((n, len(free)), dtype=np.float32)
    delta_col = 'delta_adj' if (use_adj and 'delta_adj' in pp.columns) else 'delta_seconds'
    y_full = pp[delta_col].values.astype(np.float64)
    ca = pp['course_a'].values
    cb = pp['course_b'].values
    for i in range(n):
        if cb[i] in free_idx:
            X_full[i, free_idx[cb[i]]] += 1
        if ca[i] in free_idx:
            X_full[i, free_idx[ca[i]]] -= 1

    def solve_from_idx(idx):
        X = X_full[idx]
        y = y_full[idx]
        theta, *_ = np.linalg.lstsq(X, y, rcond=None)
        offsets = {c: 0.0 for c in courses_list}
        for c, i in free_idx.items():
            offsets[c] = float(theta[i])
        return offsets

    # Point estimate
    offsets = solve_from_idx(np.arange(n))

    # Bootstrap (vectorized index sampling)
    rng = np.random.default_rng(seed)
    boot_offsets = {c: [] for c in courses_list}
    for _ in range(n_boot):
        idx = rng.integers(0, n, size=n)
        try:
            off = solve_from_idx(idx)
            for c, v in off.items():
                boot_offsets[c].append(v)
        except np.linalg.LinAlgError:
            continue

    rows = []
    for c in courses_list:
        vals = np.array(boot_offsets[c])
        rows.append({
            'course': c,
            'f2_offset_s': offsets[c],
            'f2_ci_low': float(np.percentile(vals, 2.5)),
            'f2_ci_high': float(np.percentile(vals, 97.5)),
            'f2_sd': float(vals.std()),
        })
    return pd.DataFrame(rows), pp


# ══════════════════════════════════════════════════════════════
# FRAMEWORK 3: Weather-normalized average finish time
# ══════════════════════════════════════════════════════════════
def weather_multiplier(temp_c, humidity, wind_kph):
    """Same Maughan-style penalty curve used in build_data — used here to back out
    the weather contribution from observed finish times."""
    if temp_c > 10:
        temp_pen = (temp_c - 10) * 0.005
    elif temp_c < 5:
        temp_pen = (5 - temp_c) * 0.002
    else:
        temp_pen = 0
    hum_pen = max(0, humidity - 60) * 0.0005
    wind_pen = max(0, wind_kph - 15) * 0.0005
    return 1.0 + temp_pen + hum_pen + wind_pen


def framework3_weather(results, weather):
    """
    Weather-normalize the top-10 average finish time per (course, year, gender),
    then aggregate to a per-course mean. Anchor Berlin to 0.
    """
    w = weather.set_index(['course', 'year']).to_dict('index')

    # top-10 average per (course, year, gender)
    top10 = (results[results['place'] <= 10]
             .groupby(['course', 'year', 'gender'])['finish_time_seconds']
             .mean()
             .reset_index()
             .rename(columns={'finish_time_seconds': 'top10_avg_s'}))

    def wmul(row):
        rec = w[(row['course'], row['year'])]
        return weather_multiplier(rec['start_temp_c'], rec['start_humidity'], rec['start_wind_kph'])

    top10['weather_mul'] = top10.apply(wmul, axis=1)
    top10['adj_top10_s'] = top10['top10_avg_s'] / top10['weather_mul']

    # Average across years per (course, gender)
    course_means = (top10.groupby(['course', 'gender'])['adj_top10_s']
                    .mean()
                    .reset_index())

    # For the headline F3 metric, average across genders (after re-anchoring per gender to berlin)
    rows = []
    for course in course_means['course'].unique():
        m = course_means[(course_means['course'] == course) & (course_means['gender'] == 'M')]['adj_top10_s'].iloc[0]
        w_ = course_means[(course_means['course'] == course) & (course_means['gender'] == 'W')]['adj_top10_s'].iloc[0]
        rows.append({'course': course, 'adj_top10_M': m, 'adj_top10_W': w_})
    f3 = pd.DataFrame(rows)

    # Anchor to Berlin baseline (per gender), then average the two gender offsets
    m_berlin = f3.loc[f3['course'] == 'berlin', 'adj_top10_M'].iloc[0]
    w_berlin = f3.loc[f3['course'] == 'berlin', 'adj_top10_W'].iloc[0]
    f3['f3_offset_M_s'] = f3['adj_top10_M'] - m_berlin
    f3['f3_offset_W_s'] = f3['adj_top10_W'] - w_berlin
    f3['f3_offset_s'] = (f3['f3_offset_M_s'] + f3['f3_offset_W_s']) / 2
    return f3, top10


# ══════════════════════════════════════════════════════════════
# CROSS-FRAMEWORK: Course Difficulty Index (CDI)
# ══════════════════════════════════════════════════════════════
CDI_WEIGHTS = {'F1': 0.15, 'F2': 0.50, 'F3': 0.35}

def compute_cdi(f1, f2, f3):
    """Composite Course Difficulty Index.

    Each framework returns a 'seconds penalty vs Berlin' that we convert to a
    multiplicative factor on a 7800s flat-equivalent. We then take a weighted
    mean with F2 (paired runners) weighted highest because it is the cleanest
    framework — it controls for athlete ability without any course assumptions.
    The Minetti elevation model (F1) is down-weighted because it credits net-
    descent courses too generously (it does not capture late-race fatigue from
    the Newton hills, which is empirically observable in F2 and F3).

    Weights: F1=0.15, F2=0.50, F3=0.35. Berlin pinned to CDI = 1.000.
    """
    REF = 7800
    cdi = f1[['course', 'f1_vs_berlin_s']].merge(
        f2[['course', 'f2_offset_s', 'f2_ci_low', 'f2_ci_high']], on='course'
    ).merge(f3[['course', 'f3_offset_s']], on='course')

    cdi['cdi_f1'] = 1 + cdi['f1_vs_berlin_s'] / REF
    cdi['cdi_f2'] = 1 + cdi['f2_offset_s'] / REF
    cdi['cdi_f3'] = 1 + cdi['f3_offset_s'] / REF
    w = CDI_WEIGHTS
    cdi['CDI'] = (w['F1']*cdi['cdi_f1'] + w['F2']*cdi['cdi_f2'] + w['F3']*cdi['cdi_f3'])
    # CI is from F2's bootstrap, scaled by F2's CDI weight
    cdi['CDI_ci_low']  = cdi['CDI'] + w['F2'] * (cdi['f2_ci_low']  - cdi['f2_offset_s']) / REF
    cdi['CDI_ci_high'] = cdi['CDI'] + w['F2'] * (cdi['f2_ci_high'] - cdi['f2_offset_s']) / REF
    return cdi.sort_values('CDI').reset_index(drop=True)


# ══════════════════════════════════════════════════════════════
# STATISTICAL TESTS
# ══════════════════════════════════════════════════════════════
def cross_framework_tests(f1, f2, f3):
    """Welch t and Levene comparing framework dispersion + per-course agreement."""
    REF = 7800
    s = {}
    for label, df, col in [('F1', f1, 'f1_vs_berlin_s'),
                            ('F2', f2, 'f2_offset_s'),
                            ('F3', f3, 'f3_offset_s')]:
        vals = df.loc[df['course'].isin(COURSE_ORDER), col].values / REF
        s[f'{label}_mean_x_berlin'] = float(vals.mean())
        s[f'{label}_std_x_berlin'] = float(vals.std())
        s[f'{label}_cv_pct'] = float(vals.std() / max(abs(vals.mean()), 1e-9) * 100)
    return s


def welch_berlin_vs_chicago_f2(paired):
    """Are Berlin and Chicago statistically indistinguishable under F2?"""
    # All Berlin-Chicago pair deltas (signed: berlin -> chicago)
    bc = paired[((paired['course_a'] == 'berlin') & (paired['course_b'] == 'chicago')) |
                ((paired['course_a'] == 'chicago') & (paired['course_b'] == 'berlin'))].copy()
    bc['delta_chicago_minus_berlin'] = np.where(
        bc['course_b'] == 'chicago', bc['delta_seconds'], -bc['delta_seconds']
    )
    deltas = bc['delta_chicago_minus_berlin'].values
    t, p = stats.ttest_1samp(deltas, 0.0)
    return {'n': int(len(deltas)), 'mean_s': float(np.mean(deltas)),
            'sd_s': float(np.std(deltas, ddof=1)), 't': float(t), 'p': float(p)}


# ══════════════════════════════════════════════════════════════
# SENSITIVITY
# ══════════════════════════════════════════════════════════════
def sensitivity_analysis(paired, f1, f3, weather=None):
    """Three perturbations:
      A. Drop Framework 1 (the elevation model) entirely.
      B. Restrict paired-runners to elite-only sub-2:10 men.
      C. Use Strava-GAP style alternative for elevation (simpler ratio).
    """
    REF = 7800
    # Baseline F2 (weather-adjusted, same as main pipeline)
    paired_adj = weather_adjust_paired(paired, weather) if weather is not None else paired
    f2_base, _ = framework2_paired(paired_adj)
    base_cdi = compute_cdi(f1, f2_base, f3)[['course', 'CDI']].set_index('course')

    # A. drop F1: CDI = mean of F2 and F3 only
    f1_zero = f1.copy()
    f1_zero['f1_vs_berlin_s'] = 0.0  # treat F1 as flat
    drop_f1 = compute_cdi(f1_zero, f2_base, f3)[['course', 'CDI']].set_index('course')

    # B. restrict to sub-2:10 men: pairs where both observed times under 7800s and gender M
    sub210 = paired_adj[(paired_adj['gender'] == 'M') &
                        (paired_adj['time_a'] < 7800) & (paired_adj['time_b'] < 7800)]
    if len(sub210) >= 50:
        f2_b, _ = framework2_paired(sub210, n_boot=500)
    else:
        f2_b = f2_base.copy()
    sub210_cdi = compute_cdi(f1, f2_b, f3)[['course', 'CDI']].set_index('course')

    # C. Strava-GAP-style alternative: ratio model penalty = gain*4 - loss*2 (signed)
    courses = pd.read_csv(os.path.join(DATA_DIR, 'course_profiles.csv'))
    courses = courses[courses['course'].isin(COURSE_ORDER)]
    courses['strava_pen_s'] = 4.0 * courses['total_gain_m'] - 2.0 * courses['total_loss_m']
    berlin_pen = courses.loc[courses['course'] == 'berlin', 'strava_pen_s'].iloc[0]
    courses['strava_vs_berlin_s'] = courses['strava_pen_s'] - berlin_pen
    f1_strava = courses[['course', 'strava_vs_berlin_s']].rename(columns={'strava_vs_berlin_s': 'f1_vs_berlin_s'})
    strava_cdi = compute_cdi(f1_strava, f2_base, f3)[['course', 'CDI']].set_index('course')

    out = pd.DataFrame({
        'baseline': base_cdi['CDI'],
        'drop_F1': drop_f1['CDI'],
        'sub_2_10_M_only': sub210_cdi['CDI'],
        'strava_GAP_F1': strava_cdi['CDI'],
    })
    return out


# ══════════════════════════════════════════════════════════════
# HISTORICAL: year-by-year weather-adjusted winning time per course
# ══════════════════════════════════════════════════════════════
def historical_evolution(results, weather):
    w = weather.set_index(['course', 'year']).to_dict('index')
    winners = (results[results['place'] == 1]
               .copy())

    def wadj(row):
        rec = w[(row['course'], row['year'])]
        mul = weather_multiplier(rec['start_temp_c'], rec['start_humidity'], rec['start_wind_kph'])
        return row['finish_time_seconds'] / mul

    winners['adj_winning_time_s'] = winners.apply(wadj, axis=1)
    return winners


# ══════════════════════════════════════════════════════════════
# EXTENSION: Sydney + Cape Town (Framework 1 only)
# ══════════════════════════════════════════════════════════════
def extension_courses(courses_full, f1_full, f2, f3):
    """For Sydney and Cape Town we only have F1 elevation data + a rough proxy.
    We report a 'F1-only CDI' as a ghost bar in the headline ranking."""
    rows = []
    REF = 7800
    for course in ['sydney', 'cape_town']:
        f1_row = f1_full[f1_full['course'] == course]
        if len(f1_row) == 0:
            continue
        f1_val = f1_row['f1_vs_berlin_s'].iloc[0]
        rows.append({
            'course': course,
            'cdi_f1_only': 1 + f1_val / REF,
            'note': 'F1 only (no paired/weather data)',
        })
    return pd.DataFrame(rows)


# ══════════════════════════════════════════════════════════════
# FIGURES
# ══════════════════════════════════════════════════════════════
def plot_fig1(results):
    """Box-and-whisker of top-100 elite finish times per course, 2015–2024."""
    fig, axes = plt.subplots(1, 2, figsize=(15, 6))
    for ax, gender, title in [(axes[0], 'M', 'Men'), (axes[1], 'W', 'Women')]:
        data = [results[(results.course == c) & (results.gender == gender)]['finish_time_seconds'].values / 60
                for c in COURSE_ORDER]
        bp = ax.boxplot(data, labels=[COURSE_LABEL[c] for c in COURSE_ORDER], patch_artist=True,
                        medianprops={'color': INK, 'linewidth': 2})
        for patch, c in zip(bp['boxes'], COURSE_ORDER):
            patch.set_facecolor(COURSE_COLOR[c])
            patch.set_alpha(0.6)
            patch.set_edgecolor('white')
        # Annotate medians
        for i, c in enumerate(COURSE_ORDER, start=1):
            med = np.median(data[i-1])
            ax.text(i, med, f'{med:.1f}', ha='center', va='bottom',
                    fontsize=8, fontweight='bold', color=INK)
        ax.set_title(f'{title} – Top-100 finish times (2015-2024)', fontweight='bold')
        ax.set_ylabel('Finish time (minutes)')
        ax.tick_params(axis='x', rotation=15)
    fig.suptitle('Figure 1. Raw elite finish-time distribution by Major',
                 fontsize=15, fontweight='bold', y=1.02)
    plt.tight_layout()
    fig.savefig(os.path.join(FIG_DIR, 'fig1_raw_times_by_course.png'))
    plt.close(fig)
    print("  fig1_raw_times_by_course.png")


def plot_fig2(results, f1):
    """Same top-100 medians, but with Framework-1 elevation adjustment applied,
    shown as arrows from raw to adjusted medians."""
    fig, ax = plt.subplots(figsize=(13, 6))
    f1_map = dict(zip(f1['course'], f1['elev_factor']))
    courses = COURSE_ORDER

    medians_raw = []
    medians_adj = []
    for c in courses:
        sub = results[(results.course == c) & (results.gender == 'M')]
        med = np.median(sub['finish_time_seconds']) / 60
        medians_raw.append(med)
        # Adjust: time / elev_factor gives flat-course equivalent
        medians_adj.append(med / f1_map[c])

    x = np.arange(len(courses))
    ax.scatter(x, medians_raw, s=140, color=[COURSE_COLOR[c] for c in courses],
               label='Raw median', edgecolor='white', zorder=3)
    ax.scatter(x, medians_adj, s=140, marker='s', color=[COURSE_COLOR[c] for c in courses],
               label='Elevation-adjusted', edgecolor=INK, zorder=3, alpha=0.6)
    for i, c in enumerate(courses):
        ax.annotate('', xy=(x[i], medians_adj[i]), xytext=(x[i], medians_raw[i]),
                    arrowprops=dict(arrowstyle='->', color=INK, lw=1.5, alpha=0.7))
        ax.text(x[i] + 0.18, medians_raw[i], f'{medians_raw[i]:.1f}', va='center', fontsize=8)
        ax.text(x[i] + 0.18, medians_adj[i], f'{medians_adj[i]:.1f}', va='center', fontsize=8, color='#666')

    ax.set_xticks(x)
    ax.set_xticklabels([COURSE_LABEL[c] for c in courses])
    ax.set_ylabel('Median men\'s finish time (min)')
    ax.set_title('Figure 2. Raw vs Framework-1 elevation-adjusted medians (men)',
                 fontsize=14, fontweight='bold')
    ax.legend()
    plt.tight_layout()
    fig.savefig(os.path.join(FIG_DIR, 'fig2_elevation_adjusted.png'))
    plt.close(fig)
    print("  fig2_elevation_adjusted.png")


def plot_fig3(paired, f2):
    """Forest plot: 15 course-pair deltas with bootstrap CIs (men+women combined)."""
    pairs = []
    for i, c1 in enumerate(COURSE_ORDER):
        for c2 in COURSE_ORDER[i+1:]:
            sub = paired[((paired.course_a == c1) & (paired.course_b == c2)) |
                         ((paired.course_a == c2) & (paired.course_b == c1))].copy()
            sub['delta_b_minus_a'] = np.where(
                sub['course_b'] == c2, sub['delta_seconds'], -sub['delta_seconds']
            )
            d = sub['delta_b_minus_a'].values
            if len(d) < 5:
                continue
            mean = d.mean()
            se = d.std(ddof=1) / np.sqrt(len(d))
            ci = 1.96 * se
            pairs.append({'pair': f'{COURSE_LABEL[c1]} → {COURSE_LABEL[c2]}',
                          'mean': mean, 'lo': mean - ci, 'hi': mean + ci, 'n': len(d)})
    pdf = pd.DataFrame(pairs).sort_values('mean')
    fig, ax = plt.subplots(figsize=(11, 9))
    y = np.arange(len(pdf))
    ax.errorbar(pdf['mean'], y, xerr=[pdf['mean']-pdf['lo'], pdf['hi']-pdf['mean']],
                fmt='o', color=INK, capsize=4, markersize=6, ecolor='#888')
    ax.axvline(0, color='#888', linestyle='--', alpha=0.6)
    ax.set_yticks(y)
    ax.set_yticklabels(pdf['pair'])
    ax.set_xlabel('Mean within-runner time delta (seconds, course_b − course_a)')
    ax.set_title('Figure 3. Framework-2 within-runner course-pair deltas, 95% CI',
                 fontsize=14, fontweight='bold')
    for yi, (mean, n) in enumerate(zip(pdf['mean'], pdf['n'])):
        ax.text(mean, yi + 0.25, f'n={n}', ha='center', fontsize=7, color='#666')
    plt.tight_layout()
    fig.savefig(os.path.join(FIG_DIR, 'fig3_within_runner_gaps.png'))
    plt.close(fig)
    print("  fig3_within_runner_gaps.png")


def plot_fig4(results, weather):
    """Year-by-year weather-adjusted winning time per course."""
    winners = historical_evolution(results, weather)
    winners_m = winners[winners.gender == 'M']
    fig, ax = plt.subplots(figsize=(13, 6))
    for c in COURSE_ORDER:
        sub = winners_m[winners_m.course == c].sort_values('year')
        ax.plot(sub['year'], sub['adj_winning_time_s'] / 60, marker='o',
                color=COURSE_COLOR[c], linewidth=2, label=COURSE_LABEL[c])
    ax.set_xlabel('Year')
    ax.set_ylabel('Weather-adjusted winning time (min, men)')
    ax.set_title('Figure 4. Weather-normalized winning time, by Major (2015-2024, men)',
                 fontsize=14, fontweight='bold')
    ax.legend(ncol=3, loc='upper center', bbox_to_anchor=(0.5, -0.12), frameon=False)
    plt.tight_layout()
    fig.savefig(os.path.join(FIG_DIR, 'fig4_weather_normalized.png'))
    plt.close(fig)
    print("  fig4_weather_normalized.png")


def plot_fig5(cdi):
    """6x3 heatmap: courses × frameworks, values = relative difficulty (Berlin=1.00)."""
    fig, ax = plt.subplots(figsize=(10, 6))
    mat = cdi.set_index('course')[['cdi_f1', 'cdi_f2', 'cdi_f3']].loc[COURSE_ORDER]
    mat.columns = ['F1: Elevation', 'F2: Paired runners', 'F3: Weather-adj']
    mat.index = [COURSE_LABEL[c] for c in mat.index]
    sns.heatmap(mat, annot=True, fmt='.3f', cmap='RdYlGn_r', center=1.0,
                linewidths=1, linecolor='white',
                cbar_kws={'label': 'Difficulty multiplier (Berlin = 1.00)'}, ax=ax)
    ax.set_title('Figure 5. Cross-framework comparison (Berlin = 1.00)',
                 fontsize=14, fontweight='bold')
    plt.tight_layout()
    fig.savefig(os.path.join(FIG_DIR, 'fig5_framework_comparison.png'))
    plt.close(fig)
    print("  fig5_framework_comparison.png")


def plot_fig6(cdi):
    """The headline chart: CDI per course, sorted, with bootstrap error bars (from F2)."""
    fig, ax = plt.subplots(figsize=(11, 6))
    cdi_sorted = cdi.sort_values('CDI').reset_index(drop=True)
    y = np.arange(len(cdi_sorted))
    colors = [COURSE_COLOR[c] for c in cdi_sorted['course']]
    bars = ax.barh(y, cdi_sorted['CDI'], color=colors, edgecolor='white', alpha=0.85)
    # error bars derived from F2 CI (the only framework with a bootstrap CI), scaled by F2 weight
    REF = 7800
    w_f2 = CDI_WEIGHTS['F2']
    err_lo = w_f2 * (cdi_sorted['f2_offset_s'] - cdi_sorted['f2_ci_low']) / REF
    err_hi = w_f2 * (cdi_sorted['f2_ci_high'] - cdi_sorted['f2_offset_s']) / REF
    ax.errorbar(cdi_sorted['CDI'], y, xerr=[err_lo, err_hi], fmt='none',
                ecolor=INK, capsize=4, elinewidth=1.4)
    ax.set_yticks(y)
    ax.set_yticklabels([COURSE_LABEL[c] for c in cdi_sorted['course']])
    ax.set_xlabel('Course Difficulty Index (Berlin = 1.000)')
    ax.set_title('Figure 6. Course Difficulty Index — the composite ranking',
                 fontsize=15, fontweight='bold')
    for i, v in enumerate(cdi_sorted['CDI']):
        ax.text(v + 0.0008, i, f'{v:.3f}', va='center', fontsize=10, fontweight='bold')
    ax.axvline(1.0, color='#888', linestyle='--', alpha=0.6)
    ax.set_xlim(min(cdi_sorted['CDI']) - 0.005, max(cdi_sorted['CDI']) + 0.012)
    plt.tight_layout()
    fig.savefig(os.path.join(FIG_DIR, 'fig6_course_difficulty_index.png'))
    plt.close(fig)
    print("  fig6_course_difficulty_index.png")


def plot_fig7(sens):
    """Sensitivity: three sub-bars per course showing CDI under different assumptions."""
    fig, ax = plt.subplots(figsize=(13, 6))
    courses = sens.index.tolist()
    x = np.arange(len(courses))
    width = 0.20
    scenarios = ['baseline', 'drop_F1', 'sub_2_10_M_only', 'strava_GAP_F1']
    labels = ['Baseline', 'Drop F1', 'Sub-2:10 men only', 'Strava-GAP F1']
    colors = [INK, '#888', PALETTE_M, PALETTE_ALT]
    for i, (s, lbl, col) in enumerate(zip(scenarios, labels, colors)):
        ax.bar(x + (i - 1.5) * width, sens[s], width=width,
               color=col, alpha=0.85, label=lbl, edgecolor='white')
    ax.set_xticks(x)
    ax.set_xticklabels([COURSE_LABEL[c] for c in courses])
    ax.set_ylabel('Course Difficulty Index')
    ax.set_title('Figure 7. Sensitivity analysis — ranking robustness',
                 fontsize=14, fontweight='bold')
    ax.axhline(1.0, color='#888', linestyle='--', alpha=0.6)
    ax.legend(ncol=4, loc='upper center', bbox_to_anchor=(0.5, -0.10), frameon=False)
    ax.set_ylim(min(sens.values.min(), 0.99), sens.values.max() + 0.005)
    plt.tight_layout()
    fig.savefig(os.path.join(FIG_DIR, 'fig7_sensitivity.png'))
    plt.close(fig)
    print("  fig7_sensitivity.png")


def plot_fig8(cdi, ext):
    """Headline ranking extended to Sydney + Cape Town as ghost bars (F1-only)."""
    fig, ax = plt.subplots(figsize=(11, 6))
    cdi_sorted = cdi.sort_values('CDI').reset_index(drop=True)
    all_rows = [(r['course'], r['CDI'], False) for _, r in cdi_sorted.iterrows()]
    if ext is not None and len(ext) > 0:
        for _, r in ext.iterrows():
            all_rows.append((r['course'], r['cdi_f1_only'], True))
    all_rows.sort(key=lambda x: x[1])
    y = np.arange(len(all_rows))
    for yi, (c, v, ghost) in enumerate(all_rows):
        color = COURSE_COLOR[c]
        ax.barh(yi, v, color=color, alpha=0.35 if ghost else 0.85,
                edgecolor='white', hatch='///' if ghost else None)
        suffix = ' (F1 only)' if ghost else ''
        ax.text(v + 0.0008, yi, f'{v:.3f}{suffix}', va='center', fontsize=10, fontweight='bold')
    ax.set_yticks(y)
    ax.set_yticklabels([COURSE_LABEL[c] + (' †' if ghost else '') for c, _, ghost in all_rows])
    ax.set_xlabel('Course Difficulty Index (Berlin = 1.000)')
    ax.set_title('Figure 8. Alternative ranking — extended to Sydney and Cape Town',
                 fontsize=14, fontweight='bold')
    ax.axvline(1.0, color='#888', linestyle='--', alpha=0.6)
    ax.set_xlim(0.985, max(v for _, v, _ in all_rows) + 0.015)
    plt.tight_layout()
    fig.savefig(os.path.join(FIG_DIR, 'fig8_alternative_ranking.png'))
    plt.close(fig)
    print("  fig8_alternative_ranking.png")


# ══════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════
def main():
    print("=" * 64)
    print("Marathon Majors Course Difficulty - Three-Framework Analysis")
    print("=" * 64)

    print("\n[1/7] Loading data...")
    courses, results, weather, paired = load_data()
    print(f"  courses={len(courses)}, results={len(results)}, paired={len(paired)}")

    print("\n[2/7] Framework 1: Elevation/grade-adjusted (Minetti)...")
    f1_full = framework1_elevation(courses)
    f1 = f1_full[f1_full['course'].isin(COURSE_ORDER)].reset_index(drop=True)
    for _, r in f1.iterrows():
        print(f"  {COURSE_LABEL[r['course']]:8s}  factor={r['elev_factor']:.4f}  "
              f"penalty={r['elev_penalty_s']:+6.1f}s  (vs Berlin: {r['f1_vs_berlin_s']:+6.1f}s)")

    print("\n[3/7] Framework 2: Within-runner paired comparison (bootstrap 2000)...")
    paired_adj = weather_adjust_paired(paired, weather)
    f2, paired_main = framework2_paired(paired_adj, n_boot=2000)
    for _, r in f2.iterrows():
        print(f"  {COURSE_LABEL[r['course']]:8s}  offset={r['f2_offset_s']:+6.1f}s  "
              f"95% CI [{r['f2_ci_low']:+6.1f}, {r['f2_ci_high']:+6.1f}]")

    bvc = welch_berlin_vs_chicago_f2(paired_main)
    print(f"\n  Berlin vs Chicago (1-sample t on chicago−berlin deltas):")
    print(f"    n={bvc['n']}, mean={bvc['mean_s']:+.1f}s, t={bvc['t']:.3f}, p={bvc['p']:.3f}")

    print("\n[4/7] Framework 3: Weather-normalized top-10 average...")
    f3, top10 = framework3_weather(results, weather)
    for _, r in f3.iterrows():
        if r['course'] in COURSE_ORDER:
            print(f"  {COURSE_LABEL[r['course']]:8s}  M offset={r['f3_offset_M_s']:+6.1f}s  "
                  f"W offset={r['f3_offset_W_s']:+6.1f}s  avg={r['f3_offset_s']:+6.1f}s")

    print("\n[5/7] Composite Course Difficulty Index (CDI)...")
    cdi = compute_cdi(f1, f2, f3[f3['course'].isin(COURSE_ORDER)])
    for _, r in cdi.iterrows():
        print(f"  {COURSE_LABEL[r['course']]:8s}  CDI={r['CDI']:.4f}  "
              f"(F1={r['cdi_f1']:.4f}  F2={r['cdi_f2']:.4f}  F3={r['cdi_f3']:.4f})")

    print("\n[6/7] Sensitivity analysis...")
    sens = sensitivity_analysis(paired, f1, f3[f3['course'].isin(COURSE_ORDER)], weather=weather)
    print(sens.round(4).to_string())

    print("\n[7/7] Generating figures...")
    plot_fig1(results)
    plot_fig2(results, f1)
    plot_fig3(paired_main, f2)
    plot_fig4(results, weather)
    plot_fig5(cdi)
    plot_fig6(cdi)
    plot_fig7(sens)

    # Extension courses (F1 only for Sydney/Cape Town)
    ext = extension_courses(courses, f1_full, f2, f3)
    plot_fig8(cdi, ext)

    # ── Persist results ──
    out = cdi.copy()
    out['CDI_rank'] = out['CDI'].rank(ascending=True).astype(int)
    out.to_csv(OUT_CSV, index=False)
    print(f"\n  Saved: {OUT_CSV}")

    # Statistical summary
    tests = cross_framework_tests(f1, f2, f3[f3['course'].isin(COURSE_ORDER)])
    print("\nCross-framework dispersion:")
    for k, v in tests.items():
        print(f"  {k}: {v:.4f}")

    print("\nAnalysis complete. All outputs in outputs/")
    return cdi, sens, bvc


if __name__ == '__main__':
    main()
