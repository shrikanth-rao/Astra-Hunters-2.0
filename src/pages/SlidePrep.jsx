import { useRef, useState } from "react";
import "./SlidePrep.css";

const API_URL = (import.meta.env.VITE_API_URL || "http://127.0.0.1:5000").replace(/\/$/, "");

export default function SlidePrep() {
  const inputRef = useRef(null);
  const [file, setFile] = useState(null);
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  function handleFileChange(event) {
    const chosen = event.target.files?.[0];
    setReport(null);
    setError("");
    if (!chosen) {
      setFile(null);
      return;
    }
    if (!chosen.name.toLowerCase().endsWith(".pptx")) {
      setFile(null);
      event.target.value = "";
      setError("Only .pptx PowerPoint files are accepted.");
      return;
    }
    setFile(chosen);
  }

  async function handleAnalyze() {
    if (!file) {
      setError("Upload a .pptx file before clicking Analyse.");
      return;
    }
    setLoading(true);
    setError("");
    setReport(null);
    const formData = new FormData();
    formData.append("file", file);
    try {
      const response = await fetch(`${API_URL}/api/analyze-ppt`, {
        method: "POST",
        body: formData,
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(data.error || `Request failed (${response.status}).`);
      if (!data.report) throw new Error("The server returned no analysis report.");
      setReport(data.report);
    } catch (err) {
      setError(`${err.message || "Could not connect to the backend."} Make sure Flask is running at ${API_URL}.`);
    } finally {
      setLoading(false);
    }
  }

  function handleReset() {
    setFile(null);
    setReport(null);
    setError("");
    setLoading(false);
    if (inputRef.current) inputRef.current.value = "";
  }

  return (
    <main className="slideprep-page">
      <section className="slideprep-hero">
        <p className="slideprep-eyebrow">SLIDE ANALYSIS</p>
        <h1>SlideReady</h1>
        <p className="slideprep-intro">Upload your PowerPoint to review slide structure, text density, font sizes, and practical improvements.</p>
      </section>

      <section className="slideprep-panel" aria-label="PowerPoint upload and analysis">
        <label className="slideprep-label" htmlFor="pptx-upload">PowerPoint file (.pptx only)</label>
        <input ref={inputRef} id="pptx-upload" className="slideprep-file" type="file" accept=".pptx,application/vnd.openxmlformats-officedocument.presentationml.presentation" onChange={handleFileChange} disabled={loading} />
        <p className="slideprep-file-hint">Maximum file size: 30 MB.</p>
        {file && <div className="slideprep-selected"><span className="slideprep-file-icon">PPT</span><div><strong>{file.name}</strong><span>{(file.size / (1024 * 1024)).toFixed(2)} MB</span></div></div>}
        <div className="slideprep-actions">
          <button className="slideprep-btn slideprep-primary" type="button" onClick={handleAnalyze} disabled={loading || !file}>{loading ? "Analyzing…" : "Analyse"}</button>
          <button className="slideprep-btn slideprep-secondary" type="button" onClick={handleReset} disabled={loading}>Reset</button>
        </div>
        {loading && <div className="slideprep-loading" role="status"><span className="slideprep-spinner" />Analyzing your presentation. This may take a few seconds…</div>}
        {error && <div className="slideprep-error" role="alert">{error}</div>}
      </section>

      {report && <section className="slideprep-results" aria-live="polite">
        <div className="slideprep-results-heading"><div><p className="slideprep-eyebrow">ANALYSIS COMPLETE</p><h2>{report.file_name}</h2></div><span className="slideprep-score">{report.average_basic_structure_score}<small>/100</small><em>Average structure score</em></span></div>
        <div className="slideprep-metrics">
          <Metric label="Slides" value={report.slide_count} />
          <Metric label="Words" value={report.total_word_count} />
          <Metric label="Words / slide" value={report.average_words_per_slide} />
          <Metric label="Images" value={report.total_images} />
          <Metric label="Charts" value={report.total_charts} />
          <Metric label="Tables" value={report.total_tables} />
        </div>
        <section className="slideprep-subsection"><h3>Overall findings</h3><ul>{report.overall_findings.map((item, index) => <li key={`${index}-${item}`}>{item}</li>)}</ul><p className="slideprep-note">{report.score_explanation}</p></section>
        <section className="slideprep-subsection"><h3>Slide-by-slide results</h3><div className="slideprep-slide-list">{report.slides.map((slide) => <article className="slideprep-slide" key={slide.slide_number}>
          <div className="slideprep-slide-top"><div><span className="slideprep-slide-number">SLIDE {slide.slide_number}</span><h4>{slide.title}</h4></div><span className={`slideprep-slide-score ${slide.basic_structure_score < 60 ? "is-low" : ""}`}>{slide.basic_structure_score}/100</span></div>
          <div className="slideprep-slide-stats"><span>{slide.word_count} words</span><span>{slide.sentence_count} sentences</span><span>Min font: {slide.minimum_font_size_pt == null ? "Not detected" : `${slide.minimum_font_size_pt} pt`}</span><span>{slide.image_count} images</span><span>{slide.chart_count} charts</span><span>{slide.table_count} tables</span></div>
          <div className="slideprep-columns"><div><h5>Findings</h5><ul>{slide.findings.map((item, index) => <li key={`${index}-${item}`}>{item}</li>)}</ul></div><div><h5>Suggestions</h5>{slide.suggestions.length ? <ul>{slide.suggestions.map((item, index) => <li key={`${index}-${item}`}>{item}</li>)}</ul> : <p>No specific recommendations.</p>}</div></div>
          {slide.extracted_text && <details className="slideprep-extracted"><summary>View extracted slide text</summary><pre>{slide.extracted_text}</pre></details>}
        </article>)}</div></section>
        <section className="slideprep-subsection"><h3>Repeated four-word phrases</h3>{report.repeated_four_word_phrases.length ? <ul>{report.repeated_four_word_phrases.map((item) => <li key={item.phrase}><strong>{item.phrase}</strong> <span>({item.count} occurrences)</span></li>)}</ul> : <p>No repeated four-word phrases detected.</p>}</section>
      </section>}
      <p className="slideprep-footnote">The score is a rule-based structural heuristic, not an AI judgement of design quality, factual accuracy, or persuasiveness.</p>
    </main>
  );
}

function Metric({ label, value }) {
  return <div className="slideprep-metric"><span>{label}</span><strong>{value ?? 0}</strong></div>;
}
