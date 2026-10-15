import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Upload, Video, RefreshCw, ArrowRight, FileVideo2, ShieldCheck } from "lucide-react";
import "./UploadVideo.css";

const MAX_FILE_SIZE_MB = 500;

export default function UploadVideo() {
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const inputRef = useRef(null);
  const navigate = useNavigate();
  const [videoFile, setVideoFile] = useState(null);
  const [videoUrl, setVideoUrl] = useState("");
  const [error, setError] = useState("");

  useEffect(() => () => {
    if (videoUrl) URL.revokeObjectURL(videoUrl);
  }, [videoUrl]);

  function selectVideo(file) {
    setError("");
    if (!file) return;
    if (!file.type.startsWith("video/")) {
      setError("Please choose a video file, such as MP4, WebM, or MOV.");
      return;
    }
    if (file.size > MAX_FILE_SIZE_MB * 1024 * 1024) {
      setError(`Please choose a video smaller than ${MAX_FILE_SIZE_MB} MB.`);
      return;
    }
    const nextUrl = URL.createObjectURL(file);
    setVideoFile(file);
    setVideoUrl(oldUrl => {
      if (oldUrl) URL.revokeObjectURL(oldUrl);
      return nextUrl;
    });
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

  setIsAnalyzing(true);

  setTimeout(() => {
    navigate("/report", {
      state: {
        videoFile,
        videoName: videoFile.name,
        videoSize: videoFile.size,
        previewUrl: videoUrl,
      },
    });
  }, 2000);
}

  return isAnalyzing ? (
  <div className="upload-analysis-state" role="status">
    <div className="upload-loader"></div>
    <h1>Analysing your presentation...</h1>
    <p>Preparing your speech insights. Please wait.</p>
  </div>
) : (
    <section className="upload-page">
      <div className="upload-page-heading">
        <span className="upload-eyebrow">
          <span className="upload-eyebrow-dot" />
          SPEECH ANALYSIS STUDIO
        </span>
        <h1>Upload your Video</h1>
        <p>Share a recording of your speech and let SpeakKaro.AI help you improve.</p>
      </div>

      {!videoFile ? (
        <div
          className="upload-dropzone"
          role="button"
          tabIndex={0}
          aria-label="Choose a video to upload"
          onClick={() => inputRef.current?.click()}
          onKeyDown={event => {
            if (event.key === "Enter" || event.key === " ") {
              event.preventDefault();
              inputRef.current?.click();
            }
          }}
          onDragOver={event => event.preventDefault()}
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
            <div className="upload-icon-circle"><Upload size={34} strokeWidth={1.7} /></div>
            <span className="upload-orbit-dot upload-orbit-dot-one" />
            <span className="upload-orbit-dot upload-orbit-dot-two" />
          </div>
          <h2>Drop your video here</h2>
          <p className="upload-dropzone-copy">or click below to browse files from your device</p>
          <button
            className="upload-choose-button"
            type="button"
            onClick={event => {
              event.stopPropagation();
              inputRef.current?.click();
            }}
          >
            <FileVideo2 size={18} /> Choose Video
          </button>
          <p className="upload-file-hint">MP4, WebM or MOV · Up to {MAX_FILE_SIZE_MB} MB</p>
        </div>
      ) : (
        <div className="upload-preview-card">
          <div className="upload-preview-topline">
            <div className="upload-preview-file-icon"><Video size={19} /></div>
            <div className="upload-preview-file-info">
              <h2 title={videoFile.name}>{videoFile.name}</h2>
              <p>{formatFileSize(videoFile.size)} · Ready to analyse</p>
            </div>
            <span className="upload-ready-label"><span />Video ready</span>
          </div>
          <div className="upload-video-frame">
            <video key={videoUrl} src={videoUrl} controls playsInline preload="metadata"
              aria-label={`Preview of ${videoFile.name}`}>
              Your browser does not support video playback.
            </video>
          </div>
          <div className="upload-preview-actions">
            <button type="button" className="upload-change-button"
              onClick={() => inputRef.current?.click()}>
              <RefreshCw size={17} /> Change Video
            </button>
            <input ref={inputRef} className="upload-hidden-input" type="file"
              accept="video/*,.mp4,.webm,.mov,.m4v" onChange={handleInputChange} />
            <button type="button" className="upload-analyze-button" onClick={startAnalysis}>
              Start Analysis <ArrowRight size={18} />
            </button>
          </div>
        </div>
      )}

      {error && <div className="upload-error" role="alert">{error}</div>}

      <div className="upload-privacy-note">
        <span className="upload-privacy-icon"><ShieldCheck size={19} /></span>
        <span>
          <strong>Your recording, your progress.</strong>
          <small>Choose a clear recording with audible speech and your face visible when possible.</small>
        </span>
      </div>
    </section>
  );
}

function formatFileSize(bytes) {
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}
