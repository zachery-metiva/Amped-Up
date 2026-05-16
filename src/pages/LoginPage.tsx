import '../login.css';

export function LoginPage() {
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

          {/* Mobile subtitle — only visible on small screens */}
          <p className="lp-mobile-sub">Help keep your neighborhood powered.</p>

          {/* Desktop tagline */}
          <div className="lp-tagline">
            <h1>Help keep your neighborhood powered.</h1>
            <p>Report damaged poles in seconds. Crews are dispatched within hours. Trusted by 12 utilities across the Northeast to keep over 4 million homes online.</p>
          </div>

          <ul className="lp-bullets">
            <li>
              <svg className="lp-bullet-check" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><polyline points="20 6 9 17 4 12" /></svg>
              Spot a leaning pole or a downed line? Tell us.
            </li>
            <li>
              <svg className="lp-bullet-check" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><polyline points="20 6 9 17 4 12" /></svg>
              Your location is captured automatically by GPS.
            </li>
            <li>
              <svg className="lp-bullet-check" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><polyline points="20 6 9 17 4 12" /></svg>
              No account needed to submit a report.
            </li>
          </ul>

          {/* Skyline illustration */}
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
          <h2>Welcome</h2>
          <p className="lp-right-sub">How would you like to continue?</p>

          <div className="lp-options">
            <button className="lp-opt" onClick={() => { window.location.href = '/report'; }}>
              <div className="lp-opt-icon blue">
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z" /><circle cx="12" cy="10" r="3" />
                </svg>
              </div>
              <div className="lp-opt-body">
                <div className="lp-opt-title">
                  Continue as guest
                  <span className="lp-pill">Fastest</span>
                </div>
                <div className="lp-opt-desc">Report a pole issue in your area. No account, no password. Takes about 30 seconds.</div>
              </div>
              <svg className="lp-opt-chev" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <polyline points="9 18 15 12 9 6" />
              </svg>
            </button>

            <button className="lp-opt" onClick={() => { window.location.href = '/employee'; }}>
              <div className="lp-opt-icon amber">
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <rect x="2" y="7" width="20" height="14" rx="2" /><path d="M16 7V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v2" /><line x1="12" y1="12" x2="12" y2="16" /><line x1="10" y1="14" x2="14" y2="14" />
                </svg>
              </div>
              <div className="lp-opt-body">
                <div className="lp-opt-title">Sign in as employee</div>
                <div className="lp-opt-desc">Field techs, inspectors, and ops. Manage reports, approve, and dispatch crews.</div>
              </div>
              <svg className="lp-opt-chev" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <polyline points="9 18 15 12 9 6" />
              </svg>
            </button>
          </div>

          <div className="lp-legal">
            By continuing you agree to our <a>Terms</a> and <a>Privacy policy</a>.<br />
            Need help? <a className="lp-link">Contact support</a>
          </div>
        </div>

      </div>
    </div>
  );
}
