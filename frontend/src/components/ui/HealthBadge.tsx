import React from 'react';
import { HealthStatus } from '../../types';

interface HealthBadgeProps {
  health: HealthStatus | null;
  loading: boolean;
}

export const HealthBadge: React.FC<HealthBadgeProps> = ({ health, loading }) => {
  if (loading) {
    return (
      <div className="flex items-center space-x-2 text-xs text-slate-400 bg-slate-800/80 px-2.5 py-1 rounded-full border border-slate-700">
        <span className="w-2 h-2 rounded-full bg-amber-400 animate-ping" />
        <span>Checking health...</span>
      </div>
    );
  }

  if (!health || health.status !== 'healthy') {
    return (
      <div className="flex items-center space-x-2 text-xs text-amber-300 bg-amber-950/60 px-2.5 py-1 rounded-full border border-amber-800/60">
        <span className="w-2 h-2 rounded-full bg-amber-500" />
        <span>DB Degraded / Offline</span>
      </div>
    );
  }

  return (
    <div className="flex items-center space-x-2 text-xs text-emerald-300 bg-emerald-950/50 px-2.5 py-1 rounded-full border border-emerald-800/60">
      <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
      <span>System Ready</span>
    </div>
  );
};
