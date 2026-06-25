import {
  Navigate,
  Route,
  BrowserRouter as Router,
  Routes,
} from "react-router-dom";
import { AppLayout } from "@/components/layout/app-layout";
import { Actions } from "@/pages/actions";
import { AgentTools } from "@/pages/agent-tools";
import { AnimationStudio } from "@/pages/animation";
import { Chat } from "@/pages/chat";
import { Dashboard } from "@/pages/dashboard";
import { Help } from "@/pages/help";
import { LayerManager } from "@/pages/layers";
import Logs from "@/pages/logs";
import { Settings } from "@/pages/settings";
import { Status } from "@/pages/status";
import { SvgStudio } from "@/pages/svg-studio";

function App() {
  return (
    <Router>
      <AppLayout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/status" element={<Status />} />
          <Route path="/help" element={<Help />} />
          <Route path="/agent-tools" element={<AgentTools />} />
          <Route path="/svg-studio" element={<SvgStudio />} />
          <Route path="/actions" element={<Actions />} />
          <Route path="/animation" element={<AnimationStudio />} />
          <Route path="/layers" element={<LayerManager />} />
          <Route path="/logs" element={<Logs />} />
          <Route path="/chat" element={<Chat />} />
          <Route path="/settings" element={<Settings />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AppLayout>
    </Router>
  );
}

export default App;
