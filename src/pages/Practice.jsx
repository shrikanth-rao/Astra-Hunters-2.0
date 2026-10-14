import { useEffect, useRef, useState } from "react";
import "./Practice.css";

const SpeechRecognitionAPI =
  window.SpeechRecognition || window.webkitSpeechRecognition;

function estimatePitch(buffer, sampleRate) {
  // Lightweight autocorrelation pitch estimate. Returns Hz, or null for silence/noisy frames.
  let rms = 0;
  for (let i = 0; i < buffer.length; i++) rms += buffer[i] * buffer[i];
  rms = Math.sqrt(rms / buffer.length);
  if (rms < 0.012) return null;

  let bestOffset = -1;
  let bestCorrelation = 0;
  const minHz = 70;
  const maxHz = 350;
  const minOffset = Math.floor(sampleRate / maxHz);
  const maxOffset = Math.min(
    Math.floor(sampleRate / minHz),
    buffer.length - 1
  );

  for (let offset = minOffset; offset <= maxOffset; offset++) {
    let correlation = 0;
    const limit = buffer.length - offset;
    for (let i = 0; i < limit; i++) {
      correlation += buffer[i] * buffer[i + offset];
    }
    correlation /= limit;

    if (correlation > bestCorrelation) {
      bestCorrelation = correlation;
      bestOffset = offset;
    }
  }

  if (bestOffset < 0 || bestCorrelation < 0.01) return null;
  return Math.round(sampleRate / bestOffset);
}

function formatTime(totalSeconds) {
  const seconds = Math.max(0, Math.floor(totalSeconds));
  const minutes = Math.floor(seconds / 60);
  const remainder = seconds % 60;
  return `${String(minutes).padStart(2, "0")}:${String(remainder).padStart(2, "0")}`;
}

export default function Practice() {
  const [status, setStatus] = useState("idle");
  const [transcript, setTranscript] = useState("");
  const [interimTranscript, setInterimTranscript] = useState("");
  const [elapsed, setElapsed] = useState(0);
  const [waveBars, setWaveBars] = useState(Array(36).fill(5));
  const [pitchPoints, setPitchPoints] = useState([]);
  const [currentPitch, setCurrentPitch] = useState(null);
  const [averagePitch, setAveragePitch] = useState(null);
  const [pauseMessage, setPauseMessage] = useState("");
  const [pauseCount, setPauseCount] = useState(0);
  const [error, setError] = useState("");
  const [summary, setSummary] = useState(null);

  const activeRef = useRef(false);
  const recognitionRef = useRef(null);
  const streamRef = useRef(null);
  const audioContextRef = useRef(null);
  const analyserRef = useRef(null);
  const animationRef = useRef(null);
  const startedAtRef = useRef(0);
  const silenceStartedRef = useRef(null);
  const pauseShownRef = useRef(false);
  const pitchSamplesRef = useRef([]);
  const finalTranscriptRef = useRef("");
  const interimTranscriptRef = useRef("");
  const pauseCountRef = useRef(0);

  useEffect(() => {
    return () => {
      activeRef.current = false;
      if (recognitionRef.current) {
        recognitionRef.current.onend = null;
        try {
          recognitionRef.current.stop();
        } catch {}
      }
      if (animationRef.current) cancelAnimationFrame(animationRef.current);
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((track) => track.stop());
      }
      if (audioContextRef.current) {
        audioContextRef.current.close().catch(() => {});
      }
    };
  }, []);

  function setupSpeechRecognition() {
    if (!SpeechRecognitionAPI) {
      throw new Error(
        "Live speech-to-text is not supported by this browser. Try Google Chrome."
      );
    }

    const recognition = new SpeechRecognitionAPI();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = "en-IN";

    recognition.onresult = (event) => {
      let finalText = "";
      let interimText = "";

      for (let i = 0; i < event.results.length; i++) {
        const result = event.results[i];
        const text = result[0]?.transcript || "";
        if (result.isFinal) finalText += `${text} `;
        else interimText += text;
      }

      // The browser returns the full result list on updates. Rebuild the transcript
      // from that list to avoid duplicating recognized words.
      const allFinal = [];
      let allInterim = [];
      for (let i = 0; i < event.results.length; i++) {
        const result = event.results[i];
        const text = result[0]?.transcript || "";
        if (result.isFinal) allFinal.push(text.trim());
        else allInterim.push(text.trim());
      }

      finalTranscriptRef.current = allFinal.filter(Boolean).join(" ").trim();
      interimTranscriptRef.current = allInterim.filter(Boolean).join(" ").trim();
      setTranscript(finalTranscriptRef.current);
      setInterimTranscript(interimTranscriptRef.current);
    };

    recognition.onerror = (event) => {
      if (event.error !== "no-speech" && event.error !== "aborted") {
        setError(
          event.error === "not-allowed"
            ? "Microphone permission was denied. Allow microphone access in your browser."
            : `Speech recognition error: ${event.error}`
        );
      }
    };

    recognition.onend = () => {
      if (activeRef.current) {
        try {
          recognition.start();
        } catch {
          // The browser may still be transitioning between recognition sessions.
        }
      }
    };

    recognitionRef.current = recognition;
    recognition.start();
  }

  async function startPractice() {
    setError("");
    setSummary(null);
    setTranscript("");
    setInterimTranscript("");
    setElapsed(0);
    setWaveBars(Array(36).fill(5));
    setPitchPoints([]);
    setCurrentPitch(null);
    setAveragePitch(null);
    setPauseMessage("");
    setPauseCount(0);
    pitchSamplesRef.current = [];
    finalTranscriptRef.current = "";
    interimTranscriptRef.current = "";
    pauseCountRef.current = 0;
    silenceStartedRef.current = null;
    pauseShownRef.current = false;

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;

      const AudioContextAPI = window.AudioContext || window.webkitAudioContext;
      const audioContext = new AudioContextAPI();
      audioContextRef.current = audioContext;
      await audioContext.resume();

      const source = audioContext.createMediaStreamSource(stream);
      const analyser = audioContext.createAnalyser();
      analyser.fftSize = 2048;
      analyser.smoothingTimeConstant = 0.65;
      source.connect(analyser);
      analyserRef.current = analyser;

      activeRef.current = true;
      startedAtRef.current = Date.now();
      setStatus("recording");
      setupSpeechRecognition();

      const buffer = new Float32Array(analyser.fftSize);

      const updateAudio = () => {
        if (!activeRef.current || !analyserRef.current) return;

        analyserRef.current.getFloatTimeDomainData(buffer);

        let sumSquares = 0;
        for (let i = 0; i < buffer.length; i++) {
          sumSquares += buffer[i] * buffer[i];
        }
        const rms = Math.sqrt(sumSquares / buffer.length);
        const level = Math.min(100, Math.round(rms * 420));
        setWaveBars((previous) => [
          ...previous.slice(1),
          Math.max(4, level),
        ]);

        const pitch = estimatePitch(buffer, audioContext.sampleRate);

        if (rms < 0.012) {
          if (silenceStartedRef.current === null) {
            silenceStartedRef.current = Date.now();
          }

          const silenceDuration = Date.now() - silenceStartedRef.current;
          if (silenceDuration >= 1500 && !pauseShownRef.current) {
            pauseShownRef.current = true;
            pauseCountRef.current += 1;
            setPauseCount(pauseCountRef.current);
            setPauseMessage("You paused speaking. Continue when you're ready.");
          }
        } else {
          silenceStartedRef.current = null;
          pauseShownRef.current = false;
          setPauseMessage("");
        }

        if (pitch !== null && rms >= 0.012) {
          pitchSamplesRef.current.push(pitch);
          setCurrentPitch(pitch);
          setPitchPoints((previous) => [
            ...previous.slice(-59),
            pitch,
          ]);
          const samples = pitchSamplesRef.current;
          setAveragePitch(
            Math.round(samples.reduce((total, value) => total + value, 0) / samples.length)
          );
        } else {
          setCurrentPitch(null);
          setPitchPoints((previous) => [...previous.slice(-59), null]);
        }

        setElapsed(Math.floor((Date.now() - startedAtRef.current) / 1000));
        animationRef.current = requestAnimationFrame(updateAudio);
      };

      animationRef.current = requestAnimationFrame(updateAudio);
    } catch (err) {
      activeRef.current = false;
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((track) => track.stop());
        streamRef.current = null;
      }
      if (audioContextRef.current) {
        await audioContextRef.current.close().catch(() => {});
        audioContextRef.current = null;
      }
      setStatus("idle");
      setError(
        err.name === "NotAllowedError"
          ? "Microphone access was blocked. Allow it in your browser and try again."
          : err.message || "Could not start microphone recording."
      );
    }
  }

  async function endPractice() {
    if (!activeRef.current) return;

    activeRef.current = false;
    setStatus("finished");

    if (animationRef.current) cancelAnimationFrame(animationRef.current);

    if (recognitionRef.current) {
      recognitionRef.current.onend = null;
      try {
        recognitionRef.current.stop();
      } catch {}
    }

    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }

    if (audioContextRef.current) {
      await audioContextRef.current.close().catch(() => {});
      audioContextRef.current = null;
    }

    const fullTranscript = [
      finalTranscriptRef.current,
      interimTranscriptRef.current,
    ]
      .filter(Boolean)
      .join(" ")
      .trim();

    const durationSeconds = Math.max(
      1,
      Math.floor((Date.now() - startedAtRef.current) / 1000)
    );
    const wordCount = fullTranscript
      ? fullTranscript.split(/\s+/).filter(Boolean).length
      : 0;
    const wordsPerMinute = Math.round((wordCount / durationSeconds) * 60);
    const samples = pitchSamplesRef.current;
    const meanPitch = samples.length
      ? Math.round(samples.reduce((total, value) => total + value, 0) / samples.length)
      : null;

    setTranscript(fullTranscript);
    setInterimTranscript("");
    setElapsed(durationSeconds);
    setAveragePitch(meanPitch);
    setSummary({
      transcript: fullTranscript,
      durationSeconds,
      wordCount,
      wordsPerMinute,
      averagePitch: meanPitch,
      pauseCount: pauseCountRef.current,
      pitchSamples: samples.length,
    });
  }

  const displayedTranscript = [transcript, interimTranscript]
    .filter(Boolean)
    .join(" ");

  const pitchPolyline = pitchPoints
    .map((pitch, index) => {
      const x = pitchPoints.length <= 1
        ? 0
        : (index / (pitchPoints.length - 1)) * 600;
      const boundedPitch = pitch == null ? 210 : Math.max(70, Math.min(350, pitch));
      const y = 190 - ((boundedPitch - 70) / (350 - 70)) * 160;
      return `${x},${y}`;
    })
    .join(" ");

  return (
    <main className="quick-practice-page">
      <header className="practice-heading">
        <p className="practice-eyebrow">SPEAKKARO.AI</p>
        <h1>Quick Audio Practice</h1>
        <p>
          Practice speaking freely. Watch your transcript and voice pitch live.
          This session is temporary and is not saved to your account.
        </p>
      </header>

      {error && <div className="practice-error" role="alert">{error}</div>}

      <section className="practice-control-panel">
        <div className={`practice-status ${status}`}>
          <span className="practice-status-dot" />
          {status === "recording"
            ? "Recording"
            : status === "finished"
              ? "Session ended"
              : "Ready to practise"}
        </div>

        <div className="practice-timer">{formatTime(elapsed)}</div>

        <div className="practice-controls">
          {status !== "recording" ? (
            <button
              type="button"
              className="practice-start-button"
              onClick={startPractice}
            >
              <span aria-hidden="true">●</span>
              {status === "finished" ? "Start new practice" : "Start practice"}
            </button>
          ) : (
            <button
              type="button"
              className="practice-end-button"
              onClick={endPractice}
            >
              End practice
            </button>
          )}
        </div>

        {status === "recording" && (
          <p className="practice-hint">
            Speak naturally. Your transcript and pitch update while you talk.
          </p>
        )}
      </section>

      <section className="practice-grid">
        <article className="practice-panel transcript-panel">
          <div className="practice-panel-heading">
            <div>
              <h2>Live transcript</h2>
              <p>Speech-to-text preview</p>
            </div>
            <span className="practice-live-tag">
              {status === "recording" ? "LIVE" : "TEXT"}
            </span>
          </div>

          <div className="practice-transcript">
            {displayedTranscript ? (
              <>
                {transcript}
                {interimTranscript && (
                  <span className="practice-interim">
                    {transcript ? " " : ""}{interimTranscript}
                  </span>
                )}
              </>
            ) : (
              <span className="practice-placeholder">
                Your words will appear here when you start speaking...
              </span>
            )}
          </div>

          {pauseMessage && status === "recording" && (
            <div className="practice-pause-message" role="status">
              {pauseMessage}
            </div>
          )}
        </article>

        <article className="practice-panel">
          <div className="practice-panel-heading">
            <div>
              <h2>Voice activity</h2>
              <p>Live microphone volume</p>
            </div>
          </div>

          <div className="practice-wave" aria-label="Live audio volume bars">
            {waveBars.map((height, index) => (
              <span
                key={index}
                style={{ height: `${Math.max(5, Math.min(100, height))}%` }}
              />
            ))}
          </div>

          <div className="practice-volume-caption">
            {status === "recording"
              ? "Listening to microphone"
              : "Start a session to view audio activity"}
          </div>
        </article>
      </section>

      <section className="practice-panel practice-pitch-panel">
        <div className="practice-panel-heading">
          <div>
            <h2>Live pitch graph</h2>
            <p>Estimated fundamental frequency over time</p>
          </div>
          <div className="practice-pitch-value">
            <strong>{currentPitch ?? "--"}</strong>
            <span>Hz</span>
          </div>
        </div>

        <div className="practice-pitch-chart">
          <div className="practice-pitch-axis">
            <span>350 Hz</span>
            <span>210 Hz</span>
            <span>70 Hz</span>
          </div>
          <svg
            viewBox="0 0 600 200"
            preserveAspectRatio="none"
            role="img"
            aria-label="Estimated pitch graph"
          >
            <line x1="0" y1="30" x2="600" y2="30" />
            <line x1="0" y1="110" x2="600" y2="110" />
            <line x1="0" y1="190" x2="600" y2="190" />
            {pitchPoints.length > 1 && (
              <polyline points={pitchPolyline} />
            )}
          </svg>
        </div>
        <div className="practice-chart-caption">
          {status === "recording"
            ? "Graph updates continuously while your voice is detected."
            : "Pitch values are estimated from voiced audio frames."}
        </div>
      </section>

      {summary && (
        <section className="practice-summary">
          <div className="practice-summary-heading">
            <div>
              <p className="practice-eyebrow">SESSION COMPLETE</p>
              <h2>Your quick practice summary</h2>
            </div>
            <button
              type="button"
              className="practice-secondary-button"
              onClick={() => {
                setSummary(null);
                setStatus("idle");
                setTranscript("");
                setInterimTranscript("");
                setElapsed(0);
                setPitchPoints([]);
                setCurrentPitch(null);
                setAveragePitch(null);
                setPauseCount(0);
                setPauseMessage("");
              }}
            >
              Clear session
            </button>
          </div>

          <div className="practice-summary-cards">
            <article>
              <span>Duration</span>
              <strong>{formatTime(summary.durationSeconds)}</strong>
            </article>
            <article>
              <span>Words recognised</span>
              <strong>{summary.wordCount}</strong>
            </article>
            <article>
              <span>Speaking pace</span>
              <strong>{summary.wordsPerMinute} WPM</strong>
            </article>
            <article>
              <span>Average estimated pitch</span>
              <strong>
                {summary.averagePitch == null
                  ? "Unavailable"
                  : `${summary.averagePitch} Hz`}
              </strong>
            </article>
            <article>
              <span>Detected pauses</span>
              <strong>{summary.pauseCount}</strong>
            </article>
          </div>

          <div className="practice-panel practice-summary-transcript">
            <h3>Final transcript</h3>
            <p>
              {summary.transcript ||
                "No transcript was recognised. Try speaking clearly and check microphone permission."}
            </p>
          </div>

          <p className="practice-privacy-note">
            This summary exists only in the current page session. It is not
            added to Progress or saved in browser storage.
          </p>
        </section>
      )}
    </main>
  );
}
