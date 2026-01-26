/**
 * StakingMetricsDisplay Component
 *
 * Displays staking pool metrics with visual indicators for APY and utilization.
 */

import type { StakingMetrics } from '../types/abm';

interface StakingMetricsDisplayProps {
  metrics: StakingMetrics;
  className?: string;
}

export function StakingMetricsDisplay({
  metrics,
  className = ''
}: StakingMetricsDisplayProps) {
  const formatNumber = (num: number): string => {
    if (num >= 1_000_000_000) {
      return `${(num / 1_000_000_000).toFixed(2)}B`;
    } else if (num >= 1_000_000) {
      return `${(num / 1_000_000).toFixed(2)}M`;
    } else if (num >= 1_000) {
      return `${(num / 1_000).toFixed(2)}K`;
    }
    return num.toFixed(2);
  };

  const formatPercentage = (num: number): string => {
    return `${(num * 100).toFixed(2)}%`;
  };

  const getAPYColor = (apy: number): string => {
    if (apy >= 0.15) return 'text-green-700';
    if (apy >= 0.10) return 'text-yellow-700';
    return 'text-orange-700';
  };

  const getUtilizationColor = (utilization: number): string => {
    if (utilization >= 0.80) return 'bg-red-600';
    if (utilization >= 0.50) return 'bg-yellow-600';
    return 'bg-green-600';
  };

  return (
    <div className={`bg-gradient-to-br from-blue-50 to-indigo-50 rounded-lg border-2 border-blue-200 p-6 ${className}`}>
      <div className="flex items-center mb-6">
        <span className="text-3xl mr-3">🔒</span>
        <h3 className="text-xl font-bold text-gray-900">Staking Pool Metrics</h3>
      </div>

      <div className="grid grid-cols-2 gap-6">
        <div className="bg-white rounded-lg p-4 shadow-sm border border-blue-100">
          <div className="text-sm font-medium text-gray-600 mb-1">Current APY</div>
          <div className={`text-3xl font-bold ${getAPYColor(metrics.current_apy)}`}>
            {formatPercentage(metrics.current_apy)}
          </div>
          <div className="mt-2 text-xs text-gray-500">
            {metrics.current_apy >= 0.15 && 'High rewards! Pool has low utilization'}
            {metrics.current_apy >= 0.10 && metrics.current_apy < 0.15 && 'Moderate rewards'}
            {metrics.current_apy < 0.10 && 'Pool is filling up'}
          </div>
        </div>

        <div className="bg-white rounded-lg p-4 shadow-sm border border-blue-100">
          <div className="text-sm font-medium text-gray-600 mb-1">Total Staked</div>
          <div className="text-3xl font-bold text-blue-700">
            {formatNumber(metrics.total_staked)}
          </div>
          <div className="mt-2 text-xs text-gray-500">
            tokens locked in pool
          </div>
        </div>

        <div className="bg-white rounded-lg p-4 shadow-sm border border-blue-100">
          <div className="text-sm font-medium text-gray-600 mb-1">Pool Utilization</div>
          <div className="text-2xl font-bold text-gray-900">
            {formatPercentage(metrics.utilization_pct)}
          </div>
          <div className="mt-3">
            <div className="w-full bg-gray-200 rounded-full h-3 overflow-hidden">
              <div
                className={`${getUtilizationColor(metrics.utilization_pct)} h-full transition-all duration-500 rounded-full`}
                style={{ width: `${Math.min(100, metrics.utilization_pct * 100)}%` }}
              />
            </div>
            <div className="mt-1 text-xs text-gray-500">
              {metrics.utilization_pct >= 0.80 && 'Pool nearly full!'}
              {metrics.utilization_pct >= 0.50 && metrics.utilization_pct < 0.80 && 'Pool filling up'}
              {metrics.utilization_pct < 0.50 && 'Plenty of capacity'}
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg p-4 shadow-sm border border-blue-100">
          <div className="text-sm font-medium text-gray-600 mb-1">Total Rewards Paid</div>
          <div className="text-2xl font-bold text-green-700">
            {formatNumber(metrics.total_rewards_paid)}
          </div>
          <div className="mt-2 text-xs text-gray-500">
            tokens distributed
          </div>
        </div>
      </div>

      <div className="mt-6 pt-6 border-t border-blue-200">
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div className="flex items-center justify-between">
            <span className="text-gray-600">Active Stakers:</span>
            <span className="font-semibold text-gray-900">{metrics.num_stakers.toLocaleString()}</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-gray-600">Avg Stake per User:</span>
            <span className="font-semibold text-gray-900">
              {formatNumber(metrics.total_staked / Math.max(1, metrics.num_stakers))}
            </span>
          </div>
        </div>
      </div>

      <div className="mt-6 p-4 bg-blue-100 bg-opacity-50 rounded-lg border border-blue-300">
        <p className="text-sm text-blue-900">
          <span className="font-semibold">How it works:</span> APY decreases as the pool fills up.
          Early stakers earn higher rewards. Pool utilization shows how much capacity is used.
        </p>
      </div>
    </div>
  );
}

export default StakingMetricsDisplay;
