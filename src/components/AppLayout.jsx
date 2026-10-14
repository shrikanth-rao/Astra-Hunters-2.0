
import { NavLink, Outlet } from "react-router-dom";
import {
  Activity,
  LayoutDashboard,
  FileVideo,
  Target,
  Mic,
  History,
} from "lucide-react";
import ChatbotWidget from "./ChatbotWidget";

const links = [
  { to: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { to: "/upload", label: "Analyze Speech", icon: FileVideo },
  { to: "/detailed-final", label: "Final Review", icon: Target },
  { to: "/practice", label: "Practice", icon: Mic },
  { to: "/history", label: "Progress", icon: History },
];

export default function AppLayout() {
  return (
    <div className="app-shell">
      <header className="top-navigation">
        <NavLink to="/dashboard" className="app-logo">
          <span className="app-logo-icon">
            <Activity size={22} />
          </span>
          <span>SpeakKaro<span className="logo-accent">.AI</span></span>
        </NavLink>

        <nav className="top-navigation-links">
          {links.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                `top-nav-link ${isActive ? "selected" : ""}`
              }
            >
              <Icon size={16} />
              <span>{label}</span>
            </NavLink>
          ))}
        </nav>

        <div className="top-nav-status">
          <span className="nav-status-dot" />
          AI Coach
        </div>
      </header>

      <div className="app-page-content">
        <Outlet />
      </div>

      <ChatbotWidget />
    </div>
  );
}
