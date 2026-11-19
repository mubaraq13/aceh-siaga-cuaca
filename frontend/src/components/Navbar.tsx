"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";

const NAV_ITEMS = [
  { href: "/", label: "Beranda" },
  { href: "/prakiraan", label: "Prakiraan Cuaca" },
  { href: "/peta", label: "Peta Interaktif" },
  { href: "/analisis", label: "Analisis Cuaca" },
  { href: "/machine-learning", label: "Machine Learning" },
  { href: "/peringatan-dini", label: "Peringatan Dini" },
  { href: "/edukasi", label: "Edukasi Kesiapsiagaan" },
];

export default function Navbar() {
  const pathname = usePathname();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [darkMode, setDarkMode] = useState(false);

  useEffect(() => {
    const savedTheme = window.localStorage.getItem("aceh_siaga_theme");
    if (savedTheme === "dark") {
      setDarkMode(true);
      document.documentElement.classList.add("dark");
    }
  }, []);

  const toggleTheme = () => {
    const nextDark = !darkMode;
    setDarkMode(nextDark);
    if (nextDark) {
      document.documentElement.classList.add("dark");
      window.localStorage.setItem("aceh_siaga_theme", "dark");
    } else {
      document.documentElement.classList.remove("dark");
      window.localStorage.setItem("aceh_siaga_theme", "light");
    }
  };

  return (
    <header className="bg-[#102A43] text-white border-b border-[#173F5F] sticky top-0 z-50">
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:absolute focus:top-2 focus:left-2 focus:z-50 focus:bg-white focus:text-[#102A43] focus:px-4 focus:py-2 focus:font-bold"
      >
        Lewati ke konten utama
      </a>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between min-h-[68px] py-2 gap-4">
          <div>
            <Link
              href="/"
              className="text-lg sm:text-xl font-extrabold tracking-tight text-white block"
            >
              ACEH SIAGA CUACA
            </Link>
            <p className="text-xs text-[#DCEEFF] hidden sm:block">
              Informasi Cuaca, Kesiapsiagaan, dan Perlindungan Masyarakat Aceh.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={toggleTheme}
              aria-label={darkMode ? "Aktifkan Mode Terang" : "Aktifkan Mode Gelap"}
              className="min-h-[44px] px-3 py-2 text-xs font-semibold bg-[#173F5F] hover:bg-[#DCEEFF] hover:text-[#102A43] text-white rounded-md transition-colors"
            >
              {darkMode ? "Mode Terang" : "Mode Gelap"}
            </button>

            <button
              type="button"
              onClick={() => setMobileMenuOpen((prev) => !prev)}
              aria-expanded={mobileMenuOpen}
              aria-controls="mobile-nav-menu"
              className="lg:hidden min-h-[44px] px-3 py-2 text-xs font-bold bg-[#173F5F] text-white rounded-md"
            >
              {mobileMenuOpen ? "Tutup Menu" : "Menu Navigasi"}
            </button>
          </div>
        </div>

        {/* Navigasi Desktop */}
        <nav
          aria-label="Navigasi Utama"
          className="hidden lg:flex items-center gap-1 pb-2 overflow-x-auto"
        >
          {NAV_ITEMS.map((item) => {
            const isActive = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                aria-current={isActive ? "page" : undefined}
                className={`min-h-[44px] px-3.5 py-2.5 text-sm font-semibold rounded-md flex items-center transition-colors ${
                  isActive
                    ? "bg-[#DCEEFF] text-[#102A43]"
                    : "text-[#F5F8FC] hover:bg-[#173F5F]"
                }`}
              >
                {item.label}
              </Link>
            );
          })}
        </nav>

        {/* Navigasi Mobile */}
        {mobileMenuOpen && (
          <nav
            id="mobile-nav-menu"
            aria-label="Navigasi Seluler"
            className="lg:hidden py-3 border-t border-[#173F5F] flex flex-col gap-1"
          >
            {NAV_ITEMS.map((item) => {
              const isActive = pathname === item.href;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  onClick={() => setMobileMenuOpen(false)}
                  aria-current={isActive ? "page" : undefined}
                  className={`min-h-[44px] px-4 py-2.5 text-sm font-semibold rounded-md flex items-center ${
                    isActive
                      ? "bg-[#DCEEFF] text-[#102A43]"
                      : "text-white hover:bg-[#173F5F]"
                  }`}
                >
                  {item.label}
                </Link>
              );
            })}
          </nav>
        )}
      </div>
    </header>
  );
}
