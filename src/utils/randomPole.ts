const POLE_IDS = [
  'P-1001', 'P-1002', 'P-1003', 'P-1004', 'P-1005',
  'P-1006', 'P-1007', 'P-1008', 'P-1009', 'P-1023',
  'P-1062', 'P-1078', 'P-1131', 'P-1147', 'P-1192',
];

export function randomPoleId(): string {
  return POLE_IDS[Math.floor(Math.random() * POLE_IDS.length)];
}
