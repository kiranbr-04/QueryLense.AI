import React from 'react';

export const StatusBadge = ({ status, text }) => {
  const s = (status || '').toLowerCase();
  let color = 'bg-slate-100 text-slate-700 border-slate-200';
  let dotColor = 'bg-slate-400';

  if (s === 'connected' || s === 'online' || s === 'success' || s === 'active') {
    color = 'bg-emerald-50 text-emerald-700 border-emerald-200';
    dotColor = 'bg-emerald-500';
  } else if (s === 'corrected') {
    color = 'bg-amber-50 text-amber-700 border-amber-200';
    dotColor = 'bg-amber-500';
  } else if (s === 'error' || s === 'disconnected' || s === 'revoked') {
    color = 'bg-rose-50 text-rose-700 border-rose-200';
    dotColor = 'bg-rose-500';
  } else if (s === 'testing' || s === 'loading') {
    color = 'bg-blue-50 text-blue-700 border-blue-200';
    dotColor = 'bg-blue-500';
  }

  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium border ${color}`}>
      <span className={`w-1.5 h-1.5 rounded-full ${dotColor}`} />
      {text || status}
    </span>
  );
};
