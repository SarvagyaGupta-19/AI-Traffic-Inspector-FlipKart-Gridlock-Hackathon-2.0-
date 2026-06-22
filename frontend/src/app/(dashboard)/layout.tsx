export default function DashboardLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <div className="flex h-screen overflow-hidden bg-[#87CEEB] font-sans relative selection:bg-[#fff] selection:text-[#000]">
      {/* Subtle cloud backdrop overlay */}
      <div 
        className="absolute inset-0 opacity-40 pointer-events-none mix-blend-overlay z-0" 
        style={{ backgroundImage: 'radial-gradient(circle at 50% 50%, #ffffff 0%, transparent 60%)', backgroundSize: '100% 100%' }} 
      />

      <div className="z-10 flex w-full h-full">
        <Sidebar />
        <main className="flex-1 overflow-y-auto p-4 sm:p-8">
          <div className="bg-white/90 backdrop-blur-xl border border-white/40 shadow-[0_20px_50px_rgba(0,0,0,0.1)] rounded-3xl min-h-full p-6">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}

import Sidebar from "@/components/Sidebar";
