import type { Metadata } from "next";
import { Onest } from "next/font/google";
const sans = Onest({ subsets: ["latin"], variable: "--font-sans", display: "swap" });
import "./globals.css";

export const metadata: Metadata = {
  title: "Skillroom \u2014 learn from people who do it",
  description: "Short video courses by working professionals. Resume anywhere, pass the quiz, earn a certificate.",
  icons: { icon: "/favicon.svg" },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${sans.variable}`}>
      <body>{children}</body>
    </html>
  );
}
