import { MapPole, Severity } from '../types';

const SEVERITY_COLOR: Record<Severity, string> = {
  critical: '#EF4444',
  high: '#F97316',
  medium: '#FBBF24',
  low: '#10B981',
};

interface GridMapProps {
  poles: MapPole[];
  selectedPoleId: string | null;
  onSelectPole: (poleId: string) => void;
}

function project(
  lat: number,
  lon: number,
  minLat: number,
  maxLat: number,
  minLon: number,
  maxLon: number,
  width: number,
  height: number,
  padding = 32,
): { x: number; y: number } {
  const latRange = maxLat - minLat || 0.001;
  const lonRange = maxLon - minLon || 0.001;
  const x = padding + ((lon - minLon) / lonRange) * (width - padding * 2);
  const y = height - padding - ((lat - minLat) / latRange) * (height - padding * 2);
  return { x, y };
}

export function GridMap({ poles, selectedPoleId, onSelectPole }: GridMapProps) {
  const W = 640;
  const H = 360;

  const lats = poles.map((p) => p.lat);
  const lons = poles.map((p) => p.lon);
  const minLat = Math.min(...lats);
  const maxLat = Math.max(...lats);
  const minLon = Math.min(...lons);
  const maxLon = Math.max(...lons);

  const projected = poles.map((p) => ({
    ...p,
    ...project(p.lat, p.lon, minLat, maxLat, minLon, maxLon, W, H),
  }));

  const selected = projected.find((p) => p.id === selectedPoleId);

  return (
    <div className="card" style={{ padding: 14 }}>
      <div className="row" style={{ marginBottom: 10 }}>
        <h4>Grid map · Sector 7</h4>
        <div style={{ display: 'flex', gap: 14, fontSize: 11, color: 'var(--text-3)' }}>
          {(['critical', 'high', 'medium', 'low'] as Severity[]).map((s) => (
            <span key={s} style={{ display: 'inline-flex', alignItems: 'center', gap: 5 }}>
              <span className="dot" style={{ background: SEVERITY_COLOR[s] }} />
              {s.charAt(0).toUpperCase() + s.slice(1)}
            </span>
          ))}
        </div>
      </div>

      <svg
        viewBox={`0 0 ${W} ${H}`}
        role="img"
        aria-label="Grid map showing utility pole locations color-coded by severity"
        style={{ width: '100%', height: 'auto', display: 'block', borderRadius: 8, background: '#070B16' }}
      >
        <defs>
          <pattern id="grid-pattern" width="32" height="32" patternUnits="userSpaceOnUse">
            <path d="M 32 0 L 0 0 0 32" fill="none" stroke="#0F172A" strokeWidth="0.5" />
          </pattern>
        </defs>
        <rect width={W} height={H} fill="url(#grid-pattern)" />

        {projected.map((p) => {
          const isSelected = p.id === selectedPoleId;
          const color = SEVERITY_COLOR[p.severity];
          return (
            <g key={p.id}>
              {isSelected && (
                <circle cx={p.x} cy={p.y} r={10} fill="none" stroke="#3B82F6" strokeWidth="2" />
              )}
              <circle
                cx={p.x}
                cy={p.y}
                r={isSelected ? 6.5 : 5}
                fill={color}
                stroke="#0B1020"
                strokeWidth={isSelected ? 1.5 : 0}
                style={{ cursor: 'pointer' }}
                role="button"
                aria-label={`${p.id} — ${p.severity}`}
                tabIndex={0}
                onClick={() => onSelectPole(p.id)}
                onKeyDown={(e) => e.key === 'Enter' && onSelectPole(p.id)}
              />
            </g>
          );
        })}

        {selected && (
          <g transform={`translate(${Math.min(selected.x + 12, W - 178)},${Math.max(selected.y - 56, 4)})`}>
            <rect x="0" y="0" width="170" height="46" rx="6" fill="#0F172A" stroke="#3B82F6" strokeWidth="1" />
            <text x="10" y="17" fontSize="11.5" fontWeight="500" fill="#F9FAFB" fontFamily="inherit">
              {selected.id} selected
            </text>
            <text x="10" y="33" fontSize="10.5" fill="#94A3B8" fontFamily="inherit">
              {selected.lat.toFixed(4)}° N, {Math.abs(selected.lon).toFixed(4)}° W
            </text>
          </g>
        )}

        <g transform={`translate(${W - 80},${H - 25})`}>
          <rect x="0" y="0" width="72" height="20" rx="4" fill="#0F172A" stroke="#1E293B" strokeWidth="0.5" />
          <rect x="8" y="9" width="26" height="2" fill="#94A3B8" />
          <text x="38" y="14" fontSize="10" fill="#94A3B8" fontFamily="inherit">200 ft</text>
        </g>

        <g transform={`translate(24,${H - 25})`}>
          <circle r="10" fill="#0F172A" stroke="#1E293B" strokeWidth="0.5" />
          <path d="M0,-6 L2,0 L0,6 L-2,0 Z" fill="#94A3B8" />
          <text x="-3" y="-11" fontSize="9" fill="#94A3B8" fontFamily="inherit">N</text>
        </g>
      </svg>
    </div>
  );
}
