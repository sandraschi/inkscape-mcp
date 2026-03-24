import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AppLayout } from '@/components/layout/app-layout';
import { Dashboard } from '@/pages/dashboard';
import { Actions } from '@/pages/actions';
import { Logs } from '@/pages/logs';
import { Chat } from '@/pages/chat';
import { Settings } from '@/pages/settings';
import { SvgStudio } from '@/pages/svg-studio';

function App() {
  return (
    <Router>
      <AppLayout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/svg-studio" element={<SvgStudio />} />
          <Route path="/actions" element={<Actions />} />
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
