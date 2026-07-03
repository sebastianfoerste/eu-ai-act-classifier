import type { Metadata } from "next";
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
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
