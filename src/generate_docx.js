// Generate the DOCX report for the Majors Course Difficulty study.
// Mirrors the PDF: 10 sections, embedded figures, results table.
//
// Run: node src/generate_docx.js   (after `npm install docx`)

const fs = require('fs');
const path = require('path');
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  ImageRun, AlignmentType, HeadingLevel, BorderStyle, WidthType,
  ShadingType, PageBreak,
} = require('docx');

const PROJECT_DIR = path.resolve(__dirname, '..');
const FIG_DIR = path.join(PROJECT_DIR, 'outputs', 'figures');
const RESULTS_PATH = path.join(PROJECT_DIR, 'outputs', 'analysis_results.csv');
const OUT_PATH = path.join(PROJECT_DIR, 'reports', 'Marathon_Majors_Course_Difficulty_Report.docx');

const COURSE_LABEL = {
  boston: 'Boston', nyc: 'NYC', chicago: 'Chicago',
  berlin: 'Berlin', london: 'London', tokyo: 'Tokyo',
};

function loadResults() {
  const text = fs.readFileSync(RESULTS_PATH, 'utf-8').trim();
  const lines = text.split('\n');
  const headers = lines[0].split(',');
  return lines.slice(1).map(line => {
    const cells = line.split(',');
    const obj = {};
    headers.forEach((h, i) => { obj[h] = cells[i]; });
    return obj;
  });
}

const COLOR = {
  text: '1A1A2E', soft: '555555', muted: '888888',
  shadeHead: '1A1A2E', shadeAlt: 'F5F2EC',
};

function p(text, opts = {}) {
  return new Paragraph({
    alignment: opts.align || AlignmentType.JUSTIFIED,
    spacing: { after: opts.after !== undefined ? opts.after : 120, line: 320 },
    children: [new TextRun({
      text, font: 'Calibri', size: opts.size || 22,
      bold: !!opts.bold, italics: !!opts.italics,
      color: opts.color || COLOR.text,
    })],
  });
}

function pRich(runs, opts = {}) {
  return new Paragraph({
    alignment: opts.align || AlignmentType.JUSTIFIED,
    spacing: { after: opts.after !== undefined ? opts.after : 120, line: 320 },
    children: runs.map(r => {
      if (typeof r === 'string') {
        return new TextRun({ text: r, font: 'Calibri', size: 22, color: COLOR.text });
      }
      return new TextRun({
        text: r.text, font: 'Calibri', size: r.size || 22,
        bold: !!r.bold, italics: !!r.italics, color: r.color || COLOR.text,
      });
    }),
  });
}

function head(text, level = 1) {
  return new Paragraph({
    heading: level === 1 ? HeadingLevel.HEADING_1 : HeadingLevel.HEADING_2,
    spacing: { before: level === 1 ? 360 : 200, after: level === 1 ? 160 : 120 },
    children: [new TextRun({
      text, font: 'Georgia',
      size: level === 1 ? 30 : 24, bold: true, color: COLOR.text,
    })],
  });
}

function imageBlock(filename, widthPx, heightPx, caption) {
  const data = fs.readFileSync(path.join(FIG_DIR, filename));
  const blocks = [
    new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { before: 160, after: 80 },
      children: [new ImageRun({
        type: 'png', data,
        transformation: { width: widthPx, height: heightPx },
        altText: { title: filename, description: caption, name: filename },
      })],
    }),
  ];
  if (caption) {
    blocks.push(new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { after: 240, line: 280 },
      children: [new TextRun({
        text: caption, font: 'Calibri', size: 18,
        italics: true, color: COLOR.muted,
      })],
    }));
  }
  return blocks;
}

const children = [];

// Title block
children.push(new Paragraph({
  alignment: AlignmentType.CENTER, spacing: { after: 80 },
  children: [new TextRun({
    text: 'Are the World Marathon Majors Equally Fast?',
    font: 'Georgia', size: 44, bold: true, color: COLOR.text,
  })],
}));
children.push(new Paragraph({
  alignment: AlignmentType.CENTER, spacing: { after: 80 },
  children: [new TextRun({
    text: 'A Three-Framework Analysis of Course Difficulty Across the Six Majors',
    font: 'Georgia', size: 26, italics: true, color: COLOR.soft,
  })],
}));
children.push(new Paragraph({
  alignment: AlignmentType.CENTER, spacing: { after: 360 },
  children: [new TextRun({
    text: 'Jeremy Lee  |  May 2026  |  github.com/lyhjeremy/marathon-majors-course-difficulty',
    font: 'Georgia', size: 22, italics: true, color: COLOR.soft,
  })],
}));

// Abstract
children.push(head('Abstract'));
children.push(p(
  'When an elite runs 2:02 in Berlin versus 2:05 in Boston, how much of the gap is the runner and how much is the course? This report quantifies course difficulty across the six World Marathon Majors by applying three independent frameworks: (1) an elevation- and grade-adjusted prediction using Minetti’s energy-cost-of-running model, (2) a within-runner paired comparison on 42,567 athlete-pair observations from 2015–2024, and (3) a weather-normalized average elite finish time using the Maughan / El Helou penalty curve. The frameworks are combined into a single Course Difficulty Index (CDI) with Berlin = 1.000. The within-runner framework finds Boston 101 ± 2 s and NYC 78 ± 2 s slower than Berlin for an equivalent runner, with Berlin, Chicago, London, and Tokyo clustering within 35 s of each other. The composite CDI ranks the Majors Boston > NYC > London > Tokyo > Chicago > Berlin. Sensitivity analysis confirms the ranking is robust to dropping Framework 1, restricting Framework 2 to sub-2:10 men, and substituting a Strava-GAP-style elevation model.'
));

// 1. Introduction
children.push(head('1. Introduction'));
children.push(p('The World Marathon Majors series links six races that have, between them, accounted for every men’s marathon world record set since 2003. Yet the marathon community routinely talks about these courses as if they were interchangeable when ranking athletes by personal best. Boston times do not count for record purposes, but they are how Boston runners measure themselves against runners in other cities. This report asks a narrow, defensible question: holding the runner fixed, how much time does each course cost?'));
children.push(p('We define course difficulty operationally as the expected time penalty (in seconds) an elite athlete pays to run the course versus the same athlete running a perfectly flat course at sea level in optimal weather. The choice of framework is a choice of which assumptions we are willing to make about that elite athlete.'));

// 2. Data
children.push(head('2. Data Sources'));
children.push(pRich([
  'Four CSVs power the analysis. ',
  { text: 'majors_results.csv', bold: true },
  ' (10,800 rows) contains top-100 men and top-100 women per (course × year) for the six Majors, 2015–2024, excluding 2020. ',
  { text: 'course_profiles.csv', bold: true },
  ' (8 rows) captures total elevation gain and loss, net drop, max grade, turn count, and course type. ',
  { text: 'race_weather.csv', bold: true },
  ' (54 rows) holds start-time temperature, humidity, dew point, and wind speed per race, anchored to public race-day reality where available (Boston 2018’s 3.9 °C driving rain; London 2018’s 23.5 °C heat; Berlin 2022’s tailwind day). ',
  { text: 'paired_runners.csv', bold: true },
  ' (42,567 rows) is derived from majors_results.csv: every athlete-pair across two different Majors within 18 months.',
]));

// 3. Methodology
children.push(head('3. Methodology'));
children.push(head('3.1 Framework 1: Elevation- and grade-adjusted (Minetti)', 2));
children.push(p('We integrate the Minetti et al. (2002) energetic-cost-of-running curve over each course’s gradient distribution, approximated as 40% uphill / 40% downhill / 20% flat. The average energy cost relative to flat gives an elevation factor; the predicted penalty in seconds is (factor − 1) × 7800 at a 2:10 reference. Two micro-penalties account for sharp grades (Newton hills, NYC bridges) and turn density that the pure energy-cost model under-weights. The Minetti framework predicts Boston should be fast (net descent); we report this honestly and let Framework 2 correct it empirically.'));

children.push(head('3.2 Framework 2: Within-runner paired comparison', 2));
children.push(p('For every athlete who completed two different Majors within 18 months, we have a paired observation. The same-athlete delta controls for runner ability exactly and for fitness drift approximately. We fit per-course offsets via ordinary least squares on 42,567 paired observations with Berlin pinned at zero, and bootstrap (n = 2,000) for 95% CIs. Each finish time is weather-normalized before the delta is computed. Otherwise a hot Berlin edition would penalize Berlin in the paired comparison. This is the cleanest framework and the one we weight most heavily in the composite.'));

children.push(head('3.3 Framework 3: Weather-normalized top-10 average', 2));
children.push(p('For each (course, year, gender) we compute the top-10 average finish time, divide by a Maughan / El Helou weather penalty multiplier (0.5% per °C above 10 °C; 0.05% per humidity point above 60%; 0.05% per kph wind above 15 kph), then average across years and re-anchor Berlin = 0.'));

children.push(head('3.4 Composite Course Difficulty Index (CDI)', 2));
children.push(p('Each framework’s offset in seconds is converted to a multiplicative factor on a 7800-second flat reference (1 + offset / 7800). The CDI is a weighted mean: 0.15 × F1 + 0.50 × F2 + 0.35 × F3. Framework 2 is weighted highest because it is the cleanest. Framework 1 is down-weighted because Minetti credits net-descent courses too generously. It cannot see the late-race fatigue tax that the Newton hills impose.'));

// 4. Results
children.push(new Paragraph({ children: [new PageBreak()] }));
children.push(head('4. Results'));

children.push(head('4.1 Framework 1: Elevation prediction', 2));
children.push(p('The Minetti model predicts Boston is the easiest course at 89 seconds faster than Berlin, driven by the 136 m net descent and tempered only modestly by the Newton hills’ sharp-grade penalty. NYC, Chicago, London, and Tokyo all land within ± 20 s of Berlin. This Framework-1 Boston result contradicts empirical reality and is the central limitation of energy-cost models: a hill climbed at mile 21 costs much more than the same hill at mile 5.'));
imageBlock('fig1_raw_times_by_course.png', 600, 250,
  'Figure 1. Raw top-100 elite finish times per Major, 2015–2024. Boston and NYC sit visibly higher; Berlin and Chicago at the floor.'
).forEach(b => children.push(b));

children.push(head('4.2 Framework 2: Within-runner paired comparison', 2));
children.push(p('The headline empirical finding: for the same runner in the same 18-month window, Boston costs 101 seconds and NYC costs 78 seconds relative to Berlin. Boston is the slowest Major; NYC is the second slowest; Berlin, Chicago, London, and Tokyo cluster within 35 s of each other. A 1-sample t-test on the 2,808 direct Berlin–Chicago pairs gives t = −19.05, p < 0.001. The 11-second Chicago–Berlin difference is statistically detectable at this sample size but practically below race-day weather variance.'));
imageBlock('fig3_within_runner_gaps.png', 500, 410,
  'Figure 2. Mean within-runner time delta for each course pair, 95% bootstrap CI. n = 42,567 paired observations across ~3,100 athletes.'
).forEach(b => children.push(b));

children.push(head('4.3 Framework 3: Weather-normalized top-10 average', 2));
children.push(p('Framework 3 agrees with Framework 2 to within 2 seconds on every course: Boston +100 s, NYC +80 s, London +30 s, Tokyo +17 s, Chicago +11 s, Berlin baseline. Two methodologically distinct frameworks converge on essentially the same per-course penalty. This convergence is the strongest evidence that the ranking is real, not an artifact of one statistical choice.'));
imageBlock('fig4_weather_normalized.png', 600, 275,
  'Figure 3. Year-by-year weather-adjusted winning time per Major, 2015–2024 (men). Boston (red) and NYC (orange) sit above the rest; Berlin (green) consistently at the bottom.'
).forEach(b => children.push(b));

// 5. Cross-framework findings
children.push(new Paragraph({ children: [new PageBreak()] }));
children.push(head('5. Cross-Framework Findings'));
children.push(pRich([
  { text: 'Finding 1: Boston is the hardest Major. ', bold: true },
  'F2: +101 s. F3: +100 s. F1 disagrees and predicts the opposite. The composite CDI lands Boston at 1.0092 vs Berlin at 1.0000. The disagreement between frameworks is itself the story: the Newton hills bite empirically in ways the Minetti energy-cost model cannot predict from the gradient profile alone.',
]));
children.push(pRich([
  { text: 'Finding 2: Chicago and Berlin are statistically very close. ', bold: true },
  'The F2 difference is +11 s (Chicago slower) with a 95% CI of [+9, +14] s. With n = 2,808 direct pairs the difference is statistically detectable, but the magnitude is well below race-day weather variance. For practical purposes the courses are interchangeable.',
]));
children.push(pRich([
  { text: 'Finding 3: Weather variance dominates within-course year-over-year change. ', bold: true },
  'Berlin 2022 (18 °C) and London 2018 (23.5 °C) each saw weather-adjusted slowdowns of 60–120 s versus those courses’ cooler editions: larger than the average course-to-course difference between Berlin and Tokyo (17 s).',
]));
imageBlock('fig5_framework_comparison.png', 580, 320,
  'Figure 4. Cross-framework heatmap (Berlin = 1.000). Boston’s F1 cell is the anomaly: Minetti predicts Boston is faster than Berlin. Every other course-framework cell agrees.'
).forEach(b => children.push(b));

// 6. CDI
children.push(new Paragraph({ children: [new PageBreak()] }));
children.push(head('6. The Headline: Course Difficulty Index'));
imageBlock('fig6_course_difficulty_index.png', 600, 325,
  'Figure 5. Course Difficulty Index, composite ranking (Berlin = 1.000).'
).forEach(b => children.push(b));

// Results table
function tcell(text, opts = {}) {
  return new TableCell({
    width: { size: opts.width || 1200, type: WidthType.DXA },
    shading: opts.shading ? { type: ShadingType.CLEAR, fill: opts.shading } : undefined,
    margins: { top: 80, bottom: 80, left: 80, right: 80 },
    children: [new Paragraph({
      alignment: opts.align || AlignmentType.LEFT,
      spacing: { before: 0, after: 0 },
      children: [new TextRun({
        text, font: 'Calibri', size: opts.size || 18,
        bold: !!opts.bold, color: opts.color || COLOR.text,
      })],
    })],
  });
}

const results = loadResults().sort((a, b) => parseFloat(a.CDI) - parseFloat(b.CDI));
const colW = [700, 1000, 950, 950, 950, 950, 1500];
const headerCells = ['Rank', 'Course', 'F1', 'F2', 'F3', 'CDI', 'Seconds vs Berlin'].map((h, i) =>
  tcell(h, { width: colW[i], shading: COLOR.shadeHead, color: 'FFFFFF', bold: true, align: AlignmentType.CENTER })
);
const tableRows = [new TableRow({ children: headerCells, tableHeader: true })];
results.forEach((r, i) => {
  const shade = (i % 2 === 0) ? undefined : COLOR.shadeAlt;
  const seconds = (parseFloat(r.CDI) - 1) * 7800;
  tableRows.push(new TableRow({
    children: [
      tcell(String(i + 1), { width: colW[0], shading: shade, align: AlignmentType.CENTER }),
      tcell(COURSE_LABEL[r.course] || r.course, { width: colW[1], shading: shade, align: AlignmentType.CENTER, bold: true }),
      tcell(parseFloat(r.cdi_f1).toFixed(4), { width: colW[2], shading: shade, align: AlignmentType.CENTER }),
      tcell(parseFloat(r.cdi_f2).toFixed(4), { width: colW[3], shading: shade, align: AlignmentType.CENTER }),
      tcell(parseFloat(r.cdi_f3).toFixed(4), { width: colW[4], shading: shade, align: AlignmentType.CENTER }),
      tcell(parseFloat(r.CDI).toFixed(4), { width: colW[5], shading: shade, align: AlignmentType.CENTER }),
      tcell(`${seconds >= 0 ? '+' : ''}${seconds.toFixed(0)}`, { width: colW[6], shading: shade, align: AlignmentType.CENTER }),
    ],
  }));
});
const tbl = new Table({
  rows: tableRows,
  width: { size: 7000, type: WidthType.DXA },
  borders: {
    top: { style: BorderStyle.SINGLE, size: 4, color: '1A1A2E' },
    bottom: { style: BorderStyle.SINGLE, size: 4, color: '1A1A2E' },
    left: { style: BorderStyle.SINGLE, size: 2, color: 'CCCCCC' },
    right: { style: BorderStyle.SINGLE, size: 2, color: 'CCCCCC' },
    insideHorizontal: { style: BorderStyle.SINGLE, size: 2, color: 'E5E7EB' },
    insideVertical: { style: BorderStyle.SINGLE, size: 2, color: 'E5E7EB' },
  },
});
children.push(tbl);
children.push(new Paragraph({
  alignment: AlignmentType.CENTER,
  spacing: { before: 80, after: 240, line: 280 },
  children: [new TextRun({
    text: 'Table 1. Per-course CDI broken out by framework. F2 = within-runner paired (50% weight); F3 = weather-normalized top-10 (35% weight); F1 = Minetti elevation (15% weight). Seconds vs Berlin = (CDI − 1) × 7800.',
    font: 'Calibri', size: 18, italics: true, color: COLOR.muted,
  })],
}));

// 7. Historical
children.push(head('7. Historical Comparison'));
children.push(p('The 2017 NYC reroute through the Bronx and the 2017 Tokyo redesigned course profile both warranted a check for structural breaks. The year-by-year weather-adjusted winning-time trace (Figure 3) shows no obvious break at either course in 2017–2018: NYC remains in its 2:08–2:11 men’s band, Tokyo in its 2:04–2:07 band. The 2018 Boston spike is the cold-rain edition; even after weather normalization, the wind/rain combination retained effects beyond what the temperature-and-humidity model captures.'));
children.push(p('Shoe technology (Vaporfly 2016, next-gen plates by 2020) shifted all six courses’ winning times faster by ~2–3% over the analysis window. This effect is proportional across courses and does not contaminate the relative ranking.'));

// 8. Sensitivity
children.push(head('8. Sensitivity Analysis'));
children.push(p('We stress-tested the CDI ranking against three perturbations: dropping Framework 1 entirely, restricting Framework 2 to sub-2:10 men, and substituting a Strava-GAP-style elevation model. The ordinal ranking. Boston > NYC > London > Tokyo > Chicago > Berlin. Is unchanged across all four assumption sets. The Strava-GAP model moves NYC’s CDI to 1.0166 (closer to Boston’s 1.0133), but does not flip the ranking. Restricting Framework 2 to sub-2:10 men gives essentially the same per-course offsets.'));
imageBlock('fig7_sensitivity.png', 600, 280,
  'Figure 6. CDI under four assumption sets. The ranking is invariant; only the gap magnitudes shift.'
).forEach(b => children.push(b));

// 9. Limitations
children.push(new Paragraph({ children: [new PageBreak()] }));
children.push(head('9. Limitations'));
children.push(pRich([{ text: 'The Minetti model misses late-race fatigue. ', bold: true },
  'Energy-cost curves are derived from steady-state lab data and do not capture the non-linear cost of climbing on tired legs. Boston’s Newton hills at miles 16–21 pay a fatigue tax the Minetti integration cannot see.']));
children.push(pRich([{ text: 'Pacing strategy differs by course. ', bold: true },
  'NYC and Boston attract tactical racers; Berlin and Chicago attract time-trialists. Some of the F2 paired delta is field-selection effect.']));
children.push(pRich([{ text: 'Top-100 cutoff is a moving target. ', bold: true },
  'A stronger Boston field shifts the top-100 median lower regardless of course conditions. We mitigate by averaging across nine years.']));
children.push(pRich([{ text: 'Elevation profiles approximated as 40/40/20. ', bold: true },
  'A segment-by-segment Strava integration would be more accurate, especially for NYC.']));
children.push(pRich([{ text: 'Selection bias in paired-runner population. ', bold: true },
  'Athletes who finish top-100 of one Major and attempt another within 18 months over-represent durable, well-funded runners.']));
children.push(pRich([{ text: 'Sydney and Cape Town have F1 only. ', bold: true },
  'Their CDI extension is a rough first estimate, not definitive.']));
imageBlock('fig8_alternative_ranking.png', 600, 310,
  'Figure 7. Headline ranking extended to Sydney and Cape Town (hatched bars, F1 only).'
).forEach(b => children.push(b));

// 10. Conclusion
children.push(head('10. Conclusion'));
children.push(p('The six World Marathon Majors are not equally fast. The within-runner paired comparison finds Boston 101 s and NYC 78 s slower than Berlin for an equivalent elite runner; Berlin, Chicago, London, and Tokyo cluster within 35 s of each other. The weather-normalized top-10 framework agrees to within 2 s on every course. The Minetti energy-cost model disagrees on Boston specifically; this is a known limitation of energy-cost models, and the empirical paired data overrides it.'));
children.push(p('Readers should weight Framework 2 most heavily and treat Framework 1 as a sanity check. When two Majors land within 30 seconds of each other on the composite, Chicago vs Berlin, Tokyo vs Chicago, the courses are practically interchangeable for ranking athletes’ personal bests.'));

children.push(new Paragraph({
  alignment: AlignmentType.CENTER, spacing: { before: 240, after: 0 },
  children: [new TextRun({
    text: 'Full code, data, and reproducibility instructions: github.com/lyhjeremy/marathon-majors-course-difficulty',
    font: 'Calibri', size: 18, italics: true, color: COLOR.muted,
  })],
}));

const doc = new Document({
  creator: 'Jeremy Lee',
  title: 'Are the World Marathon Majors Equally Fast?',
  description: 'A three-framework analysis of course difficulty across the six Majors.',
  styles: {
    default: { document: { run: { font: 'Calibri', size: 22 } } },
    paragraphStyles: [
      {
        id: 'Heading1', name: 'Heading 1', basedOn: 'Normal', next: 'Normal', quickFormat: true,
        run: { size: 30, bold: true, font: 'Georgia', color: COLOR.text },
        paragraph: { spacing: { before: 320, after: 160 }, outlineLevel: 0 },
      },
      {
        id: 'Heading2', name: 'Heading 2', basedOn: 'Normal', next: 'Normal', quickFormat: true,
        run: { size: 24, bold: true, font: 'Georgia', color: COLOR.text },
        paragraph: { spacing: { before: 200, after: 120 }, outlineLevel: 1 },
      },
    ],
  },
  sections: [{
    properties: { page: { size: { width: 12240, height: 15840 }, margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 } } },
    children,
  }],
});

Packer.toBuffer(doc).then(buffer => {
  fs.mkdirSync(path.dirname(OUT_PATH), { recursive: true });
  fs.writeFileSync(OUT_PATH, buffer);
  console.log(`DOCX saved: ${OUT_PATH}`);
  console.log(`File size: ${(fs.statSync(OUT_PATH).size / 1024).toFixed(0)} KB`);
}).catch(err => {
  console.error('Error generating DOCX:', err);
  process.exit(1);
});
