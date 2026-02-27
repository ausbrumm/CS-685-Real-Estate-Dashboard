// components/Header.jsx
"use client";
import Link from "next/link";
import { useEffect, useState } from "react";

const Header = () => {
  const [isScrolled, setIsScrolled] = useState(false);
  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 10);
    };
    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  return (
    <header
      className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 flex items-center justify-between sm:justify-around
        ${
          isScrolled
            ? "bg-blue-600/90 backdrop-blur-md h-12 shadow-lg"
            : "bg-blue-500 h-16 shadow-md"
        }`}
    >
      <div className="flex items-center">
        <Link href="/" className="text-white font-bold hover:text-black">
          Home
        </Link>
      </div>
      <nav className="hidden sm:flex gap-12">
        <Link href="/about" className="text-white hover:text-black">
          About
        </Link>
        <Link href="/historical" className="text-white hover:text-black">
          Historial
        </Link>
        <Link href="/predictions" className="text-white hover:text-black">
          Predictions
        </Link>
      </nav>
      <button className="sm:hidden text-gray-600 hover:text-indigo-600">
        <svg
          className="h-6 w-6"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth="2"
            d="M4 6h16M4 12h16m-7 6h7"
          />
        </svg>
      </button>
    </header>
  );
};

export default Header;
