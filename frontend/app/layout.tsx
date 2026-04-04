import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "TrusOne Compliance Checklist",
  description: "Chemical compliance prototype for structured regulatory guidance.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
