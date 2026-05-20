"""Generate a self-contained HTML article (web/index.html) with embedded figures."""
import base64
import os
import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(BASE_DIR)
FIG_DIR = os.path.join(PROJECT_DIR, 'outputs', 'figures')
WEB_DIR = os.path.join(PROJECT_DIR, 'web')
os.makedirs(WEB_DIR, exist_ok=True)

COURSE_LABEL = {'boston':'Boston','nyc':'NYC','chicago':'Chicago',
                'berlin':'Berlin','london':'London','tokyo':'Tokyo'}

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
results = results.sort_values('CDI').reset_index(drop=True)

def table_rows():
    out = []
    for rank, (_, r) in enumerate(results.iterrows(), start=1):
        secs = (r['CDI'] - 1) * 7800
        sign = '+' if secs >= 0 else ''
        cls = 'rank-top' if rank <= 2 else ('rank-mid' if rank <= 4 else 'rank-low')
        out.append(f"""
        <tr class="{cls}">
          <td class="rank">{rank}</td>
          <td class="course">{COURSE_LABEL.get(r['course'], r['course'])}</td>
          <td class="num">{r['cdi_f1']:.4f}</td>
          <td class="num">{r['cdi_f2']:.4f}</td>
          <td class="num">{r['cdi_f3']:.4f}</td>
          <td class="num cdi"><strong>{r['CDI']:.4f}</strong></td>
          <td class="seconds">{sign}{secs:.0f}s</td>
        </tr>""")
    return ''.join(out)

trows = table_rows()


HERO_SVG = """<svg viewBox="0 0 1200 320" xmlns="http://www.w3.org/2000/svg" preserveAspectRatio="xMidYMid slice">
  <defs>
    <linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#0F1729"/>
      <stop offset="60%" stop-color="#1E2A4A"/>
      <stop offset="100%" stop-color="#2A3F6E"/>
    </linearGradient>
    <linearGradient id="elev" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#1B3A66" stop-opacity="0.4"/>
      <stop offset="100%" stop-color="#0F1729" stop-opacity="0.0"/>
    </linearGradient>
  </defs>
  <rect width="1200" height="320" fill="url(#sky)"/>
  <!-- Boston-style up-and-down profile -->
  <path d="M 0 250 L 100 245 L 200 235 L 300 215 L 400 230 L 500 180 L 600 165 L 700 140 L 800 175 L 900 195 L 1000 215 L 1100 230 L 1200 240 L 1200 320 L 0 320 Z"
        fill="url(#elev)" stroke="#7FA8D7" stroke-width="2" stroke-linejoin="round"/>
  <!-- City markers -->
  <g fill="#E5E7EB" font-family="Georgia, serif" font-size="13">
    <text x="50" y="295" opacity="0.7">Berlin</text>
    <text x="250" y="295" opacity="0.7">Chicago</text>
    <text x="450" y="295" opacity="0.7">London</text>
    <text x="650" y="295" opacity="0.7">Tokyo</text>
    <text x="850" y="295" opacity="0.7">NYC</text>
    <text x="1050" y="295" opacity="0.7">Boston</text>
  </g>
  <!-- Title -->
  <text x="600" y="90" fill="#F5E9D5" font-family="Georgia, serif" font-size="46" font-weight="700" text-anchor="middle">
    Six Majors. Six Courses. Not Equal.
  </text>
  <text x="600" y="125" fill="#D4A537" font-family="Georgia, serif" font-size="20" font-style="italic" text-anchor="middle">
    Quantifying course difficulty across the World Marathon Majors
  </text>
</svg>"""


HTML = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>Are the World Marathon Majors Equally Fast?</title>
<meta name="description" content="A three-framework analysis of course difficulty across the six World Marathon Majors. Boston is ~101 seconds slower than Berlin for an equivalent runner. Berlin, Chicago, Tokyo, London cluster within 35 seconds." />
<style>
  :root {{
    --ink: #1a1a2e;
    --paper: #FBF8F1;
    --rule: #E5DCC7;
    --soft: #6B7280;
    --accent: #D4A537;
    --boston: #B91C1C;
    --nyc: #F97316;
    --chicago: #2563EB;
    --berlin: #059669;
    --london: #7C3AED;
    --tokyo: #0EA5E9;
  }}
  * {{ box-sizing: border-box; }}
  html, body {{ margin: 0; padding: 0; }}
  body {{
    background: var(--paper);
    color: var(--ink);
    font-family: Georgia, 'Times New Roman', serif;
    line-height: 1.7;
    font-size: 18px;
  }}
  .hero {{
    width: 100%;
    height: 320px;
    background: #0F1729;
    overflow: hidden;
  }}
  .hero svg {{ width: 100%; height: 320px; display: block; }}
  .container {{
    max-width: 760px;
    margin: 0 auto;
    padding: 40px 24px 80px;
  }}
  .byline {{
    color: var(--soft);
    font-style: italic;
    margin: 24px 0 40px;
    text-align: center;
  }}
  h1 {{ display: none; }}
  h2 {{
    font-family: Georgia, serif;
    font-size: 28px;
    margin: 56px 0 16px;
    border-bottom: 1px solid var(--rule);
    padding-bottom: 8px;
  }}
  h3 {{ font-size: 22px; margin: 36px 0 12px; }}
  p {{ margin: 0 0 18px; }}
  blockquote {{
    border-left: 4px solid var(--accent);
    margin: 28px 0;
    padding: 4px 24px;
    color: var(--ink);
    font-style: italic;
    background: rgba(212, 165, 55, 0.07);
  }}
  .figure {{ margin: 36px 0; text-align: center; }}
  .figure img {{ max-width: 100%; height: auto; border: 1px solid var(--rule); }}
  .figure figcaption {{ font-size: 14px; color: var(--soft); font-style: italic; margin-top: 10px; }}
  table {{
    width: 100%;
    border-collapse: collapse;
    margin: 24px 0;
    font-family: 'Helvetica Neue', Arial, sans-serif;
    font-size: 15px;
  }}
  table th {{
    background: var(--ink);
    color: white;
    padding: 12px 8px;
    text-align: center;
    font-weight: 700;
  }}
  table td {{ padding: 10px 8px; text-align: center; border-bottom: 1px solid var(--rule); }}
  tr.rank-top {{ background: rgba(185, 28, 28, 0.07); font-weight: 600; }}
  tr.rank-mid {{ background: rgba(124, 58, 237, 0.04); }}
  tr.rank-low {{ background: rgba(5, 150, 105, 0.05); }}
  td.cdi {{ color: var(--ink); font-size: 16px; }}
  td.course {{ font-weight: 700; }}
  .findings {{ background: white; border: 1px solid var(--rule); padding: 24px 32px; margin: 32px 0; }}
  .findings h3 {{ margin-top: 18px; }}
  .findings h3:first-child {{ margin-top: 0; }}
  .stat-grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; margin: 32px 0; }}
  .stat-box {{
    background: white; border: 1px solid var(--rule);
    padding: 20px; text-align: center;
  }}
  .stat-big {{ font-family: Georgia, serif; font-size: 38px; font-weight: 700; color: var(--ink); line-height: 1; }}
  .stat-label {{ font-size: 13px; color: var(--soft); text-transform: uppercase; letter-spacing: 0.5px; margin-top: 6px; }}
  .footer {{ font-size: 14px; color: var(--soft); text-align: center; margin-top: 64px; padding-top: 32px; border-top: 1px solid var(--rule); }}
  .footer a {{ color: var(--soft); }}
  @media (max-width: 600px) {{
    .container {{ padding: 24px 16px 56px; }}
    h2 {{ font-size: 24px; }}
    .stat-grid {{ grid-template-columns: 1fr; }}
  }}
</style>
</head>
<body>

<header class="hero">{HERO_SVG}</header>

<main class="container">

  <p class="byline">Jeremy Lee &nbsp;·&nbsp; May 2026 &nbsp;·&nbsp; <a href="https://github.com/lyhjeremy/marathon-majors-course-difficulty">github.com/lyhjeremy</a></p>

  <p>When an elite runs 2:02 in Berlin versus 2:05 in Boston, how much of the gap is the runner and how much is the course? Boston times don’t count for record purposes — but they’re how Boston runners measure themselves against runners in other cities. To compare an athlete’s personal bests across courses, you need a defensible scale.</p>

  <p>This article quantifies course difficulty across the six World Marathon Majors using three independent analytical frameworks. The headline answer: <strong>Boston is the hardest, slower than Berlin by 101 seconds for an equivalent runner</strong>. NYC is second at +78s. Berlin, Chicago, London, and Tokyo cluster within 35 seconds of each other.</p>

  <div class="stat-grid">
    <div class="stat-box"><div class="stat-big">+101s</div><div class="stat-label">Boston vs Berlin</div></div>
    <div class="stat-box"><div class="stat-big">+78s</div><div class="stat-label">NYC vs Berlin</div></div>
    <div class="stat-box"><div class="stat-big">42,567</div><div class="stat-label">Paired observations</div></div>
  </div>

  <h2>1. The three frameworks</h2>

  <p>We define course difficulty operationally: the expected time penalty (in seconds) an elite runner pays to run this course versus a flat, sea-level course in optimal weather. Three independent frameworks:</p>

  <h3>F1 — Elevation/grade-adjusted (Minetti)</h3>
  <p>Integrate Minetti's (2002) energy-cost-of-running curve over each course's gradient distribution. Predicts that Boston, with its 136m net descent, should be <em>faster</em> than a flat course. We report this honestly: Frameworks 2 and 3 override it.</p>

  <h3>F2 — Within-runner paired comparison <em>(the cleanest)</em></h3>
  <p>For every athlete who ran two different Majors within 18 months, compute the time delta. Fit per-course offsets with Berlin = 0. Bootstrap 2,000 times for 95% CIs. This is the gold-standard framework because it controls for athlete ability without any course physics assumption.</p>

  <h3>F3 — Weather-normalized top-10 average</h3>
  <p>Top-10 average finish time per (course, year, gender), divided by a Maughan / El Helou weather penalty multiplier, averaged across 2015–2024, anchored to Berlin = 0. Independent of F2 in aggregation; shares only the weather curve.</p>

  <h2>2. What the data show</h2>

  <figure class="figure">
    <img src="data:image/png;base64,{fig1}" alt="Raw top-100 finish times per Major" />
    <figcaption>Figure 1. Raw top-100 elite finish times per Major, 2015–2024. Boston and NYC sit visibly higher; Berlin and Chicago at the floor.</figcaption>
  </figure>

  <figure class="figure">
    <img src="data:image/png;base64,{fig3}" alt="Within-runner course-pair forest plot" />
    <figcaption>Figure 2. Mean within-runner time delta for each of the 15 course pairs, 95% bootstrap CI. n = 42,567 paired observations.</figcaption>
  </figure>

  <p>The within-runner framework is unambiguous: <strong>Boston +101s, NYC +78s, London +31s, Tokyo +21s, Chicago +11s, Berlin (baseline)</strong>. The Boston vs NYC gap is statistically clean — their CIs do not overlap.</p>

  <figure class="figure">
    <img src="data:image/png;base64,{fig4}" alt="Year-by-year weather-adjusted winning times" />
    <figcaption>Figure 3. Weather-normalized winning time by Major (men, 2015–2024). Boston (red) and NYC (orange) sit above the rest; Berlin (green) consistently at the bottom.</figcaption>
  </figure>

  <h2>3. The headline: Course Difficulty Index</h2>

  <p>Combine all three frameworks into a Course Difficulty Index (CDI) anchored at Berlin = 1.000:</p>

  <blockquote>
    CDI = 0.15 × F1 + 0.50 × F2 + 0.35 × F3
  </blockquote>

  <p>Framework 2 gets the heaviest weight because it's the cleanest. Framework 1 is down-weighted because the Minetti model can't see late-race fatigue.</p>

  <figure class="figure">
    <img src="data:image/png;base64,{fig6}" alt="Course Difficulty Index ranking" />
    <figcaption>Figure 4. Course Difficulty Index — composite ranking (Berlin = 1.000). Error bars from F2's bootstrap CI.</figcaption>
  </figure>

  <table>
    <thead>
      <tr><th>Rank</th><th>Course</th><th>F1</th><th>F2</th><th>F3</th><th>CDI</th><th>vs Berlin</th></tr>
    </thead>
    <tbody>{trows}</tbody>
  </table>

  <h2>4. Three findings that survive every framework</h2>

  <div class="findings">
    <h3>Finding 1 — Boston is the hardest Major.</h3>
    <p>F2: +101s. F3: +100s. F1 disagrees and predicts Boston should be net-fast. The disagreement is the story: the Newton hills bite empirically in ways the elevation model can't predict from the gradient profile alone.</p>

    <h3>Finding 2 — Chicago and Berlin are statistically very close.</h3>
    <p>The F2 difference is +11s with a 95% CI of [+9, +14]s. Detectable at n = 2,808 direct pairs, but well below race-day weather variance. Practically interchangeable.</p>

    <h3>Finding 3 — Weather dominates within-course year-over-year change.</h3>
    <p>Berlin 2022 (18°C) and London 2018 (23.5°C) each saw weather-adjusted slowdowns of 60–120s — larger than the average gap between Berlin and Tokyo (17s).</p>
  </div>

  <h2>5. Cross-framework view</h2>

  <figure class="figure">
    <img src="data:image/png;base64,{fig5}" alt="Cross-framework heatmap" />
    <figcaption>Figure 5. Difficulty multiplier by course × framework. Boston's F1 cell is the only one that disagrees: Minetti predicts Boston should be faster than Berlin.</figcaption>
  </figure>

  <h2>6. Sensitivity — does the ranking hold?</h2>

  <p>We stress-tested the CDI against three perturbations: drop Framework 1 entirely; restrict Framework 2 to sub-2:10 men; substitute a Strava-GAP-style elevation model.</p>

  <figure class="figure">
    <img src="data:image/png;base64,{fig7}" alt="Sensitivity analysis" />
    <figcaption>Figure 6. CDI under four assumption sets. The ordinal ranking — Boston &gt; NYC &gt; London &gt; Tokyo &gt; Chicago &gt; Berlin — is invariant.</figcaption>
  </figure>

  <h2>7. Beyond the six — Sydney and Cape Town</h2>

  <p>Sydney joined the Majors in 2025; we don't yet have paired-runner data for it. The extension below uses Framework 1 (elevation) only.</p>

  <figure class="figure">
    <img src="data:image/png;base64,{fig8}" alt="Extended ranking" />
    <figcaption>Figure 7. Headline ranking extended to Sydney and Cape Town (hatched bars, F1 only). Both slot between Tokyo and NYC on the elevation prediction.</figcaption>
  </figure>

  <h2>8. The takeaway</h2>

  <p>The six World Marathon Majors are not equally fast. If you ran 2:08 in Boston, the equivalent Berlin effort is about 2:06 — almost two minutes faster, for the same physiological work. If you ran 2:08 in Chicago, the equivalent Berlin time is 2:07:49, and the two are practically interchangeable. For most readers ranking their personal bests across Majors, this is the missing scale.</p>

  <p>Full code, data, methodology, and reproducibility instructions live at <a href="https://github.com/lyhjeremy/marathon-majors-course-difficulty">github.com/lyhjeremy/marathon-majors-course-difficulty</a>. The analysis runs end-to-end from <code>python src/analysis.py</code> in under 90 seconds.</p>

  <div class="footer">
    © 2026 Jeremy Lee · MIT License · Data current as of May 2026<br/>
    <a href="https://github.com/lyhjeremy/marathon-majors-course-difficulty">Repository</a> &nbsp;·&nbsp;
    <a href="https://github.com/lyhjeremy/marathon-majors-course-difficulty/blob/main/writeup.md">Full writeup</a> &nbsp;·&nbsp;
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
