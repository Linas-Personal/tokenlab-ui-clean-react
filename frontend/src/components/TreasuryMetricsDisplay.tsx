/**
 * TreasuryMetricsDisplay Component
 *
 * Displays treasury metrics including fees collected, buyback, and burn.
 */

import type { TreasuryMetrics } from '../types/abm';

interface TreasuryMetricsDisplayProps {
  metrics: TreasuryMetrics;
  className?: string;
}

export function TreasuryMetricsDisplay({
  metrics,
  className = ''
}: TreasuryMetricsDisplayProps) {
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

  const formatCurrency = (num: number): string => {
    return `$${formatNumber(num)}`;
  };

  const totalValue = metrics.fiat_balance + (metrics.token_balance * 1.0);

  return (
    <div className={`bg-gradient-to-br from-purple-50 to-pink-50 rounded-lg border-2 border-purple-200 p-6 ${className}`}>
      <div className="flex items-center mb-6">
        <span className="text-3xl mr-3">🏦</span>
        <h3 className="text-xl font-bold text-gray-900">Treasury Metrics</h3>
      </div>

      <div className="grid grid-cols-2 gap-6 mb-6">
        <div className="bg-white rounded-lg p-4 shadow-sm border border-purple-100">
          <div className="text-sm font-medium text-gray-600 mb-1">Fiat Balance</div>
          <div className="text-3xl font-bold text-green-700">
            {formatCurrency(metrics.fiat_balance)}
          </div>
          <div className="mt-2 text-xs text-gray-500">
            in treasury reserves
          </div>
        </div>

        <div className="bg-white rounded-lg p-4 shadow-sm border border-purple-100">
          <div className="text-sm font-medium text-gray-600 mb-1">Token Balance</div>
          <div className="text-3xl font-bold text-blue-700">
            {formatNumber(metrics.token_balance)}
          </div>
          <div className="mt-2 text-xs text-gray-500">
            tokens held by treasury
          </div>
        </div>

        <div className="bg-white rounded-lg p-4 shadow-sm border border-purple-100">
          <div className="text-sm font-medium text-gray-600 mb-1">Total Fees Collected</div>
          <div className="text-2xl font-bold text-purple-700">
            {formatCurrency(metrics.total_fees_collected_fiat)}
          </div>
          <div className="mt-2 text-xs text-gray-500">
            from transaction fees
          </div>
        </div>

        <div className="bg-white rounded-lg p-4 shadow-sm border border-purple-100">
          <div className="text-sm font-medium text-gray-600 mb-1">Liquidity Deployed</div>
          <div className="text-2xl font-bold text-indigo-700">
            {formatCurrency(metrics.total_liquidity_deployed)}
          </div>
          <div className="mt-2 text-xs text-gray-500">
            to market liquidity
          </div>
        </div>
      </div>

      <div className="bg-gradient-to-r from-orange-100 to-red-100 rounded-lg p-6 border-2 border-orange-300 mb-6">
        <div className="flex items-center mb-4">
          <span className="text-2xl mr-2">🔥</span>
          <h4 className="text-lg font-bold text-gray-900">Deflationary Mechanics</h4>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <div className="text-sm font-medium text-gray-700 mb-1">Tokens Bought Back</div>
            <div className="text-2xl font-bold text-orange-700">
              {formatNumber(metrics.total_tokens_bought)}
            </div>
          </div>

          <div>
            <div className="text-sm font-medium text-gray-700 mb-1">Tokens Burned</div>
            <div className="text-2xl font-bold text-red-700">
              {formatNumber(metrics.total_tokens_burned)}
            </div>
          </div>
        </div>

        <div className="mt-4 pt-4 border-t border-orange-300">
          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-700">Burn Rate:</span>
            <span className="text-sm font-semibold text-red-700">
              {metrics.total_tokens_bought > 0
                ? `${((metrics.total_tokens_burned / metrics.total_tokens_bought) * 100).toFixed(1)}%`
                : '0%'} of buyback
            </span>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-4 text-sm mb-6">
        <div className="bg-white rounded-lg p-3 shadow-sm border border-purple-100">
          <div className="text-xs text-gray-600 mb-1">Total Value</div>
          <div className="text-lg font-bold text-gray-900">
            {formatCurrency(totalValue)}
          </div>
        </div>

        <div className="bg-white rounded-lg p-3 shadow-sm border border-purple-100">
          <div className="text-xs text-gray-600 mb-1">Fiat %</div>
          <div className="text-lg font-bold text-green-700">
            {totalValue > 0 ? ((metrics.fiat_balance / totalValue) * 100).toFixed(1) : '0'}%
          </div>
        </div>

        <div className="bg-white rounded-lg p-3 shadow-sm border border-purple-100">
          <div className="text-xs text-gray-600 mb-1">Token %</div>
          <div className="text-lg font-bold text-blue-700">
            {totalValue > 0 ? ((metrics.token_balance / totalValue) * 100).toFixed(1) : '0'}%
          </div>
        </div>
      </div>

      <div className="p-4 bg-purple-100 bg-opacity-50 rounded-lg border border-purple-300">
        <p className="text-sm text-purple-900">
          <span className="font-semibold">Treasury Strategy:</span> Collects transaction fees,
          deploys to liquidity for market stability, and executes buyback-and-burn to create
          deflationary pressure on token supply.
        </p>
      </div>
    </div>
  );
}

export default TreasuryMetricsDisplay;
