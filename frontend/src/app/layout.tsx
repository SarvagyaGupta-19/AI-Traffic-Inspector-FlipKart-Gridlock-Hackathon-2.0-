import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";


const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
});

export const metadata: Metadata = {
  title: "AI Traffic Inspector — Traffic Violation Detection",
  description: "AI-powered automated traffic violation detection and enforcement system",
  keywords: ["traffic", "violation", "detection", "AI", "computer vision", "YOLO"],
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body className={`${inter.variable} font-sans antialiased bg-[#060918] text-white min-h-screen`}>
        {children}
      </body>
    </html>
  );
}
