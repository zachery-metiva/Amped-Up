import '../login.css';

export function EmployeePage() {
  return (
    <div className="lp-root">
      <div className="lp-card">

        {/* ── Left panel ── */}
        <div className="lp-left">
          <div className="lp-logo">
            <div className="lp-logo-mark">
              <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="#FBBF24" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z" />
              </svg>
            </div>
            <span className="lp-logo-name">Amped Up</span>
          </div>

          {/* Mobile subtitle */}
          <p className="lp-mobile-sub">Select your role to continue.</p>

          <div className="lp-tagline">
            <h1>Your role shapes your tools.</h1>
            <p>Field technicians capture conditions on the ground. Evaluators review the data, assign severity, and coordinate dispatch — all from a single real-time dashboard.</p>
          </div>

          <ul className="lp-bullets">
            <li>
              <svg className="lp-bullet-check" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><polyline points="20 6 9 17 4 12" /></svg>
              Full access to the risk and compliance dashboard.
            </li>
            <li>
              <svg className="lp-bullet-check" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><polyline points="20 6 9 17 4 12" /></svg>
              Live WebSocket updates as reports come in.
            </li>
            <li>
              <svg className="lp-bullet-check" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><polyline points="20 6 9 17 4 12" /></svg>
              Approve, snooze, or dismiss with one tap.
            </li>
          </ul>

          <svg className="lp-skyline" viewBox="0 0 600 120" preserveAspectRatio="none">
            <g fill="#1E293B">
              <rect x="40"  y="58" width="4" height="62" /><rect x="10"  y="74" width="62" height="3" />
              <rect x="140" y="46" width="4" height="74" /><rect x="110" y="64" width="62" height="3" />
              <rect x="240" y="54" width="4" height="66" /><rect x="210" y="72" width="62" height="3" />
              <rect x="340" y="42" width="4" height="78" /><rect x="310" y="60" width="62" height="3" />
              <rect x="440" y="50" width="4" height="70" /><rect x="410" y="68" width="62" height="3" />
              <rect x="540" y="56" width="4" height="64" /><rect x="510" y="72" width="62" height="3" />
            </g>
            <g stroke="#1E293B" strokeWidth="1" fill="none">
              <path d="M42,58 L142,46 L242,54 L342,42 L442,50 L542,56" />
              <path d="M42,64 L142,52 L242,60 L342,48 L442,56 L542,62" />
            </g>
          </svg>
        </div>

        {/* ── Right panel ── */}
        <div className="lp-right">
          <button className="lp-back" onClick={() => { window.location.href = '/'; }}>
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="19" y1="12" x2="5" y2="12" /><polyline points="12 19 5 12 12 5" />
            </svg>
            Back
          </button>

          <h2>Select your role</h2>
          <p className="lp-right-sub">Choose how you'll be working today.</p>

          <div className="lp-options">
            <button className="lp-opt" onClick={() => { window.location.href = '/field-report'; }}>
              <div className="lp-opt-icon amber">
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z" />
                </svg>
              </div>
              <div className="lp-opt-body">
                <div className="lp-opt-title">
                  Field Technician
                  <span className="lp-pill" style={{ background: '#451A03', color: '#FBBF24' }}>Mobile</span>
                </div>
                <div className="lp-opt-desc">Capture pole inspections with photo documentation. Report conditions directly from the field.</div>
              </div>
              <svg className="lp-opt-chev" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <polyline points="9 18 15 12 9 6" />
              </svg>
            </button>

            <button className="lp-opt" onClick={() => { window.location.href = '/evaluation'; }}>
              <div className="lp-opt-icon blue">
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <rect x="3" y="3" width="18" height="18" rx="2" /><path d="M3 9h18" /><path d="M9 21V9" />
                </svg>
              </div>
              <div className="lp-opt-body">
                <div className="lp-opt-title">Evaluator / Ops</div>
                <div className="lp-opt-desc">Review submitted reports, manage severity assignments, approve dispatches, and track portfolio risk.</div>
              </div>
              <svg className="lp-opt-chev" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <polyline points="9 18 15 12 9 6" />
              </svg>
            </button>
          </div>

          <div className="lp-legal">
            Not your account? <a onClick={() => { window.location.href = '/'; }} style={{ cursor: 'pointer' }}>Sign out</a> ·{' '}
            <a className="lp-link">Contact IT support</a>
          </div>
        </div>

      </div>
    </div>
  );
}
