'use client';

import { useEffect, useState } from 'react';
import { BarChart3, TrendingUp } from 'lucide-react';
import api from '@/lib/api';
import type { AnalyticsResponse } from '@/lib/types';
import { VIOLATION_LABELS, VIOLATION_COLORS, type ViolationType } from '@/lib/types';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend,
  Area, AreaChart,
} from 'recharts';

const CHART_COLORS = ['#4f7cff', '#7c5cfc', '#ff4757', '#ffa502', '#2ed573', '#18dcff', '#a55eea'];

export default function AnalyticsPage() {
  const [analytics, setAnalytics] = useState<AnalyticsResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadAnalytics() {
      try {
        const data = await api.getAnalytics();
        setAnalytics(data);
      } catch (err) {
        console.error('Failed to load analytics:', err);
      } finally {
        setLoading(false);
      }
    }
    loadAnalytics();
  }, []);

  if (loading) {
    return (
      <div className="p-8  min-h-screen">
        <div className="shimmer h-8 w-48 rounded-lg mb-8" />
        <div className="grid grid-cols-2 gap-6">
          <div className="shimmer h-80 rounded-2xl" />
          <div className="shimmer h-80 rounded-2xl" />
          <div className="shimmer h-80 rounded-2xl col-span-2" />
        </div>
      </div>
    );
  }

  // Prepare chart data
  const pieData = Object.entries(analytics?.by_type || {}).map(([type, count]) => ({
    name: VIOLATION_LABELS[type as ViolationType] || type,
    value: count as number,
    color: VIOLATION_COLORS[type as ViolationType] || '#888',
  }));

  const barData = Object.entries(analytics?.by_day || {})
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([date, count]) => ({
      date: new Date(date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
      violations: count as number,
    }));

  // Create trend data from daily counts
  const trendData = barData.map((item, index) => ({
    ...item,
    cumulative: barData.slice(0, index + 1).reduce((sum, d) => sum + d.violations, 0),
  }));

  return (
    <div className="p-8  min-h-screen">
      <div className="mb-8 animate-slide-up">
        <h1 className="text-2xl font-bold">
          <span className="text-[var(--accent-blue)]">Analytics & Insights</span>
        </h1>
        <p className="text-sm text-[var(--text-secondary)] mt-1">
          Traffic violation patterns and detection performance
        </p>
      </div>

      {/* Summary cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8 stagger-children">
        <div className="border bg-[#FFFFFF] rounded-md shadow-sm border-[var(--border-color)] p-5 text-center">
          <p className="text-4xl font-bold text-[var(--accent-blue)]">{analytics?.total_violations || 0}</p>
          <p className="text-xs text-[var(--text-secondary)] mt-2">Total Violations</p>
        </div>
        <div className="border bg-[#FFFFFF] rounded-md shadow-sm border-[var(--border-color)] p-5 text-center">
          <p className="text-4xl font-bold" style={{ color: 'var(--accent-green)' }}>
            {Math.round((analytics?.avg_confidence || 0) * 100)}%
          </p>
          <p className="text-xs text-[var(--text-secondary)] mt-2">Average Confidence</p>
        </div>
        <div className="border bg-[#FFFFFF] rounded-md shadow-sm border-[var(--border-color)] p-5 text-center">
          <p className="text-4xl font-bold" style={{ color: 'var(--accent-cyan)' }}>
            {analytics?.plates_detected || 0}
          </p>
          <p className="text-xs text-[var(--text-secondary)] mt-2">Plates Extracted</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        {/* Pie Chart — Violation Distribution */}
        <div className="border bg-[#FFFFFF] rounded-md shadow-sm border-[var(--border-color)] p-6 animate-slide-up" style={{ animationDelay: '0.2s' }}>
          <h3 className="text-sm font-semibold text-[var(--text-secondary)] uppercase tracking-wider mb-6 flex items-center gap-2">
            <BarChart3 className="w-4 h-4 text-[var(--accent-blue)]" />
            Violation Distribution
          </h3>
          {pieData.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={pieData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={110}
                  paddingAngle={3}
                  dataKey="value"
                  stroke="none"
                >
                  {pieData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{
                    background: 'var(--bg-card)',
                    border: '1px solid var(--border-color)',
                    borderRadius: '12px',
                    color: 'var(--text-primary)',
                    fontSize: '12px',
                  }}
                />
                <Legend
                  wrapperStyle={{ fontSize: '12px', color: 'var(--text-secondary)' }}
                />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-[300px] flex items-center justify-center text-sm text-[var(--text-secondary)]">
              No data available yet
            </div>
          )}
        </div>

        {/* Bar Chart — Daily Violations */}
        <div className="border bg-[#FFFFFF] rounded-md shadow-sm border-[var(--border-color)] p-6 animate-slide-up" style={{ animationDelay: '0.3s' }}>
          <h3 className="text-sm font-semibold text-[var(--text-secondary)] uppercase tracking-wider mb-6 flex items-center gap-2">
            <TrendingUp className="w-4 h-4 text-[var(--accent-purple)]" />
            Daily Violation Count
          </h3>
          {barData.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={barData}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border-color)" />
                <XAxis
                  dataKey="date"
                  tick={{ fill: 'var(--text-secondary)', fontSize: 11 }}
                  axisLine={{ stroke: 'var(--border-color)' }}
                />
                <YAxis
                  tick={{ fill: 'var(--text-secondary)', fontSize: 11 }}
                  axisLine={{ stroke: 'var(--border-color)' }}
                />
                <Tooltip
                  contentStyle={{
                    background: 'var(--bg-card)',
                    border: '1px solid var(--border-color)',
                    borderRadius: '12px',
                    color: 'var(--text-primary)',
                    fontSize: '12px',
                  }}
                />
                <Bar dataKey="violations" radius={[6, 6, 0, 0]}>
                  {barData.map((_, index) => (
                    <Cell key={`bar-${index}`} fill={CHART_COLORS[index % CHART_COLORS.length]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-[300px] flex items-center justify-center text-sm text-[var(--text-secondary)]">
              No daily data available yet
            </div>
          )}
        </div>
      </div>

      {/* Area Chart — Cumulative Trend */}
      <div className="border bg-[#FFFFFF] rounded-md shadow-sm border-[var(--border-color)] p-6 animate-slide-up" style={{ animationDelay: '0.4s' }}>
        <h3 className="text-sm font-semibold text-[var(--text-secondary)] uppercase tracking-wider mb-6">
          Cumulative Detection Trend
        </h3>
        {trendData.length > 0 ? (
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={trendData}>
              <defs>
                <linearGradient id="gradientBlue" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="var(--accent-blue)" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="var(--accent-blue)" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border-color)" />
              <XAxis
                dataKey="date"
                tick={{ fill: 'var(--text-secondary)', fontSize: 11 }}
                axisLine={{ stroke: 'var(--border-color)' }}
              />
              <YAxis
                tick={{ fill: 'var(--text-secondary)', fontSize: 11 }}
                axisLine={{ stroke: 'var(--border-color)' }}
              />
              <Tooltip
                contentStyle={{
                  background: 'var(--bg-card)',
                  border: '1px solid var(--border-color)',
                  borderRadius: '12px',
                  color: 'var(--text-primary)',
                  fontSize: '12px',
                }}
              />
              <Area
                type="monotone"
                dataKey="cumulative"
                stroke="var(--accent-blue)"
                fill="url(#gradientBlue)"
                strokeWidth={2}
              />
            </AreaChart>
          </ResponsiveContainer>
        ) : (
          <div className="h-[300px] flex items-center justify-center text-sm text-[var(--text-secondary)]">
            Process some images to see trends
          </div>
        )}
      </div>
    </div>
  );
}
