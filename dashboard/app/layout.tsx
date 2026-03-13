import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { Sidebar } from "@/components/Sidebar";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Open Grace AI OS | Control Plane",
  description: "Next-generation autonomous agent orchestration system",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body className={`${inter.className} bg-slate-950 text-slate-200 antialiased`}>
        <div className="flex h-screen overflow-hidden">
          <Sidebar />
          <main className="flex-1 overflow-y-auto p-8 relative">
             {/* Background mesh gradient for premium feel */}
            <div className="absolute top-0 left-0 w-full h-full pointer-events-none opacity-20 overflow-hidden">
              <div className="absolute -top-[10%] -left-[10%] w-[40%] h-[40%] bg-blue-600 rounded-full blur-[120px]"></div>
              <div className="absolute top-[20%] -right-[10%] w-[35%] h-[35%] bg-purple-600 rounded-full blur-[120px]"></div>
              <div className="absolute -bottom-[10%] left-[20%] w-[30%] h-[30%] bg-indigo-600 rounded-full blur-[120px]"></div>
            </div>
            
            <div className="relative z-10 w-full max-w-7xl mx-auto">
              {children}
            </div>
          </main>
        </div>
      </body>
    </html>
  );
}
