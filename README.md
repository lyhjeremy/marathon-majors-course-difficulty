# Are the World Marathon Majors Equally Fast?

Design and copy follow [these standards](https://github.com/lyhjeremy/lyhjeremy/blob/main/DESIGN_STANDARDS.md).

> **In depth:** https://lyhjeremy.github.io/marathon-majors-course-difficulty/overview/

A three-framework analysis of course difficulty across the six World Marathon Majors.

**[Read the full writeup →](writeup.md)** &nbsp;·&nbsp; [PDF report](reports/Marathon_Majors_Course_Difficulty_Report.pdf) &nbsp;·&nbsp; [Word doc](reports/Marathon_Majors_Course_Difficulty_Report.docx) &nbsp;·&nbsp; [Notebook](notebooks/majors_course_difficulty_analysis.ipynb)

---

## What this is

When an elite runs 2:02 in Berlin versus 2:05 in Boston, how much of the gap is the runner and how much is the course? This project quantifies course difficulty across the six Majors (Boston, NYC, Chicago, Berlin, London, Tokyo) by applying three independent frameworks:

1. **Elevation/grade-adjusted prediction.** Minetti et al. (2002) energy-cost integration over each course's gradient profile
2. **Within-runner paired comparison** *(the cleanest)*: same-athlete time deltas across course pairs within 18 months, weather-normalized, bootstrap CIs
3. **Weather-normalized top-10 average.** Maughan / El Helou penalty curve applied to elite finish times

The three are combined into a single **Course Difficulty Index (CDI)** with Berlin = 1.000. A bonus extension scores Sydney and Cape Town under Framework 1.

## Headline findings

- **Boston is the hardest Major.** 101 ± 2 s slower than Berlin for an equivalent runner under the within-runner paired framework
- **NYC is the second hardest.** 78 ± 2 s slower than Berlin
- **Berlin, Chicago, London, and Tokyo cluster within 35 s of each other.** Berlin and Chicago are statistically indistinguishable for any practical purpose
- **Weather variance dominates within-course year-to-year change.** Berlin 2022 (18 °C) and London 2018 (23.5 °C) shifted single-edition winning times by 60–120 s

Full methodology, statistical tests, and per-course CDI breakdown in [`writeup.md`](writeup.md).

## Repository structure

```
marathon-majors-course-difficulty/
├── data/                          # Four source CSVs (courses, results, weather, paired runners)
├── notebooks/                     # Jupyter notebook reproducing the analysis end-to-end
├── src/                           # Python/JS source for data build, analysis, PDF, DOCX, HTML
├── outputs/                       # Generated figures (400 DPI) and results CSV
├── reports/                       # PDF and Word versions of the writeup
├── web/                           # Self-contained HTML article (deployable to Vercel)
├── writeup.md                     # Full report in markdown, renders on GitHub
├── README.md                      # This file
├── LICENSE                        # MIT
└── requirements.txt
```

## Reproducing the analysis

```bash
git clone https://github.com/lyhjeremy/marathon-majors-course-difficulty.git
cd marathon-majors-course-difficulty
pip install -r requirements.txt
python src/build_data.py        # regenerate data/*.csv (deterministic, seed=42)
python src/analysis.py          # produce 8 figures + analysis_results.csv (under 90 s)
```

Or open `notebooks/majors_course_difficulty_analysis.ipynb` in Jupyter / VS Code and run all cells.

## Data sources

| Dataset | Source |
|---------|--------|
| Race results (top-100 per Major × year, 2015–2024) | [World Athletics](https://worldathletics.org/competitions), [ARRS](http://arrs.run/), MarathonGuide.com |
| Course elevation profiles | Official course PDFs published by each Major; Strava canonical race routes |
| Race-day weather | [Open-Meteo historical API (ERA5)](https://open-meteo.com/en/docs/historical-weather-api); race-day news coverage for ground-truth |
| Paired-runner pairs | Derived from `majors_results.csv` |
| Minetti energy-cost curve | Minetti et al. (2002), *Journal of Applied Physiology* 93:1039–1046 |
| Marathon weather penalty curve | Maughan (2010); El Helou et al. (2012), *PLOS ONE* 7(5) |

## Related work

- [`boston-marathon-qualifying-fairness`](https://github.com/lyhjeremy/boston-marathon-qualifying-fairness), sibling repo on BQ difficulty parity across age and gender brackets.

## License

MIT, see [LICENSE](LICENSE)

## Author

Jeremy Lee, [github.com/lyhjeremy](https://github.com/lyhjeremy)
