import Header from "../components/Header";
import Footer from "../components/Footer";
import "./globals.css";

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="relative">
        <Header />
        <main className="relative flex flex-col min-h-screen items-center pt-20">
          {children}
        </main>
        <Footer />
      </body>
    </html>
  );
}
