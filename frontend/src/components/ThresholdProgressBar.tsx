import React from 'react';
import { Clock, CheckCircle2, Users } from 'lucide-react';

interface ThresholdProps {
  currentCount: number;
  threshold?: number;
  status: string;
}

export const ThresholdProgressBar: React.FC<ThresholdProps> = ({
  currentCount,
  threshold = 5,
  status,
}) => {
  const percentage = Math.min(100, Math.round((currentCount / threshold) * 100));
  const isComplete = currentCount >= threshold;

  return (
    <div className="p-6 rounded-3xl bg-olive-900 border border-olive-700 shadow-xl text-cream-100">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-4">
        <div className="flex items-center space-x-3">
          {isComplete ? (
            <div className="w-9 h-9 rounded-xl bg-cream-200 text-olive-950 flex items-center justify-center shadow-md">
              <CheckCircle2 className="w-5 h-5" />
            </div>
          ) : (
            <div className="w-9 h-9 rounded-xl bg-olive-800 text-cream-300 border border-olive-700 flex items-center justify-center">
              <Clock className="w-5 h-5 text-cream-300" />
            </div>
          )}
          <div>
            <h4 className="text-xs font-display tracking-widest font-bold text-cream-200 uppercase">
              Automated Submission Threshold
            </h4>
            <p className="text-xs text-olive-400">
              {isComplete
                ? `Threshold satisfied (${threshold} students). Similarity analysis active.`
                : `Waiting for ${threshold} distinct students before triggering comparisons.`}
            </p>
          </div>
        </div>

        <div className="flex items-baseline space-x-1.5 self-end sm:self-auto bg-olive-850 px-4 py-2 rounded-2xl border border-olive-700">
          <span className="text-2xl font-black font-display text-cream-200">{currentCount}</span>
          <span className="text-xs font-semibold text-olive-400">/ {threshold} valid students</span>
        </div>
      </div>

      {/* Progress Track */}
      <div className="w-full h-3 bg-olive-950 rounded-full overflow-hidden p-0.5 border border-olive-700/60">
        <div
          className={`h-full rounded-full transition-all duration-700 ease-out ${
            isComplete
              ? 'bg-gradient-to-r from-cream-300 to-cream-100 shadow-md shadow-cream-200/20'
              : 'bg-gradient-to-r from-olive-500 to-cream-300'
          }`}
          style={{ width: `${percentage}%` }}
        />
      </div>

      <div className="mt-3.5 flex items-center justify-between text-[11px] text-olive-400">
        <span>Counting distinct students (resubmissions update code without increasing count)</span>
        <span className="font-semibold text-cream-200">
          {isComplete ? 'Threshold Met — Analysis Active' : `${Math.max(0, threshold - currentCount)} more required`}
        </span>
      </div>
    </div>
  );
};
