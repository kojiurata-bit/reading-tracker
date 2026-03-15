import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "読書トラッカーβ",
  description: "読書記録を管理するアプリ",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ja">
      <body className="antialiased">{children}</body>
    </html>
  );
}
