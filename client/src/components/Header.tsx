// components/Header.jsx

import Link from "next/link";

const Header = () => {
  return (
    <header className="bg-blue-500 h-16 shadow-md flex items-center justify-between sm:justify-around sticky top-0 z-10">
      <div className="flex items-center">
        <Link href="/" className="text-white font-bold hover:text-black">
          Home
        </Link>
      </div>
      <nav className="hidden sm:flex gap-12">
        <Link href="/about" className="text-white hover:text-black">
          About
        </Link>
        <Link href="/dashboard" className="text-white hover:text-black">
          Dashboard
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
