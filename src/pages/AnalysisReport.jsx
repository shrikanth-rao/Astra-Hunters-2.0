import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useData } from "../context/DataContext";
import "./AnalysisReport.css";

export default function AnalysisReport() {
  const navigate = useNavigate();

  const {
    currentUser,
    pendingAnalysis,
    setPendingAnalysis,
    addSpeechResult,
  } = useData();

  const [speechName, setSpeechName] = useState("");
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState("");

  const report = pendingAnalysis;

  const formatDuration = (seconds = 0) => {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;

    return `${minutes}m ${String(remainingSeconds).padStart(2, "0")}s`;
  };

  const handleSave = () => {
    const trimmedName = speechName.trim();

    if (!trimmedName) {
      setError("Please enter a name for your speech.");
      return;
    }

    if (!currentUser?.gmail) {
      setError("Please log in before saving your report.");
      return;
    }

    if (!report) {
      setError("No analysis result found. Please analyse a video first.");
      return;
    }

    addSpeechResult(currentUser.gmail, {
      ...report,
      title: trimmedName,
      date: report.date || new Date().toISOString().slice(0, 10),
    });

    setSaved(true);
    setPendingAnalysis(null);
  };

  if (!report && !saved) {
    return (
      <main className="analysis-report">
        <section className="report-empty">
          <h2>No analysis available</h2>
          <p>Upload a video and analyse your speech to see your report.</p>
          <button onClick={() => navigate("/practice")}>
            Back to video upload
          </button>
        </section>
      </main>
    );
  }

  if (saved) {
    return (
      <main className="analysis-report">
        <section className="report-success">
          <div className="success-icon">✓</div>
          <p className="report-eyebrow">REPORT SAVED</p>
          <h1>Speech saved successfully</h1>
          <p>
            Your report for <strong>{speechName.trim()}</strong> has been
            added to your progress.
          </p>

          <div className="report-actions">
            <button
              className="report-button report-button-primary"
              onClick={() => navigate("/progress")}
            >
              View my progress
            </button>

            <button
              className="report-button report-button-secondary"
              onClick={() => navigate("/practice")}
            >
              Analyse another video
            </button>
          </div>
        </section>
      </main>
    );
  }

  return (
    <main className="analysis-report">
      <header className="report-header">
        <div>
          <p className="report-eyebrow">SPEAKAI / ANALYSIS</p>
          <h1>Speech analysis report</h1>
          <p className="report-subtitle">
            Review your demo results and save this session to your progress.
          </p>
        </div>

        <span className="demo-badge">DEMO DATA</span>
      </header>

      <section className="speech-name-card">
        <label htmlFor="speechName">Name your speech</label>
        <p>
          Enter a title you'll recognise later in your progress history.
        </p>

        <input
          id="speechName"
          type="text"
          value={speechName}
          onChange={(event) => {
            setSpeechName(event.target.value);
            setError("");
          }}
          placeholder="e.g. Introduction to Artificial Intelligence"
          maxLength={100}
        />

        {error && <p className="report-error">{error}</p>}

        <button
          className="report-button report-button-primary save-report-button"
          onClick={handleSave}
        >
          Save report
        </button>
      </section>

      <section className="report-score-card">
        <div>
          <p className="metric-label">OVERALL SCORE</p>
          <div className="overall-score">
            {report.score}
            <span>/100</span>
          </div>
          <p className="score-caption">Demo speaking score</p>
        </div>

        <div className="score-ring">
          <span>{report.score}%</span>
          <small>Score</small>
        </div>
      </section>

      <section className="report-metrics">
        <article className="metric-card">
          <span className="metric-label">PACE SCORE</span>
          <strong>{Math.min(100, Math.max(40, 100 - Math.abs(report.pace - 140)))}<small>/100</small></strong>
          <p>Estimated delivery pace</p>
        </article>

        <article className="metric-card">
          <span className="metric-label">SPEAKING PACE</span>
          <strong>{report.pace}</strong>
          <p>Words per minute</p>
        </article>

        <article className="metric-card">
          <span className="metric-label">FILLER WORDS</span>
          <strong>{report.fillerCount}</strong>
          <p>Total detected in demo</p>
        </article>

        <article className="metric-card">
          <span className="metric-label">PAUSES</span>
          <strong>{report.pauseCount}</strong>
          <p>Estimated pause count</p>
        </article>

        <article className="metric-card">
          <span className="metric-label">DURATION</span>
          <strong>{formatDuration(report.duration)}</strong>
          <p>Demo speech duration</p>
        </article>

        <article className="metric-card">
          <span className="metric-label">AVERAGE PITCH</span>
          <strong>{report.averagePitch}<small> Hz</small></strong>
          <p>Demo pitch estimate</p>
        </article>
      </section>

      <section className="report-panel">
        <h2>Filler word breakdown</h2>
        <p className="panel-description">
          Sample counts generated for this demo report.
        </p>

        <div className="filler-list">
          {Object.entries(report.fillerWords || {}).map(([word, count]) => (
            <div className="filler-row" key={word}>
              <span>{word}</span>
              <div className="filler-track">
                <div
                  className="filler-fill"
                  style={{
                    width: `${
                      report.fillerCount
                        ? Math.min(100, (count / report.fillerCount) * 100)
                        : 0
                    }%`,
                  }}
                />
              </div>
              <strong>{count}</strong>
            </div>
          ))}
        </div>
      </section>

      <section className="report-panel">
        <h2>Transcript</h2>
        <p className="panel-description">
          Sample transcript for the demo. It is not transcribed from your video.
        </p>
        <div className="transcript-box">{report.transcript}</div>
      </section>

      <section className="report-panel">
        <h2>Coaching feedback</h2>

        <div className="report-detail">
          <span>Pitch variation</span>
          <strong>{report.pitchVariation}</strong>
        </div>

        <div className="report-detail">
          <span>Eye contact</span>
          <strong>{report.eyeContact}</strong>
        </div>

        <div className="report-detail">
          <span>Posture</span>
          <strong>{report.posture}</strong>
        </div>

        <h3>Areas to improve</h3>
        <ul className="drawback-list">
          {report.drawbacks?.map((drawback, index) => (
            <li key={index}>{drawback}</li>
          ))}
        </ul>

        <div className="feedback-box">
          <strong>Recommendation</strong>
          <p>{report.feedback}</p>
        </div>
      </section>

      <footer className="report-footer">
        Demo values are randomly generated examples, not actual measurements
        of your uploaded video.
      </footer>
    </main>
  );
}