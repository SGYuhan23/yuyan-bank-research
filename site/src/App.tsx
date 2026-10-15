import { useEffect } from "react";
import { Routes, Route, useLocation, Navigate } from "react-router-dom";
import Landing from "./pages/Landing";
import DemoHome from "./pages/DemoHome";
import AgentDemo from "./pages/AgentDemo";
import Screenshots from "./pages/Screenshots";
import About from "./pages/About";
export default function App() {
  const { pathname } = useLocation();
  useEffect(() => {
    window.scrollTo(0, 0);
  }, [pathname]);
  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route path="/demo" element={<DemoHome />} />
      <Route path="/demo/:id" element={<AgentDemo key={pathname} />} />
      <Route path="/screenshots" element={<Screenshots />} />
      <Route path="/about" element={<About />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
