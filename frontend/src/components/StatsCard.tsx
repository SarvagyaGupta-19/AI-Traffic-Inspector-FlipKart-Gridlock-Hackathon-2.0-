'use client';

import { VIOLATION_COLORS, VIOLATION_ICONS, VIOLATION_LABELS, type ViolationType } from '@/lib/types';

interface StatsCardProps {
  label: string;
  value: string | number;
  change?: string;
  changeType?: 'up' | 'down' | 'neutral';
  icon?: React.ReactNode;
  color?: string;
}

export function StatsCard({ label, value, change, changeType = 'neutral', icon }: StatsCardProps) {
  return (
    <div className="border bg-[#FFFFFF] rounded-md shadow-sm border-[var(--border-color)] p-5">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs text-[var(--text-secondary)] font-bold uppercase tracking-wider mb-1.5">
            {label}
          </p>
          <p className="text-3xl font-extrabold text-[var(--text-primary)]">{value}</p>
          {change && (
            <p className={`text-xs mt-2 font-semibold ${
              changeType === 'up' ? 'text-[var(--accent-red)]' :
              changeType === 'down' ? 'text-[var(--accent-green)]' :
              'text-[var(--text-secondary)]'
            }`}>
              {changeType === 'up' ? '↑' : changeType === 'down' ? '↓' : '•'} {change}
            </p>
          )}
        </div>
        {icon && (
          <div className="w-10 h-10 rounded flex items-center justify-center border" style={{ background: '#F4F6F8', borderColor: 'var(--border-color)' }}>
            {icon}
          </div>
        )}
      </div>
    </div>
  );
}

interface ViolationBadgeProps {
  type: ViolationType | string;
  size?: 'sm' | 'md';
}

export function ViolationBadge({ type, size = 'sm' }: ViolationBadgeProps) {
  const violationType = type as ViolationType;
  const label = VIOLATION_LABELS[violationType] || type;
  const color = VIOLATION_COLORS[violationType] || '#637381';
  const icon = VIOLATION_ICONS[violationType] || '⚠️';

  return (
    <span
      className="badge border bg-white"
      style={{
        color: color,
        borderColor: color,
        fontSize: size === 'sm' ? '11px' : '13px',
        padding: size === 'sm' ? '2px 8px' : '4px 12px',
        borderRadius: '4px',
        fontWeight: 700
      }}
    >
      <span className="mr-1">{icon}</span>
      {label}
    </span>
  );
}

interface ConfidenceMeterProps {
  value: number;
  size?: 'sm' | 'md';
}

export function ConfidenceMeter({ value, size = 'sm' }: ConfidenceMeterProps) {
  const pct = Math.round(value * 100);
  const color = pct >= 80 ? 'var(--accent-green)' :
                pct >= 60 ? 'var(--accent-orange)' :
                'var(--accent-red)';

  return (
    <div className="flex items-center gap-2">
      <div className={`progress-bar flex-1 ${size === 'sm' ? 'h-[4px]' : 'h-[6px]'}`}>
        <div
          className="progress-bar-fill"
          style={{ width: `${pct}%`, background: color }}
        />
      </div>
      <span className="text-[10px] font-mono font-bold" style={{ color }}>
        {pct}%
      </span>
    </div>
  );
}
