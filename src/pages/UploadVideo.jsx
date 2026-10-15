// import { useEffect, useRef, useState } from "react";
// import { useNavigate } from "react-router-dom";
// import { Upload, Video, RefreshCw, ArrowRight, FileVideo2, ShieldCheck } from "lucide-react";
// import "./UploadVideo.css";

// const MAX_FILE_SIZE_MB = 500;

// export default function UploadVideo() {
//   const [isAnalyzing, setIsAnalyzing] = useState(false);
//   const inputRef = useRef(null);
//   const navigate = useNavigate();
//   const [videoFile, setVideoFile] = useState(null);
//   const [videoUrl, setVideoUrl] = useState("");
//   const [error, setError] = useState("");

//   useEffect(() => () => {
//     if (videoUrl) URL.revokeObjectURL(videoUrl);
//   }, [videoUrl]);

//   function selectVideo(file) {
//     setError("");
//     if (!file) return;
//     if (!file.type.startsWith("video/")) {
//       setError("Please choose a video file, such as MP4, WebM, or MOV.");
//       return;
//     }
//     if (file.size > MAX_FILE_SIZE_MB * 1024 * 1024) {
//       setError(`Please choose a video smaller than ${MAX_FILE_SIZE_MB} MB.`);
//       return;
//     }
//     const nextUrl = URL.createObjectURL(file);
//     setVideoFile(file);
//     setVideoUrl(oldUrl => {
//       if (oldUrl) URL.revokeObjectURL(oldUrl);
//       return nextUrl;
//     });
//   }

//   function handleInputChange(event) {
//     selectVideo(event.target.files?.[0]);
//     event.target.value = "";
//   }

//   function handleDrop(event) {
//     event.preventDefault();
//     selectVideo(event.dataTransfer.files?.[0]);
//   }

//   function startAnalysis() {
//   if (!videoFile || isAnalyzing) return;

//   setIsAnalyzing(true);

//   setTimeout(() => {
//     navigate("/report", {
//       state: {
//         videoFile,
//         videoName: videoFile.name,
//         videoSize: videoFile.size,
//         previewUrl: videoUrl,
//       },
//     });
//   }, 2000);
// }

//   return isAnalyzing ? (
//   <div className="upload-analysis-state" role="status">
//     <div className="upload-loader"></div>
//     <h1>Analysing your presentation...</h1>
//     <p>Preparing your speech insights. Please wait.</p>
//   </div>
// ) : (
//     <section className="upload-page">
//       <div className="upload-page-heading">
//         <span className="upload-eyebrow">
//           <span className="upload-eyebrow-dot" />
//           SPEECH ANALYSIS STUDIO
//         </span>
//         <h1>Upload your Video</h1>
//         <p>Share a recording of your speech and let SpeakKaro.AI help you improve.</p>
//       </div>

//       {!videoFile ? (
//         <div
//           className="upload-dropzone"
//           role="button"
//           tabIndex={0}
//           aria-label="Choose a video to upload"
//           onClick={() => inputRef.current?.click()}
//           onKeyDown={event => {
//             if (event.key === "Enter" || event.key === " ") {
//               event.preventDefault();
//               inputRef.current?.click();
//             }
//           }}
//           onDragOver={event => event.preventDefault()}
//           onDrop={handleDrop}
//         >
//           <input
//             ref={inputRef}
//             className="upload-hidden-input"
//             type="file"
//             accept="video/*,.mp4,.webm,.mov,.m4v"
//             onChange={handleInputChange}
//           />
//           <div className="upload-icon-orbit" aria-hidden="true">
//             <div className="upload-icon-circle"><Upload size={34} strokeWidth={1.7} /></div>
//             <span className="upload-orbit-dot upload-orbit-dot-one" />
//             <span className="upload-orbit-dot upload-orbit-dot-two" />
//           </div>
//           <h2>Drop your video here</h2>
//           <p className="upload-dropzone-copy">or click below to browse files from your device</p>
//           <button
//             className="upload-choose-button"
//             type="button"
//             onClick={event => {
//               event.stopPropagation();
//               inputRef.current?.click();
//             }}
//           >
//             <FileVideo2 size={18} /> Choose Video
//           </button>
//           <p className="upload-file-hint">MP4, WebM or MOV · Up to {MAX_FILE_SIZE_MB} MB</p>
//         </div>
//       ) : (
//         <div className="upload-preview-card">
//           <div className="upload-preview-topline">
//             <div className="upload-preview-file-icon"><Video size={19} /></div>
//             <div className="upload-preview-file-info">
//               <h2 title={videoFile.name}>{videoFile.name}</h2>
//               <p>{formatFileSize(videoFile.size)} · Ready to analyse</p>
//             </div>
//             <span className="upload-ready-label"><span />Video ready</span>
//           </div>
//           <div className="upload-video-frame">
//             <video key={videoUrl} src={videoUrl} controls playsInline preload="metadata"
//               aria-label={`Preview of ${videoFile.name}`}>
//               Your browser does not support video playback.
//             </video>
//           </div>
//           <div className="upload-preview-actions">
//             <button type="button" className="upload-change-button"
//               onClick={() => inputRef.current?.click()}>
//               <RefreshCw size={17} /> Change Video
//             </button>
//             <input ref={inputRef} className="upload-hidden-input" type="file"
//               accept="video/*,.mp4,.webm,.mov,.m4v" onChange={handleInputChange} />
//             <button type="button" className="upload-analyze-button" onClick={startAnalysis}>
//               Start Analysis <ArrowRight size={18} />
//             </button>
//           </div>
//         </div>
//       )}

//       {error && <div className="upload-error" role="alert">{error}</div>}

//       <div className="upload-privacy-note">
//         <span className="upload-privacy-icon"><ShieldCheck size={19} /></span>
//         <span>
//           <strong>Your recording, your progress.</strong>
//           <small>Choose a clear recording with audible speech and your face visible when possible.</small>
//         </span>
//       </div>
//     </section>
//   );
// }

// function formatFileSize(bytes) {
//   if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`;
//   return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
// }






























import { useEffect, useRef, useState } from "react";
import {
  Upload,
  Video,
  RefreshCw,
  ArrowRight,
  FileVideo2,
  ShieldCheck,
  Save,
  CheckCircle2,
} from "lucide-react";
import { useData } from "../context/DataContext";
import "./UploadVideo.css";

const MAX_FILE_SIZE_MB = 500;

export default function UploadVideo() {
  const inputRef = useRef(null);

  const { currentUser, addSpeechResult } = useData();

  const [videoFile, setVideoFile] = useState(null);
  const [videoUrl, setVideoUrl] = useState("");
  const [videoDuration, setVideoDuration] = useState(0);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [report, setReport] = useState(null);
  const [speechName, setSpeechName] = useState("");
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    return () => {
      if (videoUrl) URL.revokeObjectURL(videoUrl);
    };
  }, [videoUrl]);

  function selectVideo(file) {
    setError("");

    if (!file) return;

    if (!file.type.startsWith("video/")) {
      setError("Please choose an MP4, WebM, or MOV video.");
      return;
    }

    if (file.size > MAX_FILE_SIZE_MB * 1024 * 1024) {
      setError(`Choose a video smaller than ${MAX_FILE_SIZE_MB} MB.`);
      return;
    }

    const nextUrl = URL.createObjectURL(file);

    setVideoFile(file);
    setVideoUrl(nextUrl);
    setVideoDuration(0);
    setReport(null);
    setSpeechName("");
    setSaved(false);
  }

  function handleInputChange(event) {
    selectVideo(event.target.files?.[0]);
    event.target.value = "";
  }

  function handleDrop(event) {
    event.preventDefault();
    selectVideo(event.dataTransfer.files?.[0]);
  }

  function startAnalysis() {
    if (!videoFile || isAnalyzing) return;

    setError("");
    setReport(null);
    setSaved(false);
    setIsAnalyzing(true);

    // DEMO ONLY: These metrics are placeholders.
    // They are not calculated from the video's speech.
    setTimeout(() => {
      const duration = Math.round(videoDuration || 120);
      const fillerWords = {
        um: 4,
        uh: 3,
        like: 2,
      };

      setReport({
        date: new Date().toISOString().slice(0, 10),
        score: 76,
        duration,
        pace: 145,
        fillerCount: Object.values(fillerWords).reduce(
          (total, count) => total + count,
          0
        ),
        fillerWords,
        pauseCount: 5,
        transcript:
          "Real speech transcription will be connected later.",
        averagePitch: 180,
        pitchVariation: "Moderate",
        eyeContact: "70%",
        posture: "Upright",
        drawbacks: [
          "Some filler words detected (demo)",
          "Try varying your vocal tone (demo)",
          "Practise deliberate pauses (demo)",
        ],
        feedback:
          "feedback: practise a steady speaking pace, reduce filler words, and use vocal variation.",
      });

      setIsAnalyzing(false);
    }, 10000);
  }

  function saveReport() {
    if (!currentUser?.gmail) {
      setError("Please log in before saving your analysis.");
      return;
    }

    if (!report) {
      setError("No analysis result is available to save.");
      return;
    }

    if (!speechName.trim()) {
      setError("Please enter a name for your speech.");
      return;
    }

    addSpeechResult(currentUser.gmail, {
      ...report,
      title: speechName.trim(),
    });

    setSaved(true);
    setError("");
  }

  function resetAnalysis() {
    setReport(null);
    setSpeechName("");
    setSaved(false);
    setError("");
  }

  return (
    <section className="upload-page">
      <div className="upload-page-heading">
        <span className="upload-eyebrow">
          <span className="upload-eyebrow-dot" />
          SPEECH ANALYSIS STUDIO
        </span>

        <h1>Upload your Video</h1>
        <p>
          Share a recording of your speech and let SpeakKaro.AI help you improve.
        </p>
      </div>

      {!videoFile ? (
        <div
          className="upload-dropzone"
          role="button"
          tabIndex={0}
          aria-label="Choose a video to upload"
          onClick={() => inputRef.current?.click()}
          onKeyDown={(event) => {
            if (event.key === "Enter" || event.key === " ") {
              event.preventDefault();
              inputRef.current?.click();
            }
          }}
          onDragOver={(event) => event.preventDefault()}
          onDrop={handleDrop}
        >
          <input
            ref={inputRef}
            className="upload-hidden-input"
            type="file"
            accept="video/*,.mp4,.webm,.mov,.m4v"
            onChange={handleInputChange}
          />

          <div className="upload-icon-orbit" aria-hidden="true">
            <div className="upload-icon-circle">
              <Upload size={34} strokeWidth={1.7} />
            </div>
            <span className="upload-orbit-dot upload-orbit-dot-one" />
            <span className="upload-orbit-dot upload-orbit-dot-two" />
          </div>

          <h2>Drop your video here</h2>
          <p className="upload-dropzone-copy">
            Or click below to browse files from your device
          </p>

          <button
            className="upload-choose-button"
            type="button"
            onClick={(event) => {
              event.stopPropagation();
              inputRef.current?.click();
            }}
          >
            <FileVideo2 size={18} /> Choose Video
          </button>

          <p className="upload-file-hint">
            MP4, WebM or MOV · Up to {MAX_FILE_SIZE_MB} MB
          </p>
        </div>
      ) : (
        <div className="upload-preview-card">
          <div className="upload-preview-topline">
            <div className="upload-preview-file-icon">
              <Video size={19} />
            </div>

            <div className="upload-preview-file-info">
              <h2 title={videoFile.name}>{videoFile.name}</h2>
              <p>{formatFileSize(videoFile.size)} · Ready to analyse</p>
            </div>

            <span className="upload-ready-label">
              <span /> Video ready
            </span>
          </div>

          <div className="upload-video-frame">
            <video
              key={videoUrl}
              src={videoUrl}
              controls
              playsInline
              preload="metadata"
              onLoadedMetadata={(event) => {
                const duration = event.currentTarget.duration;
                if (Number.isFinite(duration)) {
                  setVideoDuration(duration);
                }
              }}
              aria-label={`Preview of ${videoFile.name}`}
            >
              Your browser does not support video playback.
            </video>
          </div>

          <div className="upload-preview-actions">
            <button
              type="button"
              className="upload-change-button"
              onClick={() => inputRef.current?.click()}
              disabled={isAnalyzing}
            >
              <RefreshCw size={17} /> Change Video
            </button>

            <input
              ref={inputRef}
              className="upload-hidden-input"
              type="file"
              accept="video/*,.mp4,.webm,.mov,.m4v"
              onChange={handleInputChange}
            />

            <button
              type="button"
              className="upload-analyze-button"
              onClick={startAnalysis}
              disabled={isAnalyzing || saved}
            >
              {isAnalyzing ? "Analysing..." : "Start Analysis"}
              <ArrowRight size={18} />
            </button>
          </div>
        </div>
      )}

      {isAnalyzing && (
        <div className="upload-analysis-state" role="status">
          <div className="upload-loader" />
          <h2>Preparing your report...</h2>
          <p>Please wait while the demo analysis is generated.</p>
        </div>
      )}

      {error && (
        <div className="upload-error" role="alert">
          {error}
        </div>
      )}

      {report && (
        <div className="speech-report">
          <div className="speech-report-heading">
            <span className="upload-eyebrow">YOUR SPEECH REPORT</span>
            <h2>Analysis Results</h2>
            <p>
              Results are shown below. Enter your own speech name before saving.
            </p>
          </div>

          <div className="speech-demo-notice">
            {/* Demo results only. The metrics below are sample values, not */}
            {/* measurements extracted from your uploaded video. */}
          </div>

          <div className="speech-metrics-grid">
            <Metric label="Overall score" value={`${report.score}/100`} />
            <Metric label="Duration" value={formatDuration(report.duration)} />
            <Metric label="Speaking pace" value={`${report.pace} WPM`} />
            <Metric label="Filler words" value={report.fillerCount} />
            <Metric label="Pauses" value={report.pauseCount} />
            <Metric label="Average pitch" value={`${report.averagePitch} Hz`} />
          </div>

          <div className="speech-report-section">
            <h3>Filler word breakdown</h3>
            <div className="speech-filler-list">
              {Object.entries(report.fillerWords).map(([word, count]) => (
                <div className="speech-filler-row" key={word}>
                  <span>{word}</span>
                  <strong>{count}</strong>
                </div>
              ))}
            </div>
          </div>

          <div className="speech-report-section">
            <h3>Transcript</h3>
            <p className="speech-transcript">{report.transcript}</p>
          </div>

          <div className="speech-report-section">
            <h3>Delivery observations</h3>
            <div className="speech-observation-grid">
              <p>
                <span>Pitch variation</span>
                <strong>{report.pitchVariation}</strong>
              </p>
              <p>
                <span>Eye contact</span>
                <strong>{report.eyeContact}</strong>
              </p>
              <p>
                <span>Posture</span>
                <strong>{report.posture}</strong>
              </p>
            </div>
          </div>

          <div className="speech-report-section">
            <h3>Areas to improve</h3>
            <ul className="speech-drawbacks">
              {report.drawbacks.map((item, index) => (
                <li key={index}>{item}</li>
              ))}
            </ul>
            <h3>Feedback</h3>
            <p className="speech-feedback">{report.feedback}</p>
          </div>

          {!saved ? (
            <div className="speech-save-panel">
              <label htmlFor="speech-name">Name your speech</label>
              <input
                id="speech-name"
                type="text"
                value={speechName}
                onChange={(event) => setSpeechName(event.target.value)}
                placeholder="e.g. Introduction to Artificial Intelligence"
                maxLength={100}
              />

              <button
                type="button"
                className="speech-save-button"
                onClick={saveReport}
              >
                <Save size={18} /> Save Analysis
              </button>
            </div>
          ) : (
            <div className="speech-saved-message" role="status">
              <CheckCircle2 size={22} />
              <div>
                <strong>Analysis saved successfully!</strong>
                <p>
                  “{speechName.trim()}” has been added to your progress.
                </p>
              </div>
            </div>
          )}

          {saved && (
            <button
              type="button"
              className="upload-change-button"
              onClick={resetAnalysis}
            >
              Analyse another video
            </button>
          )}
        </div>
      )}

      <div className="upload-privacy-note">
        <span className="upload-privacy-icon">
          <ShieldCheck size={19} />
        </span>
        <span>
          <strong>Your recording, your progress.</strong>
          <small>
            Choose a clear recording with audible speech and your face visible
            when possible.
          </small>
        </span>
      </div>
    </section>
  );
}

function Metric({ label, value }) {
  return (
    <div className="speech-metric-card">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function formatFileSize(bytes) {
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function formatDuration(seconds) {
  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = Math.round(seconds % 60);
  return `${minutes}:${String(remainingSeconds).padStart(2, "0")}`;
}
