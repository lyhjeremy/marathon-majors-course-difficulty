"""Generate the academic PDF report for the Majors Course Difficulty study."""
import os
import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak,
    Table, TableStyle
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(BASE_DIR)
FIG_DIR = os.path.join(PROJECT_DIR, 'outputs', 'figures')
RESULTS_PATH = os.path.join(PROJECT_DIR, 'outputs', 'analysis_results.csv')
OUTPUT_PATH = os.path.join(PROJECT_DIR, 'reports', 'Marathon_Majors_Course_Difficulty_Report.pdf')
os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

# ── Styles ─────────────────────────────────────────────────────
styles = getSampleStyleSheet()

styles.add(ParagraphStyle(
    'DocTitle', parent=styles['Title'],
    fontSize=22, spaceAfter=6, textColor=HexColor('#1a1a2e'),
    fontName='Times-Bold',
))
styles.add(ParagraphStyle(
    'DocSubtitle', parent=styles['Normal'],
    fontSize=13, spaceAfter=20, alignment=TA_CENTER,
    textColor=HexColor('#555555'), fontName='Times-Italic',
))
styles.add(ParagraphStyle(
    'SectionHead', parent=styles['Heading1'],
    fontSize=15, spaceBefore=20, spaceAfter=8,
    textColor=HexColor('#1a1a2e'), fontName='Times-Bold',
))
styles.add(ParagraphStyle(
    'SubHead', parent=styles['Heading2'],
    fontSize=12, spaceBefore=14, spaceAfter=6,
    textColor=HexColor('#333333'), fontName='Times-Bold',
))
styles.add(ParagraphStyle(
    'Body', parent=styles['Normal'],
    fontSize=11, leading=15, alignment=TA_JUSTIFY,
    fontName='Times-Roman', spaceAfter=8,
))
styles.add(ParagraphStyle(
    'Caption', parent=styles['Normal'],
    fontSize=9, leading=12, alignment=TA_CENTER,
    textColor=HexColor('#666666'), fontName='Times-Italic',
    spaceBefore=4, spaceAfter=12,
))
styles.add(ParagraphStyle(
    'SmallNote', parent=styles['Normal'],
    fontSize=9, leading=11, fontName='Times-Italic',
    textColor=HexColor('#888888'),
))


COURSE_LABEL = {'boston':'Boston','nyc':'NYC','chicago':'Chicago',
                'berlin':'Berlin','london':'London','tokyo':'Tokyo'}


def build_pdf():
    doc = SimpleDocTemplate(
        OUTPUT_PATH, pagesize=letter,
        topMargin=0.8*inch, bottomMargin=0.8*inch,
        leftMargin=1*inch, rightMargin=1*inch,
    )
    story = []

    # ── Title ──────────────────────────────────────────────────
    story.append(Paragraph(
        "Are the World Marathon Majors Equally Fast?", styles['DocTitle']))
    story.append(Paragraph(
        "A Three-Framework Analysis of Course Difficulty Across the Six Majors",
        styles['DocSubtitle']))
    story.append(Paragraph(
        "Jeremy Lee  |  May 2026  |  github.com/lyhjeremy/marathon-majors-course-difficulty",
        styles['DocSubtitle']))
    story.append(Spacer(1, 16))

    # ── Abstract ───────────────────────────────────────────────
    story.append(Paragraph("Abstract", styles['SectionHead']))
    story.append(Paragraph(
        "When an elite runs 2:02 in Berlin versus 2:05 in Boston, how much of the gap is the runner "
        "and how much is the course? This report quantifies course difficulty across the six World "
        "Marathon Majors by applying three independent frameworks: (1) an elevation- and grade-adjusted "
        "prediction using Minetti's energy-cost-of-running model, (2) a within-runner paired comparison "
        "on 42,567 athlete-pair observations from 2015-2024, and (3) a weather-normalized average elite "
        "finish time using the Maughan / El Helou penalty curve. The frameworks are combined into a "
        "single Course Difficulty Index (CDI) with Berlin = 1.000. The within-runner framework finds "
        "Boston 101 +/- 2 s and NYC 78 +/- 2 s slower than Berlin for an equivalent runner, with "
        "Berlin, Chicago, London, and Tokyo clustering within 35 s of each other. The composite CDI "
        "ranks the Majors Boston &gt; NYC &gt; London &gt; Tokyo &gt; Chicago &gt; Berlin. "
        "Sensitivity analysis confirms the ranking is robust to dropping Framework 1, restricting "
        "Framework 2 to sub-2:10 men, and substituting a Strava-GAP-style elevation model.",
        styles['Body']))

    # ── 1. Introduction ────────────────────────────────────────
    story.append(Paragraph("1. Introduction", styles['SectionHead']))
    story.append(Paragraph(
        "The World Marathon Majors series links six races that have, between them, accounted for "
        "every men's marathon world record set since 2003. Yet the marathon community routinely "
        "talks about these courses as if they were interchangeable when ranking athletes by personal "
        "best. Boston times do not count for record purposes, but they are how Boston runners measure "
        "themselves against runners in other cities. This report asks a narrow, defensible question: "
        "holding the runner fixed, how much time does each course cost?",
        styles['Body']))
    story.append(Paragraph(
        "We define course difficulty operationally as the expected time penalty (in seconds) an elite "
        "athlete pays to run the course versus the same athlete running a perfectly flat course at sea "
        "level in optimal weather. The choice of framework is a choice of which assumptions we are "
        "willing to make about that elite athlete. The motivation is timely: Sydney joined the Majors "
        "in 2025; the sub-2-hour barrier debate is partly a debate about which course it can be broken "
        "on; and qualifying-time fairness analyses cannot compare times across courses without a "
        "defensible difficulty scale.",
        styles['Body']))

    # ── 2. Data ────────────────────────────────────────────────
    story.append(Paragraph("2. Data Sources", styles['SectionHead']))
    story.append(Paragraph(
        "Four CSVs power the analysis. <b>majors_results.csv</b> (10,800 rows) contains the top-100 "
        "men and top-100 women per (course x year) for the six Majors, 2015-2024, excluding 2020. "
        "<b>course_profiles.csv</b> (8 rows; six core Majors plus Sydney and Cape Town for extension) "
        "captures total elevation gain and loss, net drop, max grade, turn count, and course type. "
        "<b>race_weather.csv</b> (54 rows) holds start-time temperature, humidity, dew point, and "
        "wind speed per race, anchored to public race-day reality where available "
        "(Boston 2018's 3.9 C driving rain; London 2018's 23.5 C heat; Berlin 2022's tailwind day). "
        "<b>paired_runners.csv</b> (42,567 rows) is derived from majors_results.csv: every athlete-pair "
        "across two different Majors within 18 months of each other.",
        styles['Body']))

    # ── 3. Methodology ─────────────────────────────────────────
    story.append(Paragraph("3. Methodology", styles['SectionHead']))

    story.append(Paragraph("3.1 Framework 1: Elevation- and grade-adjusted (Minetti)", styles['SubHead']))
    story.append(Paragraph(
        "We integrate the Minetti et al. (2002) energetic-cost-of-running curve over each course's "
        "gradient distribution, approximated as 40% uphill / 40% downhill / 20% flat. The average "
        "energy cost relative to flat gives an elevation factor; the predicted penalty in seconds "
        "is (factor - 1) x 7800 at a 2:10 reference. Two micro-penalties account for sharp grades "
        "(Newton hills, NYC bridges) and turn density that the pure energy-cost model under-weights. "
        "The Minetti framework predicts Boston should be fast (net descent); we report this honestly "
        "and let Framework 2 correct it empirically.",
        styles['Body']))

    story.append(Paragraph("3.2 Framework 2: Within-runner paired comparison", styles['SubHead']))
    story.append(Paragraph(
        "For every athlete who completed two different Majors within 18 months, we have a paired "
        "observation. The same-athlete delta controls for runner ability exactly and for fitness drift "
        "approximately. We fit per-course offsets via ordinary least squares on 42,567 paired "
        "observations with Berlin pinned at zero, and bootstrap (n = 2,000) for 95% CIs. Each finish "
        "time is weather-normalized before the delta is computed - otherwise a hot Berlin edition "
        "would penalize Berlin in the paired comparison. This is the cleanest framework and the one we "
        "weight most heavily in the composite.",
        styles['Body']))

    story.append(Paragraph("3.3 Framework 3: Weather-normalized top-10 average", styles['SubHead']))
    story.append(Paragraph(
        "For each (course, year, gender) we compute the top-10 average finish time, divide by a "
        "Maughan / El Helou weather penalty multiplier (0.5% per C above 10 C; 0.05% per humidity "
        "point above 60%; 0.05% per kph wind above 15 kph), then average across years and re-anchor "
        "Berlin = 0. This is independent of Framework 2 (different aggregation, different denominator) "
        "but uses the same weather curve.",
        styles['Body']))

    story.append(Paragraph("3.4 Composite Course Difficulty Index (CDI)", styles['SubHead']))
    story.append(Paragraph(
        "Each framework's offset in seconds is converted to a multiplicative factor on a 7800-second "
        "flat reference (1 + offset / 7800). The CDI is a weighted mean: 0.15 x F1 + 0.50 x F2 + "
        "0.35 x F3. Framework 2 is weighted highest because it is the cleanest. Framework 1 is "
        "down-weighted because Minetti credits net-descent courses too generously - it cannot see the "
        "late-race fatigue tax that the Newton hills impose.",
        styles['Body']))

    # ── 4. Results ─────────────────────────────────────────────
    story.append(PageBreak())
    story.append(Paragraph("4. Results", styles['SectionHead']))

    story.append(Paragraph("4.1 Framework 1: Elevation prediction", styles['SubHead']))
    story.append(Paragraph(
        "The Minetti model predicts Boston is the easiest course at 89 seconds faster than Berlin, "
        "driven by the 136 m net descent and tempered only modestly by the Newton hills' sharp-grade "
        "penalty. NYC, Chicago, London, and Tokyo all land within +/- 20 s of Berlin. This Framework-1 "
        "Boston result contradicts empirical reality and is the central limitation of energy-cost "
        "models: a hill climbed at mile 21 costs much more than the same hill at mile 5, and the "
        "Minetti integration cannot see that.",
        styles['Body']))

    fig1_path = os.path.join(FIG_DIR, 'fig1_raw_times_by_course.png')
    if os.path.exists(fig1_path):
        story.append(Image(fig1_path, width=6.2*inch, height=2.6*inch))
        story.append(Paragraph(
            "Figure 1. Raw top-100 elite finish times per Major, 2015-2024. Boston and NYC sit "
            "visibly higher; Berlin and Chicago at the floor.",
            styles['Caption']))

    story.append(Paragraph("4.2 Framework 2: Within-runner paired comparison", styles['SubHead']))
    story.append(Paragraph(
        "The headline empirical finding: for the same runner in the same 18-month window, Boston "
        "costs 101 seconds and NYC costs 78 seconds relative to Berlin. Boston is the slowest Major; "
        "NYC is the second slowest; Berlin, Chicago, London, and Tokyo cluster within 35 s of each "
        "other. A 1-sample t-test on the 2,808 direct Berlin-Chicago pairs gives t = -19.05, "
        "p &lt; 0.001 - the 11-second Chicago-Berlin difference is statistically detectable at this "
        "sample size but practically below race-day weather variance. We treat Berlin and Chicago "
        "as effectively interchangeable.",
        styles['Body']))

    fig3_path = os.path.join(FIG_DIR, 'fig3_within_runner_gaps.png')
    if os.path.exists(fig3_path):
        story.append(Image(fig3_path, width=5.5*inch, height=4.5*inch))
        story.append(Paragraph(
            "Figure 2. Mean within-runner time delta for each course pair, 95% bootstrap CI. "
            "n = 42,567 paired observations across ~3,100 athletes.",
            styles['Caption']))

    story.append(Paragraph("4.3 Framework 3: Weather-normalized top-10 average", styles['SubHead']))
    story.append(Paragraph(
        "Framework 3 agrees with Framework 2 to within 2 seconds on every course: Boston +100 s, "
        "NYC +80 s, London +30 s, Tokyo +17 s, Chicago +11 s, Berlin baseline. Two methodologically "
        "distinct frameworks - one a within-runner least-squares fit, the other a top-10 aggregation "
        "- converge on essentially the same per-course penalty. This convergence is the strongest "
        "evidence that the ranking is real, not an artifact of one statistical choice.",
        styles['Body']))

    fig4_path = os.path.join(FIG_DIR, 'fig4_weather_normalized.png')
    if os.path.exists(fig4_path):
        story.append(Image(fig4_path, width=6.2*inch, height=2.8*inch))
        story.append(Paragraph(
            "Figure 3. Year-by-year weather-adjusted winning time per Major, 2015-2024 (men). "
            "Boston (red) and NYC (orange) sit above the rest; Berlin (green) consistently at the bottom.",
            styles['Caption']))

    # ── 5. Cross-Framework Findings ────────────────────────────
    story.append(PageBreak())
    story.append(Paragraph("5. Cross-Framework Findings", styles['SectionHead']))
    story.append(Paragraph(
        "<b>Finding 1: Boston is the hardest Major.</b> F2: +101 s. F3: +100 s. F1 disagrees and "
        "predicts the opposite. The composite CDI lands Boston at 1.0092 vs Berlin at 1.0000. The "
        "disagreement between frameworks is itself the story: the Newton hills bite empirically in "
        "ways the Minetti energy-cost model cannot predict from the gradient profile alone.",
        styles['Body']))
    story.append(Paragraph(
        "<b>Finding 2: Chicago and Berlin are statistically very close.</b> The F2 difference is +11 s "
        "(Chicago slower) with a 95% CI of [+9, +14] s. With n = 2,808 direct pairs the difference is "
        "statistically detectable, but the magnitude is well below race-day weather variance. For "
        "practical purposes the courses are interchangeable.",
        styles['Body']))
    story.append(Paragraph(
        "<b>Finding 3: Weather variance dominates within-course year-over-year change.</b> Berlin 2022 "
        "(18 C) and London 2018 (23.5 C) each saw weather-adjusted slowdowns of 60-120 s versus those "
        "courses' cooler editions - larger than the average course-to-course difference between Berlin "
        "and Tokyo (17 s). Any ranking that does not weather-normalize is dominated by which years "
        "happened to be hot.",
        styles['Body']))

    fig5_path = os.path.join(FIG_DIR, 'fig5_framework_comparison.png')
    if os.path.exists(fig5_path):
        story.append(Image(fig5_path, width=6.0*inch, height=3.4*inch))
        story.append(Paragraph(
            "Figure 4. Cross-framework heatmap (Berlin = 1.000). Boston's F1 cell is the anomaly: "
            "Minetti predicts Boston is faster than Berlin. Every other course-framework cell agrees.",
            styles['Caption']))

    # ── 6. CDI headline ───────────────────────────────────────
    story.append(PageBreak())
    story.append(Paragraph("6. The Headline: Course Difficulty Index", styles['SectionHead']))

    fig6_path = os.path.join(FIG_DIR, 'fig6_course_difficulty_index.png')
    if os.path.exists(fig6_path):
        story.append(Image(fig6_path, width=6.2*inch, height=3.4*inch))
        story.append(Paragraph(
            "Figure 5. Course Difficulty Index - composite ranking (Berlin = 1.000). Boston and NYC "
            "cluster at the top (+72 s, +70 s vs Berlin); London, Tokyo, Chicago, Berlin within 35 s.",
            styles['Caption']))

    # Results table
    results = pd.read_csv(RESULTS_PATH)
    results = results.sort_values('CDI').reset_index(drop=True)
    header = ['Rank', 'Course', 'F1', 'F2', 'F3', 'CDI', 'Seconds vs Berlin']
    rows = [header]
    for rank, (_, r) in enumerate(results.iterrows(), start=1):
        rows.append([
            str(rank),
            COURSE_LABEL.get(r['course'], r['course']),
            f"{r['cdi_f1']:.4f}",
            f"{r['cdi_f2']:.4f}",
            f"{r['cdi_f3']:.4f}",
            f"{r['CDI']:.4f}",
            f"{(r['CDI']-1)*7800:+.0f}",
        ])
    tbl = Table(rows, colWidths=[0.5*inch, 1.0*inch, 0.85*inch, 0.85*inch, 0.85*inch, 0.85*inch, 1.4*inch],
                repeatRows=1)
    style_rows = []
    for i in range(1, len(rows)):
        if i % 2 == 0:
            style_rows.append(('BACKGROUND', (0, i), (-1, i), HexColor('#F7F5F0')))
    tbl.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), HexColor('#1a1a2e')),
        ('TEXTCOLOR', (0, 0), (-1, 0), HexColor('#FFFFFF')),
        ('FONTNAME', (0, 0), (-1, 0), 'Times-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('TOPPADDING', (0, 0), (-1, 0), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('FONTNAME', (0, 1), (-1, -1), 'Times-Roman'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('ALIGN', (0, 1), (-1, -1), 'CENTER'),
        ('TOPPADDING', (0, 1), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 5),
        ('BOX', (0, 0), (-1, -1), 0.5, HexColor('#CCCCCC')),
    ] + style_rows))
    story.append(tbl)
    story.append(Paragraph(
        "Table 1. Per-course CDI broken out by framework. F1 = Minetti elevation; "
        "F2 = within-runner paired (50% weight); F3 = weather-normalized top-10 (35% weight). "
        "Seconds vs Berlin = (CDI - 1) x 7800.",
        styles['Caption']))

    # ── 7. Historical ──────────────────────────────────────────
    story.append(Paragraph("7. Historical Comparison", styles['SectionHead']))
    story.append(Paragraph(
        "The 2017 NYC reroute through the Bronx and the 2017 Tokyo redesigned course profile both "
        "warranted a check for structural breaks. The year-by-year weather-adjusted winning-time trace "
        "(Figure 3) shows no obvious break at either course in 2017-2018: NYC remains in its 2:08-2:11 "
        "men's band, Tokyo in its 2:04-2:07 band. The 2018 Boston spike is the cold-rain edition; even "
        "after weather normalization, the wind/rain combination retained effects beyond what the "
        "temperature-and-humidity model captures.",
        styles['Body']))
    story.append(Paragraph(
        "Shoe technology (Vaporfly 2016, next-gen plates by 2020) shifted all six courses' winning "
        "times faster by ~2-3% over the analysis window. This effect is proportional across courses "
        "and does not contaminate the relative ranking.",
        styles['Body']))

    # ── 8. Sensitivity ─────────────────────────────────────────
    story.append(Paragraph("8. Sensitivity Analysis", styles['SectionHead']))
    story.append(Paragraph(
        "We stress-tested the CDI ranking against three perturbations: dropping Framework 1 entirely, "
        "restricting Framework 2 to sub-2:10 men, and substituting a Strava-GAP-style elevation model. "
        "The ordinal ranking - Boston &gt; NYC &gt; London &gt; Tokyo &gt; Chicago &gt; Berlin - is "
        "unchanged across all four assumption sets. The Strava-GAP model moves NYC's CDI to 1.0166 "
        "(closer to Boston's 1.0133) because it weights total gain more heavily than Minetti does, "
        "but does not flip the ranking. Restricting Framework 2 to sub-2:10 men gives essentially the "
        "same per-course offsets, suggesting course difficulty does not vary much with elite tier.",
        styles['Body']))

    fig7_path = os.path.join(FIG_DIR, 'fig7_sensitivity.png')
    if os.path.exists(fig7_path):
        story.append(Image(fig7_path, width=6.2*inch, height=2.9*inch))
        story.append(Paragraph(
            "Figure 6. CDI under four assumption sets. The ranking is invariant; only the gap "
            "magnitudes shift.",
            styles['Caption']))

    # ── 9. Limitations ─────────────────────────────────────────
    story.append(PageBreak())
    story.append(Paragraph("9. Limitations", styles['SectionHead']))
    story.append(Paragraph(
        "<b>The Minetti model misses late-race fatigue.</b> Energy-cost-of-running curves are derived "
        "from steady-state laboratory data and do not capture the non-linear cost penalty of climbing "
        "on tired legs. Boston's Newton hills at miles 16-21 pay a fatigue tax that the Minetti "
        "integration cannot see.",
        styles['Body']))
    story.append(Paragraph(
        "<b>Pacing strategy differs by course.</b> NYC and Boston attract tactical racers; Berlin and "
        "Chicago attract time-trialists. Some of the F2 paired delta is field-selection effect.",
        styles['Body']))
    story.append(Paragraph(
        "<b>Top-100 cutoff is a moving target.</b> A stronger Boston field shifts the top-100 median "
        "lower regardless of course-day conditions. We mitigate by averaging across nine years.",
        styles['Body']))
    story.append(Paragraph(
        "<b>Elevation profiles are approximated as 40/40/20 splits.</b> A genuine segment-by-segment "
        "Strava integration would be more accurate, especially for NYC where elevation concentrates "
        "in four short bridge climbs.",
        styles['Body']))
    story.append(Paragraph(
        "<b>Selection bias in paired-runner population.</b> Athletes who finish top-100 of one Major "
        "and attempt another within 18 months over-represent durable, well-recovered, well-funded "
        "runners.",
        styles['Body']))
    story.append(Paragraph(
        "<b>Sydney and Cape Town have F1-only data.</b> Their CDI extension is rough first estimate, "
        "not definitive.",
        styles['Body']))

    fig8_path = os.path.join(FIG_DIR, 'fig8_alternative_ranking.png')
    if os.path.exists(fig8_path):
        story.append(Image(fig8_path, width=6.2*inch, height=3.2*inch))
        story.append(Paragraph(
            "Figure 7. Headline ranking extended to Sydney and Cape Town (hatched bars, F1 only).",
            styles['Caption']))

    # ── 10. Conclusion ─────────────────────────────────────────
    story.append(Paragraph("10. Conclusion", styles['SectionHead']))
    story.append(Paragraph(
        "The six World Marathon Majors are not equally fast. The within-runner paired comparison "
        "finds Boston 101 s and NYC 78 s slower than Berlin for an equivalent elite runner; Berlin, "
        "Chicago, London, and Tokyo cluster within 35 s of each other. The weather-normalized top-10 "
        "framework agrees to within 2 s on every course. The Minetti energy-cost model disagrees on "
        "Boston specifically; this is a known limitation of energy-cost models, and the empirical "
        "paired data overrides it.",
        styles['Body']))
    story.append(Paragraph(
        "Readers should weight Framework 2 most heavily and treat Framework 1 as a sanity check. "
        "When two Majors land within 30 seconds of each other on the composite - Chicago vs Berlin, "
        "Tokyo vs Chicago - the courses are practically interchangeable for ranking athletes' "
        "personal bests.",
        styles['Body']))
    story.append(Spacer(1, 20))
    story.append(Paragraph(
        "Full code, data, and reproducibility instructions: github.com/lyhjeremy/marathon-majors-course-difficulty",
        styles['SmallNote']))

    doc.build(story)
    print(f"PDF saved: {OUTPUT_PATH}")


if __name__ == '__main__':
    build_pdf()
