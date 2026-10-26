"""Generate a self-contained HTML report (web/index.html) with embedded figures.

Styled with the road family of the Ledger standards: tokens from ../assets/family.css,
self-hosted fonts in ../fonts/. Reads outputs/figures/*.png and
outputs/analysis_results.csv; run src/analysis.py first if those are missing.
"""
import base64
import os
import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(BASE_DIR)
FIG_DIR = os.path.join(PROJECT_DIR, 'outputs', 'figures')
WEB_DIR = os.path.join(PROJECT_DIR, 'web')
os.makedirs(WEB_DIR, exist_ok=True)

COURSE_LABEL = {'boston': 'Boston', 'nyc': 'New York', 'chicago': 'Chicago',
                'berlin': 'Berlin', 'london': 'London', 'tokyo': 'Tokyo'}

# The penalties planted by src/build_data.py (COURSE_PENALTY), in seconds vs Berlin.
PLANTED = {'berlin': 0, 'chicago': 12, 'london': 35, 'tokyo': 28, 'nyc': 85, 'boston': 105}


def encode_fig(name):
    with open(os.path.join(FIG_DIR, name), 'rb') as f:
        return base64.b64encode(f.read()).decode()


fig1 = encode_fig('fig1_raw_times_by_course.png')
fig2 = encode_fig('fig2_elevation_adjusted.png')
fig3 = encode_fig('fig3_within_runner_gaps.png')
fig4 = encode_fig('fig4_weather_normalized.png')
fig5 = encode_fig('fig5_framework_comparison.png')
fig6 = encode_fig('fig6_course_difficulty_index.png')
fig7 = encode_fig('fig7_sensitivity.png')
fig8 = encode_fig('fig8_alternative_ranking.png')

results = pd.read_csv(os.path.join(PROJECT_DIR, 'outputs', 'analysis_results.csv'))
results = results.sort_values('CDI', ascending=False).reset_index(drop=True)


def signed(x):
    return f"{x:+.1f}".replace('-', '&minus;') if abs(x) >= 0.05 else "0"


def table_rows():
    out = []
    for rank, (_, r) in enumerate(results.iterrows(), start=1):
        secs = (r['CDI'] - 1) * 7800
        out.append(f"""
        <tr>
          <td class="rank">{rank}</td>
          <td class="course">{COURSE_LABEL.get(r['course'], r['course'])}</td>
          <td class="num planted">{PLANTED[r['course']]}</td>
          <td class="num">{signed(r['f1_vs_berlin_s'])}</td>
          <td class="num">{signed(r['f2_offset_s'])}</td>
          <td class="num">{signed(r['f3_offset_s'])}</td>
          <td class="num cdi">{r['CDI']:.4f}</td>
          <td class="num">{signed(secs)}</td>
        </tr>""")
    return ''.join(out)


trows = table_rows()

CSS = """
  * { box-sizing: border-box; border-radius: 0; }
  html, body { margin: 0; padding: 0; }
  body { background: var(--paper); color: var(--ink); font-family: var(--font-head);
         font-size: 18px; line-height: 1.7; border-top: 6px solid var(--signal-2); }
  a { color: var(--signal); }
  a:hover { color: var(--ink); }
  :focus-visible { outline: 2px solid var(--signal); outline-offset: 3px; }
  .bar-link { display: block; background: var(--ink); color: var(--paper); text-align: center;
              padding: 11px 18px; font: 600 14.5px/1.45 var(--font-body); text-decoration: none; }
  .bar-link:hover { color: var(--paper); background: var(--signal-2); }
  .container { width: min(100% - 2.4rem, 46rem); margin: 0 auto; padding: 0 0 80px; }
  .masthead { padding: 34px 0 26px; border-bottom: 2px solid var(--ink); margin-bottom: 30px; }
  .kicker { font-family: var(--font-mono); font-size: 12.5px; letter-spacing: .14em; text-transform: uppercase;
            color: var(--signal); margin: 0 0 12px; }
  h1 { font-family: var(--font-display); font-weight: 700; text-transform: uppercase; line-height: .98;
       font-size: clamp(36px, 6vw, 60px); margin: 0; }
  .byline { font-family: var(--font-body); font-size: 15px; color: var(--ink-2); margin: 16px 0 0; }
  h2 { font-family: var(--font-display); font-weight: 600; font-size: clamp(26px, 3.4vw, 34px);
       line-height: 1.05; margin: 54px 0 14px; padding-bottom: 8px; border-bottom: 1px solid var(--rule); }
  h3 { font-family: var(--font-display); font-weight: 600; font-size: 22px; text-transform: uppercase;
       letter-spacing: .02em; margin: 30px 0 8px; }
  p { margin: 0 0 18px; color: var(--ink-2); }
  strong { color: var(--ink); }
  code { font-family: var(--font-mono); font-size: .84em; }
  .formula { font-family: var(--font-mono); font-size: 15px; border: 1px solid var(--edge); background: var(--panel);
             padding: 12px 16px; margin: 22px 0; color: var(--ink); overflow-x: auto; }
  .figure { margin: 34px 0; }
  .figure img { display: block; max-width: 100%; height: auto; border: 1px solid var(--rule); background: var(--panel); padding: 10px; }
  .figure figcaption { font-family: var(--font-body); font-size: 14px; color: var(--ink-2); margin-top: 10px; }
  .tablewrap { overflow-x: auto; border: 1px solid var(--edge); background: var(--panel); margin: 24px 0; }
  table { width: 100%; min-width: 600px; border-collapse: collapse; font-family: var(--font-body); font-size: 15px; }
  th { font-family: var(--font-mono); font-size: 11px; letter-spacing: .1em; text-transform: uppercase;
       color: var(--ink-2); font-weight: 400; text-align: right; padding: 11px 10px; border-bottom: 2px solid var(--ink); }
  th:nth-child(-n+2) { text-align: left; }
  td { padding: 10px; border-bottom: 1px solid var(--rule); color: var(--ink-2); }
  tr:last-child td { border-bottom: 0; }
  td.num { text-align: right; font-family: var(--font-mono); font-variant-numeric: tabular-nums; }
  td.rank { font-family: var(--font-display); font-weight: 700; font-size: 20px; color: var(--ink); }
  td.course { font-family: var(--font-display); font-weight: 600; font-size: 19px; text-transform: uppercase; color: var(--ink); }
  td.planted { color: var(--signal); }
  td.cdi { color: var(--ink); }
  .stat-grid { display: grid; grid-template-columns: 1fr; margin: 30px 0; border-top: 2px solid var(--ink); }
  @media (min-width: 640px) { .stat-grid { grid-template-columns: 1fr 1fr; column-gap: 32px; } }
  .stat-box { padding: 14px 0 16px; border-bottom: 1px solid var(--rule); }
  .stat-big { font-family: var(--font-display); font-weight: 700; font-size: 46px; line-height: 1; color: var(--signal); }
  .stat-label { font-family: var(--font-body); font-size: 14.5px; color: var(--ink-2); margin-top: 6px; }
  .note { border: 1px solid var(--edge); padding: 16px 20px; margin: 28px 0; }
  .note p:last-child { margin-bottom: 0; }
  .footer { font-family: var(--font-body); font-size: 14px; color: var(--ink-2); margin-top: 64px;
            padding-top: 24px; border-top: 1px solid var(--rule); }
  .footer a { color: var(--ink-2); }
  @media (max-width: 600px) { body { font-size: 17px; } }
"""

HTML = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>Marathon Majors course difficulty: three methods tested on a simulated field</title>
<meta name="description" content="Three methods for ranking the six World Marathon Majors by difficulty, tested on a simulated elite field with a known penalty planted on each course." />
<meta name="theme-color" content="#ECEBE6" />
<link rel="stylesheet" href="../assets/family.css" />
<style>{CSS}</style>
</head>
<body>
<a class="bar-link" href="../overview/" data-overview-link>Read the full writeup&nbsp;&rarr;</a>

<main class="container">

  <header class="masthead">
    <p class="kicker">HTML report &middot; a method test on simulated data</p>
    <h1>Ranking the Marathon Majors by course difficulty</h1>
    <p class="byline">Jeremy Lee &middot; 2026 &middot; <a href="../">project page</a> &middot; <a href="https://github.com/lyhjeremy/marathon-majors-course-difficulty">code</a></p>
  </header>

  <p>How much time does a marathon course cost a runner compared with Berlin? With real results there is no true answer to check a method against, so this project builds one. <code>src/build_data.py</code> simulates a top-100 elite field for the six World Marathon Majors from 2015 to 2024 and adds a fixed penalty to every finish on each course: Berlin 0, Chicago 12, Tokyo 28, London 35, New York 85 and Boston 105 seconds. Three ranking methods then try to recover those numbers.</p>

  <p>The <strong>within-runner paired comparison</strong> recovers every planted penalty to within 7.3 seconds: Boston +101.0, New York +77.7, London +30.7, Tokyo +21.0, Chicago +11.4. The weather-normalized top-10 average is within 11.1 seconds. The grade-adjusted energy-cost model, which reads only the course elevation profiles, puts Boston 89 seconds faster than Berlin.</p>

  <div class="stat-grid">
    <div class="stat-box"><div class="stat-big">+101.0 s</div><div class="stat-label">Boston vs Berlin, paired method (planted: 105)</div></div>
    <div class="stat-box"><div class="stat-big">7.3 s</div><div class="stat-label">Largest paired miss, New York (77.7 vs 85)</div></div>
    <div class="stat-box"><div class="stat-big">&minus;89.4 s</div><div class="stat-label">Boston vs Berlin, Minetti elevation model</div></div>
    <div class="stat-box"><div class="stat-big">42,567</div><div class="stat-label">Same-athlete course pairs within 18 months</div></div>
  </div>

  <h2>1. The simulated field</h2>

  <p>The build script draws 400 men and 400 women with a fixed flat-course ability, sends 150 of each to every race (weighted toward the faster athletes), and gives each a finish time of ability plus course penalty plus a weather penalty plus normal noise with a 90-second standard deviation. The top 100 per gender are kept: 10,800 results over 54 editions, with 2020 left out. Race-day weather is a hand-entered table of temperature, humidity and wind per edition. Athlete names are combinations of real elite first and last names with a number attached; they are not real people's results.</p>

  <h2>2. The three methods</h2>

  <h3>Grade-adjusted (Minetti)</h3>
  <p>Integrates the Minetti et al. (2002) energy cost of running over each course, treated as 40% climbing at its average up-grade, 40% descending and 20% flat, plus small penalties for grades over 1.5% and for many turns. It uses no race results. Boston's 136 m net descent makes it score faster than flat.</p>

  <h3>Within-runner paired</h3>
  <p>For every athlete who ran two different Majors within 18 months, divide each time by its race's weather multiplier and take the difference. Least squares fits one offset per course with Berlin fixed at zero; 2,000 bootstrap resamples give 95% intervals of about &plusmn;2 seconds.</p>

  <h3>Weather-normalized top-10 average</h3>
  <p>Each edition's top-10 average per gender, divided by a heat, humidity and wind multiplier after Maughan (2010) and El Helou et al. (2012), averaged over years and anchored to Berlin.</p>

  <h2>3. What the methods found</h2>

  <figure class="figure">
    <img src="data:image/png;base64,{fig1}" alt="Box plots of simulated top-100 finish times per Major; Boston and New York sit highest, Berlin and Chicago lowest." />
    <figcaption>Figure 1. Simulated top-100 finish times per Major, 2015 to 2024, before any adjustment.</figcaption>
  </figure>

  <figure class="figure">
    <img src="data:image/png;base64,{fig3}" alt="Forest plot of mean same-athlete time differences for the 15 course pairs with bootstrap intervals; pairs involving Boston and New York show the largest gaps." />
    <figcaption>Figure 2. Mean same-athlete delta for each of the 15 course pairs, with 95% bootstrap intervals; 42,567 pairs.</figcaption>
  </figure>

  <p>The paired estimate is below the planted value on every course, by 0.6 s (Chicago) to 7.3 s (New York). Only Chicago's interval contains its planted value, so the shortfall is a bias in the method on this data. The code doesn't test where it comes from.</p>

  <figure class="figure">
    <img src="data:image/png;base64,{fig4}" alt="Lines of weather-adjusted men's winning time by year for each Major; Boston and New York sit above the other four." />
    <figcaption>Figure 3. Weather-adjusted men's winning time by Major and year.</figcaption>
  </figure>

  <h2>4. The composite index</h2>

  <p>Each method's offset becomes a factor on a 7,800-second (2:10) reference, and the three are weighted:</p>

  <div class="formula">CDI = 0.15 &times; grade-adjusted + 0.50 &times; paired + 0.35 &times; weather-normalized</div>

  <figure class="figure">
    <img src="data:image/png;base64,{fig6}" alt="Bar chart of the composite Course Difficulty Index, Berlin at 1.000 and Boston and New York both near 1.009." />
    <figcaption>Figure 4. Course Difficulty Index, Berlin = 1.000. Intervals from the paired bootstrap scaled by its 0.50 weight.</figcaption>
  </figure>

  <div class="tablewrap">
  <table>
    <thead>
      <tr><th>Rank</th><th>Course</th><th>Planted (s)</th><th>Grade-adj. (s)</th><th>Paired (s)</th><th>Top-10 (s)</th><th>CDI</th><th>CDI as s</th></tr>
    </thead>
    <tbody>{trows}</tbody>
  </table>
  </div>

  <p>The composite puts Boston (1.0092) barely ahead of New York (1.0089). The grade-adjusted method's negative Boston value pulls Boston's composite down to 72 seconds over Berlin, against 101 from the paired fit alone.</p>

  <figure class="figure">
    <img src="data:image/png;base64,{fig5}" alt="Heatmap of difficulty factors by course and method; Boston's grade-adjusted cell, 0.989, is the lowest on the chart while its other two cells are the highest." />
    <figcaption>Figure 5. Difficulty factor by course and method. Boston's grade-adjusted cell is the one that disagrees.</figcaption>
  </figure>

  <h2>5. Sensitivity</h2>

  <p>Three variations: drop the grade-adjusted method, restrict the paired fit to men's pairs with both times under 2:10, and replace Minetti with a simpler gain-and-loss elevation model. The first two keep the order. The third moves New York to 1.0166, above Boston at 1.0131.</p>

  <figure class="figure">
    <img src="data:image/png;base64,{fig7}" alt="Grouped bars of the index under four assumption sets; New York rises above Boston under the gain-and-loss elevation model." />
    <figcaption>Figure 6. The index under the baseline and three alternative assumptions.</figcaption>
  </figure>

  <h2>6. Sydney and Cape Town</h2>

  <p>The two extra courses have elevation profiles but no simulated results, so only the grade-adjusted method scores them.</p>

  <figure class="figure">
    <img src="data:image/png;base64,{fig8}" alt="Ranking extended to Sydney and Cape Town as hatched bars scored by the elevation model only." />
    <figcaption>Figure 7. Ranking extended to Sydney and Cape Town (hatched, grade-adjusted only).</figcaption>
  </figure>

  <h2>7. What this doesn't show</h2>

  <div class="note">
    <p>None of these numbers is a measurement of a real course. The test is also easier than real data: the weather correction uses the same curve that generated the times, and the simulation has no pacing strategy, no fatigue tied to where the hills fall, and no difference in who races where. The simulation has no elevation term, so the gap between the grade-adjusted column and the planted one says nothing about whether the Minetti model is right about the real Boston. Course profiles are hand-entered, and the 40/40/20 split is a rough stand-in for a segment-by-segment integration.</p>
  </div>

  <p>Code, data and the notebook are at <a href="https://github.com/lyhjeremy/marathon-majors-course-difficulty">github.com/lyhjeremy/marathon-majors-course-difficulty</a>. <code>python src/build_data.py</code> then <code>python src/analysis.py</code> reproduce every number here.</p>

  <div class="footer">
    MIT &copy; 2026 Jeremy Lee &middot;
    <a href="../">Project page</a> &middot;
    <a href="../overview/">Write-up</a> &middot;
    <a href="https://github.com/lyhjeremy/marathon-majors-course-difficulty">Repository</a> &middot;
    <a href="https://github.com/lyhjeremy/marathon-majors-course-difficulty/blob/main/notebooks/majors_course_difficulty_analysis.ipynb">Notebook</a>
  </div>

</main>
</body>
</html>
"""

out_path = os.path.join(WEB_DIR, 'index.html')
with open(out_path, 'w', encoding='utf-8') as f:
    f.write(HTML)
size_kb = os.path.getsize(out_path) / 1024
print(f"HTML saved: {out_path}")
print(f"File size: {size_kb:.0f} KB")
