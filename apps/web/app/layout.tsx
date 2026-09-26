import type { Metadata } from "next";
import "./globals.css";
export const metadata: Metadata = {
  title: "PALEGIC — Maritime Intelligence",
  description:
    "Evidence-led marine pollution investigations. Historical observations, transparent source ranking and trajectory replay.",
};
export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
