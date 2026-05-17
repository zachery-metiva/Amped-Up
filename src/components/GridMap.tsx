import 'leaflet/dist/leaflet.css';
import { useEffect } from 'react';
import { MapContainer, TileLayer, CircleMarker, Tooltip, useMap } from 'react-leaflet';
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

function FlyToSelected({ poles, selectedPoleId }: { poles: MapPole[]; selectedPoleId: string | null }) {
  const map = useMap();
  useEffect(() => {
    const pole = poles.find((p) => p.id === selectedPoleId);
    if (pole) map.panTo([pole.lat, pole.lon], { animate: true, duration: 0.4 });
  }, [selectedPoleId, poles, map]);
  return null;
}

export function GridMap({ poles, selectedPoleId, onSelectPole }: GridMapProps) {
  const center: [number, number] = poles.length
    ? [
        poles.reduce((s, p) => s + p.lat, 0) / poles.length,
        poles.reduce((s, p) => s + p.lon, 0) / poles.length,
      ]
    : [42.3314, -83.0458]; // Detroit Corktown fallback

  return (
    <div className="card" style={{ padding: 14 }}>
      <div className="row" style={{ marginBottom: 10 }}>
        <h4>Live map · Detroit District D-7</h4>
        <div style={{ display: 'flex', gap: 14, fontSize: 11, color: 'var(--text-3)' }}>
          {(['critical', 'high', 'medium', 'low'] as Severity[]).map((s) => (
            <span key={s} style={{ display: 'inline-flex', alignItems: 'center', gap: 5 }}>
              <span className="dot" style={{ background: SEVERITY_COLOR[s] }} />
              {s.charAt(0).toUpperCase() + s.slice(1)}
            </span>
          ))}
        </div>
      </div>

      <MapContainer
        center={center}
        zoom={16}
        style={{ height: 320, borderRadius: 8 }}
        scrollWheelZoom
      >
        <TileLayer
          url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
          maxZoom={19}
        />

        {poles.map((pole) => {
          const isSelected = pole.id === selectedPoleId;
          const color = SEVERITY_COLOR[pole.severity];
          return (
            <CircleMarker
              key={pole.id}
              center={[pole.lat, pole.lon]}
              radius={isSelected ? 9 : 6}
              pathOptions={{
                color: isSelected ? '#3B82F6' : '#0B1020',
                fillColor: color,
                fillOpacity: 1,
                weight: isSelected ? 2.5 : 1.5,
              }}
              eventHandlers={{ click: () => onSelectPole(pole.id) }}
            >
              <Tooltip direction="top" offset={[0, -8]} opacity={1}>
                <strong>{pole.id}</strong>
                <br />
                {pole.severity.charAt(0).toUpperCase() + pole.severity.slice(1)}
                &nbsp;·&nbsp;
                {pole.lat.toFixed(5)}°N,&nbsp;{Math.abs(pole.lon).toFixed(5)}°W
              </Tooltip>
            </CircleMarker>
          );
        })}

        <FlyToSelected poles={poles} selectedPoleId={selectedPoleId} />
      </MapContainer>
    </div>
  );
}
