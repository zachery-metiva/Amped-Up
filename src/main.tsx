import { createRoot } from 'react-dom/client';
import { App } from './App';
import { ReportSubmission } from './pages/ReportSubmission';
import './index.css';

const root = document.getElementById('root');
if (!root) throw new Error('Root element not found');

const isReportPage = window.location.pathname.startsWith('/report');
createRoot(root).render(isReportPage ? <ReportSubmission /> : <App />);
