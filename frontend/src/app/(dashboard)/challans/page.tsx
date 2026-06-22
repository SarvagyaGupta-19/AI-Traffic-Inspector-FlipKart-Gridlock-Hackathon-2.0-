/* eslint-disable @next/next/no-img-element */
'use client';

import { useEffect, useState, useCallback } from 'react';
import { Search, Filter, ExternalLink, ChevronLeft, ChevronRight, X, AlertTriangle } from 'lucide-react';
import api from '@/lib/api';
import type { ViolationRecord } from '@/lib/types';
import { ViolationBadge, ConfidenceMeter } from '@/components/StatsCard';
import { VIOLATION_LABELS } from '@/lib/types';

export default function ChallansPage() {
  const [violations, setViolations] = useState<ViolationRecord[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [loading, setLoading] = useState(true);
  const [searchPlate, setSearchPlate] = useState('');
  const [filterType, setFilterType] = useState('');
  const [selectedViolation, setSelectedViolation] = useState<ViolationRecord | null>(null);

  const loadViolations = useCallback(async () => {
    setLoading(true);
    try {
      const data = await api.getViolations({
        page,
        per_page: 15,
        type: filterType || undefined,
        plate: searchPlate || undefined,
        status: 'issued',
      });
      setViolations(data.violations);
      setTotal(data.total);
      setTotalPages(data.total_pages);
    } catch (err) {
      console.error('Failed to load violations:', err);
    } finally {
      setLoading(false);
    }
  }, [page, filterType, searchPlate]);

  useEffect(() => {
    // eslint-disable-next-line
    loadViolations();
  }, [loadViolations]);

  const handleSearch = () => {
    setPage(1);
    loadViolations();
  };


  return (
    <div className="p-8  min-h-screen">
      <div className="mb-8 animate-slide-up">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold flex items-center gap-3">
              <span className="text-[var(--accent-blue)]">Official Challan Book</span>
              <span className="badge badge-purple text-[10px]">BTP Partner Integration</span>
            </h1>
            <p className="text-sm text-[var(--text-secondary)] mt-1">
              {total} verified records synced with Bengaluru Traffic Police
            </p>
          </div>
          <div className="flex items-center gap-3">
            <div className="px-3 py-1.5 rounded-lg bg-[rgba(46,213,115,0.1)] border border-[rgba(46,213,115,0.2)] flex items-center gap-2 text-xs font-semibold text-[var(--accent-green)]">
              <span className="w-2 h-2 rounded-full bg-[var(--accent-green)] animate-pulse" />
              Live Sync Active
            </div>
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="border bg-[#FFFFFF] rounded-md shadow-sm border-[var(--border-color)] p-4 mb-6 animate-slide-up" style={{ animationDelay: '0.1s' }}>
        <div className="flex flex-wrap items-center gap-3">
          {/* Search */}
          <div className="flex-1 min-w-[200px] relative">
            <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-[var(--text-secondary)]" />
            <input
              type="text"
              placeholder="Search by plate number..."
              value={searchPlate}
              onChange={(e) => setSearchPlate(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
              className="w-full pl-10 pr-4 py-2.5 rounded-xl bg-[var(--bg-primary)] border border-[var(--border-color)] text-sm text-[var(--text-primary)] placeholder:text-[var(--text-secondary)] focus:outline-none focus:border-[var(--accent-blue)] transition-colors"
            />
          </div>

          {/* Type filter */}
          <div className="relative">
            <Filter className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-[var(--text-secondary)]" />
            <select
              value={filterType}
              onChange={(e) => { setFilterType(e.target.value); setPage(1); }}
              className="pl-10 pr-8 py-2.5 rounded-xl bg-[var(--bg-primary)] border border-[var(--border-color)] text-sm text-[var(--text-primary)] focus:outline-none focus:border-[var(--accent-blue)] appearance-none cursor-pointer"
            >
              <option value="">All Types</option>
              {Object.entries(VIOLATION_LABELS).map(([key, label]) => (
                <option key={key} value={key}>{label}</option>
              ))}
            </select>
          </div>

          <button className="btn-primary" onClick={handleSearch}>
            Search
          </button>
        </div>
      </div>

      {/* Table */}
      <div className="border bg-[#FFFFFF] rounded-md shadow-sm border-[var(--border-color)] overflow-hidden animate-slide-up" style={{ animationDelay: '0.2s' }}>
        {loading ? (
          <div className="p-8">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="shimmer h-16 rounded-lg mb-3" />
            ))}
          </div>
        ) : (
          <>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-[var(--border-color)]">
                    <th className="text-left text-xs font-semibold text-[var(--text-secondary)] uppercase tracking-wider px-5 py-4">ID</th>
                    <th className="text-left text-xs font-semibold text-[var(--text-secondary)] uppercase tracking-wider px-5 py-4">Type</th>
                    <th className="text-left text-xs font-semibold text-[var(--text-secondary)] uppercase tracking-wider px-5 py-4">Confidence</th>
                    <th className="text-left text-xs font-semibold text-[var(--text-secondary)] uppercase tracking-wider px-5 py-4">Plate</th>
                    <th className="text-left text-xs font-semibold text-[var(--text-secondary)] uppercase tracking-wider px-5 py-4">Time</th>
                    <th className="text-left text-xs font-semibold text-[var(--text-secondary)] uppercase tracking-wider px-5 py-4">Status</th>
                    <th className="text-left text-xs font-semibold text-[var(--text-secondary)] uppercase tracking-wider px-5 py-4">Evidence</th>
                  </tr>
                </thead>
                <tbody>
                  {violations.map((v) => (
                    <tr
                      key={v.id}
                      className="border-b border-[var(--border-color)] last:border-0 hover:bg-[var(--bg-card-hover)] transition-colors cursor-pointer"
                      onClick={() => setSelectedViolation(v)}
                    >
                      <td className="px-5 py-4">
                        <span className="text-xs font-mono text-[var(--text-secondary)]">
                          AST-{v.id.toString().padStart(5, '0')}
                        </span>
                      </td>
                      <td className="px-5 py-4">
                        <ViolationBadge type={v.type} size="sm" />
                      </td>
                      <td className="px-5 py-4 w-40">
                        <ConfidenceMeter value={v.confidence} size="sm" />
                      </td>
                      <td className="px-5 py-4">
                        {v.plate_text ? (
                          <span className="font-mono text-sm font-bold text-[var(--accent-cyan)]">
                            {v.plate_text}
                          </span>
                        ) : (
                          <span className="text-xs text-[var(--text-secondary)]">—</span>
                        )}
                      </td>
                      <td className="px-5 py-4">
                        <span className="text-xs text-[var(--text-secondary)]">
                          {new Date(v.timestamp).toLocaleString()}
                        </span>
                      </td>
                      <td className="px-5 py-4">
                        <span className="badge badge-green text-[10px]">Challan Issued</span>
                      </td>
                      <td className="px-5 py-4">
                        {v.evidence_url ? (
                          <a
                            href={`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}${v.evidence_url}`}
                            target="_blank"
                            rel="noopener"
                            className="text-xs text-[var(--accent-blue)] hover:underline flex items-center gap-1"
                            onClick={(e) => e.stopPropagation()}
                          >
                            <ExternalLink className="w-3 h-3" /> View
                          </a>
                        ) : (
                          <span className="text-xs text-[var(--text-secondary)]">—</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Pagination */}
            <div className="flex items-center justify-between px-5 py-4 border-t border-[var(--border-color)] bg-[#FAFBFC]">
              <span className="text-xs text-[var(--text-secondary)] font-medium">
                Showing {(page - 1) * 15 + 1}–{Math.min(page * 15, total)} of {total}
              </span>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setPage(p => Math.max(1, p - 1))}
                  disabled={page === 1}
                  className="p-1.5 rounded bg-white border border-[var(--border-color)] disabled:opacity-50 hover:border-[var(--accent-blue)] transition-colors"
                >
                  <ChevronLeft className="w-4 h-4" />
                </button>
                <span className="text-xs font-semibold px-2">
                  {page} / {totalPages}
                </span>
                <button
                  onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                  disabled={page === totalPages}
                  className="p-1.5 rounded bg-white border border-[var(--border-color)] disabled:opacity-50 hover:border-[var(--accent-blue)] transition-colors"
                >
                  <ChevronRight className="w-4 h-4" />
                </button>
              </div>
            </div>
          </>
        )}
      </div>

      {/* Detail Modal */}
      {selectedViolation && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50" onClick={() => setSelectedViolation(null)}>
          <div className="bg-white rounded shadow-lg border border-[var(--border-color)] w-full max-w-2xl mx-4 max-h-[90vh] flex flex-col" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center justify-between p-4 border-b border-[var(--border-color)] bg-[#F8F9FA]">
              <h3 className="font-bold text-lg text-[var(--text-primary)]">Violation Review: AST-{selectedViolation.id.toString().padStart(5, '0')}</h3>
              <button onClick={() => setSelectedViolation(null)} className="p-1 hover:bg-[#E2E8F0] rounded text-[var(--text-secondary)]">
                <X className="w-5 h-5" />
              </button>
            </div>
            
            <div className="p-6 overflow-y-auto space-y-6">
              {/* Top Banner */}
              <div className="flex items-center gap-4 p-4 rounded border border-[var(--border-color)] bg-[#F8F9FA]">
                <ViolationBadge type={selectedViolation.type} size="md" />
                <div className="flex-1">
                  <p className="text-xs text-[var(--text-secondary)] font-bold uppercase">Confidence Score</p>
                  <ConfidenceMeter value={selectedViolation.confidence} size="md" />
                </div>
              </div>
              
              <div className="grid grid-cols-2 gap-6">
                <div>
                  <h4 className="text-xs font-bold text-[var(--text-secondary)] uppercase border-b border-[var(--border-color)] pb-2 mb-3">Violation Details</h4>
                  <p className="text-sm font-medium text-[var(--text-primary)] mb-4">{selectedViolation.description}</p>
                  
                  {selectedViolation.plate_text && (
                    <div className="mb-4">
                      <p className="text-xs font-bold text-[var(--text-secondary)] uppercase mb-1">Detected License Plate</p>
                      <div className="inline-block px-3 py-1.5 border-2 border-[var(--text-primary)] rounded bg-[#FAFBFC] font-mono text-lg font-bold">
                        {selectedViolation.plate_text}
                      </div>
                    </div>
                  )}

                  <div className="space-y-3 mt-4">
                    <div>
                      <p className="text-xs font-bold text-[var(--text-secondary)] uppercase">Timestamp</p>
                      <p className="text-sm font-medium">{new Date(selectedViolation.timestamp).toLocaleString()}</p>
                    </div>
                    <div>
                      <p className="text-xs font-bold text-[var(--text-secondary)] uppercase">Location Data</p>
                      <p className="text-sm font-medium flex items-center gap-1">
                        MG Road Junction (Verified)
                      </p>
                    </div>
                  </div>
                </div>

                <div>
                  <h4 className="text-xs font-bold text-[var(--text-secondary)] uppercase border-b border-[var(--border-color)] pb-2 mb-3">Photographic Evidence</h4>
                  {selectedViolation.evidence_url ? (
                    <div className="border border-[var(--border-color)] rounded overflow-hidden bg-[#FAFBFC]">
                      <img
                        src={`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}${selectedViolation.evidence_url}`}
                        alt="Evidence"
                        className="w-full h-auto"
                      />
                    </div>
                  ) : (
                    <div className="p-8 border border-[var(--border-color)] rounded bg-[#FAFBFC] flex flex-col items-center justify-center text-[var(--text-secondary)]">
                      <AlertTriangle className="w-8 h-8 mb-2" />
                      <p className="text-sm font-medium">Evidence image not found</p>
                    </div>
                  )}
                </div>
              </div>
            </div>

            <div className="p-4 border-t border-[var(--border-color)] bg-[#F8F9FA] flex gap-3 justify-end">
              <button
                onClick={() => setSelectedViolation(null)}
                className="btn-secondary"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
