
import { useNavigate } from "react-router-dom";
import {
  Activity,
  ArrowRight,
  BarChart3,
  BookOpen,
  Clock3,
  FileVideo,
  History,
  LayoutDashboard,
  Mic2,
  Target,
} from "lucide-react";
import "../dashboard.css";

const team = [
  "Kiran",
  "Shrikanth Rao",
  "Gagan Nagesh",
  "Tharakhesh",
];

export default function Dashboard() {
  const navigate = useNavigate();

  const navItems = [
    { label: "Overview", icon: LayoutDashboard, path: "/dashboard" },
    { label: "New Analysis", icon: FileVideo, path: "/upload" },
    { label: "Detailed Final", icon: Target, path: "/detailed-final" },
    { label: "Practice Speech", icon: Mic2, path: "/practice" },
    { label: "History & Progress", icon: History, path: "/history" },
  ];

  return (
    <div className="voxa-app">
      <main className="voxa-main">
        <header className="voxa-topbar">
          <div>
            <p className="eyebrow">YOUR PERSONAL SPEECH COACH</p>
            <h2>Overview</h2>
          </div>
          <span className="status-label">
            <span className="status-dot" /> AI COACH
          </span>
        </header>

        <section className="welcome-panel">
          <div className="welcome-content">
            <span className="section-kicker">SPEAK WITH CONFIDENCE</span>
            <h1>Your voice.<br />Your ideas. <span>Your impact.</span></h1>
            <p>
              VOXA is an AI-powered public speaking assistant that helps you
              understand and improve the way you speak. Upload a presentation
              recording to review your transcript, speaking pace, filler words,
              pauses and pitch patterns, then use those insights to practise
              with purpose.
            </p>
            <button
              className="primary-button"
              onClick={() => navigate("/upload")}
            >
              Start a new analysis <ArrowRight size={18} />
            </button>
          </div>

          <div className="welcome-visual" aria-hidden="true">
            <div className="visual-orbit orbit-one" />
            <div className="visual-orbit orbit-two" />
            <div className="visual-core"><Mic2 size={54} /></div>
            <div className="visual-chip chip-top"><Activity size={17} /> Voice</div>
            <div className="visual-chip chip-bottom"><BarChart3 size={17} /> Insights</div>
          </div>
        </section>

        <section className="section-block">
          <div className="section-heading">
            <div>
              <p className="eyebrow">HOW IT WORKS</p>
              <h2>From recording to improvement</h2>
            </div>
          </div>

          <div className="workflow-grid">
            <article className="workflow-card">
              <span className="step-number">01</span>
              <FileVideo size={23} />
              <h3>Upload</h3>
              <p>Choose a recording of your speech or presentation.</p>
            </article>
            <article className="workflow-card">
              <span className="step-number">02</span>
              <Activity size={23} />
              <h3>Analyse</h3>
              <p>Extract speech metrics and a transcript from your recording.</p>
            </article>
            <article className="workflow-card">
              <span className="step-number">03</span>
              <BookOpen size={23} />
              <h3>Improve</h3>
              <p>Review the results and identify areas to practise.</p>
            </article>
          </div>
        </section>

        <section className="team-panel">
          <div>
            <p className="eyebrow">BUILT WITH PURPOSE</p>
            <h2>Meet the builders</h2>
            <p>
              VOXA is a collaborative AI project focused on making public
              speaking practice more measurable, accessible and actionable.
            </p>
          </div>
          <div className="team-list">
            {team.map((name, index) => (
              <div className="team-member" key={name}>
                <span className="team-initial">{name.charAt(0)}</span>
                <span>{name}</span>
                <span className="team-index">0{index + 1}</span>
              </div>
            ))}
          </div>
        </section>

        <footer className="voxa-footer">
          <span>VOXA · AI PUBLIC SPEAKING COACH</span>
          <span>Understand your voice. Improve your delivery.</span>
        </footer>
      </main>

      <button
        className="floating-analysis-button"
        onClick={() => navigate("/upload")}
      >
        <Mic2 size={20} />
        <span>Analyze My Speech</span>
        <ArrowRight size={18} />
      </button>
    </div>
  );
}
