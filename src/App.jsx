
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import Login from "./pages/Login.jsx";
import Dashboard from "./pages/Dashboard.jsx";
import UploadVideo from "./pages/UploadVideo.jsx";
import Analyzing from "./pages/Analyzing.jsx";
import AnalysisReport from "./pages/AnalysisReport.jsx";
import DetailedFinal from "./pages/DetailedFinal.jsx";
import Practice from "./pages/Practice.jsx";
import History from "./pages/History.jsx";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Login />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/upload" element={<UploadVideo />} />
        <Route path="/analyzing" element={<Analyzing />} />
        <Route path="/report" element={<AnalysisReport />} />
        <Route path="/detailed-final" element={<DetailedFinal />} />
        <Route path="/practice" element={<Practice />} />
        <Route path="/history" element={<History />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
