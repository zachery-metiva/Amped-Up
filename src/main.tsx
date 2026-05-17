import { createRoot } from 'react-dom/client';
import { App } from './App';
import { LoginPage } from './pages/LoginPage';
import { EmployeePage } from './pages/EmployeePage';
import { ReportSubmission } from './pages/ReportSubmission';
import { FieldReport } from './pages/FieldReport';
import { AllReports } from './pages/AllReports';
import './index.css';

const root = document.getElementById('root');
if (!root) throw new Error('Root element not found');

const path = window.location.pathname;
const page =
  path.startsWith('/evaluation') ? <App /> :
  path.startsWith('/employee')   ? <EmployeePage /> :
  path.startsWith('/field-report') ? <FieldReport /> :
  path.startsWith('/reports')    ? <AllReports /> :
  path.startsWith('/report')     ? <ReportSubmission /> :
  <LoginPage />;

createRoot(root).render(page);
