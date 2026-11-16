import type { Metadata } from "next";
import { THEME_INIT_SCRIPT } from "../lib/theme";
import "./globals.css";

export const metadata: Metadata = {
  title: "EU AI Act Classifier",
  description: "Local EU AI Act intake cockpit",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  // The script sets data-theme on <html> before React hydrates, hence the suppression.
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: THEME_INIT_SCRIPT }} />
      </head>
      <body>{children}</body>
    </html>
  );
}
