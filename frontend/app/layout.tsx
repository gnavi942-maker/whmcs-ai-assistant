import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "WHMCS AI Assistant Pro - Enterprise Chat Agent",
  description: "An enterprise-grade sales assistant and support chatbot widget for WHMCS digital products sites.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <head>
        <link rel="icon" href="/favicon.ico" sizes="any" />
      </head>
      <body className="antialiased min-h-screen">
        {children}
      </body>
    </html>
  );
}
