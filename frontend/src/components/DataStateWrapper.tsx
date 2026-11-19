import React from "react";

interface DataStateWrapperProps {
  loading: boolean;
  error: string | null;
  isEmpty?: boolean;
  emptyMessage?: string;
  onRetry?: () => void;
  children: React.ReactNode;
}

export default function DataStateWrapper({
  loading,
  error,
  isEmpty = false,
  emptyMessage = "Data belum tersedia untuk kriteria yang dipilih.",
  onRetry,
  children,
}: DataStateWrapperProps) {
  if (loading) {
    return (
      <div
        role="status"
        aria-live="polite"
        className="border border-[#DCEEFF] dark:border-[#173F5F] bg-white dark:bg-[#102A43] p-6 rounded-md"
      >
        <p className="text-sm font-semibold text-[#102A43] dark:text-white">
          Sedang memuat data meteorologi Aceh...
        </p>
        <p className="mt-1 text-xs text-[#173F5F] dark:text-[#DCEEFF]">
          Mohon tunggu sebentar, sistem sedang memverifikasi pembaruan data terbaru.
        </p>
      </div>
    );
  }

  if (error) {
    return (
      <div
        role="alert"
        className="border-2 border-[#B42318] bg-white dark:bg-[#102A43] p-6 rounded-md"
      >
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <span className="inline-block px-2.5 py-1 text-xs font-bold bg-[#B42318] text-white rounded-sm">
              GANGGUAN PENGAMBILAN DATA
            </span>
            <h3 className="mt-2 text-base font-bold text-[#102A43] dark:text-white">
              Tidak dapat memuat informasi terkini dari server backend
            </h3>
            <p className="mt-1 text-sm text-[#173F5F] dark:text-[#DCEEFF]">
              Rincian teknis: {error}. Pastikan server FastAPI aktif pada port 8000.
            </p>
          </div>
          {onRetry && (
            <button
              type="button"
              onClick={onRetry}
              className="min-h-[44px] px-4 py-2 text-sm font-semibold bg-[#173F5F] hover:bg-[#102A43] text-white rounded-md shrink-0"
            >
              Muat Ulang Data Cuaca
            </button>
          )}
        </div>
      </div>
    );
  }

  if (isEmpty) {
    return (
      <div className="border border-[#DCEEFF] dark:border-[#173F5F] bg-white dark:bg-[#102A43] p-6 rounded-md">
        <p className="text-sm font-semibold text-[#102A43] dark:text-white">
          {emptyMessage}
        </p>
      </div>
    );
  }

  return <>{children}</>;
}
