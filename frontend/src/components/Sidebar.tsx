'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';

const navItems = [
  { href: '/upload', label: 'Upload Video', type: 'speed' },
  { href: '/violations', label: 'Violation Dashboard', type: 'wrong-way' },
  { href: '/challans', label: 'Challan Book', type: 'street' },
  { href: '/live', label: 'Live Stream', type: 'caution' },
];

export default function Sidebar() {
  const pathname = usePathname();



  return (
    <aside className="w-[320px] h-screen overflow-y-auto overflow-x-hidden flex flex-col items-center pt-8 pb-12 relative shrink-0 no-scrollbar">
      
      {/* The Metal Pole */}
      <div className="absolute top-0 bottom-0 w-[40px] bg-gradient-to-r from-[#888] via-[#e0e0e0] to-[#555] shadow-[10px_0_20px_rgba(0,0,0,0.3)] z-0 border-x border-[#444] rounded-t-full">
         {/* Bolt holes texture */}
         <div className="w-full h-full opacity-30 flex flex-col items-center py-10 space-y-[40px]">
           {[...Array(20)].map((_, i) => (
             <div key={i} className="w-2 h-2 rounded-full bg-black shadow-[inset_0_1px_3px_rgba(255,255,255,0.5)]" />
           ))}
         </div>
      </div>

      {/* Signs Container */}
      <div className="z-10 w-full flex flex-col items-center space-y-8 mt-10">
        
        {/* Top Decor: Traffic Light */}
        <div className="mb-4 bg-[#222] p-3 rounded-2xl border-4 border-[#111] shadow-[0_20px_40px_rgba(0,0,0,0.5)] flex flex-col gap-3 relative">
          <div className="absolute -top-3 left-1/2 -translate-x-1/2 w-4 h-4 rounded-full bg-[#111]" />
          <div className="w-10 h-10 rounded-full border-2 border-black bg-[#ff3b30] shadow-[0_0_20px_rgba(255,59,48,0.2),inset_0_0_10px_rgba(0,0,0,0.5)]" />
          <div className="w-10 h-10 rounded-full border-2 border-black bg-[#ffcc00] shadow-[0_0_30px_rgba(255,204,0,0.8),inset_0_0_10px_rgba(255,255,255,0.5)] animate-pulse" />
          <div className="w-10 h-10 rounded-full border-2 border-black bg-[#154c21] shadow-[inset_0_0_10px_rgba(0,0,0,0.8)]" />
        </div>

        {/* Navigation Signs */}
        {navItems.map((item) => {
          const isActive = pathname === item.href;
          
          if (item.type === 'speed') {
            return (
              <Link key={item.href} href={item.href} className={`relative group transition-transform ${isActive ? 'scale-110' : 'hover:scale-105'} origin-center`}>
                {/* Mounting Brackets */}
                <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[80px] h-4 bg-[#444] z-[-1]" />
                <div className="bg-white border-[6px] border-black rounded-lg p-3 w-[160px] h-[180px] flex flex-col items-center justify-center text-center shadow-[0_15px_30px_rgba(0,0,0,0.4)]">
                  <span className="text-black font-black text-xl leading-tight uppercase tracking-wide">SPEED<br/>LIMIT</span>
                  <span className="text-black font-black text-4xl mt-2">25</span>
                  <span className="text-black font-bold text-[10px] mt-4 uppercase leading-none border-t-2 border-black pt-1">{item.label}</span>
                </div>
                {isActive && <div className="absolute -inset-2 bg-white/20 rounded-xl blur-lg pointer-events-none" />}
              </Link>
            );
          }

          if (item.type === 'wrong-way') {
            return (
              <Link key={item.href} href={item.href} className={`relative group transition-transform ${isActive ? 'scale-110' : 'hover:scale-105'} origin-center -rotate-3`}>
                <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[80px] h-4 bg-[#444] z-[-1]" />
                <div className="bg-[#cd1719] border-4 border-white rounded-md p-2 w-[220px] flex flex-col items-center justify-center text-center shadow-[0_15px_30px_rgba(0,0,0,0.4)] ring-4 ring-[#cd1719]">
                  <span className="text-white font-black text-2xl uppercase tracking-widest">{item.label.split(' ')[0]}</span>
                  <span className="text-white font-black text-xl uppercase tracking-widest">{item.label.split(' ')[1]}</span>
                </div>
                {isActive && <div className="absolute -inset-2 bg-red-500/30 rounded-xl blur-lg pointer-events-none" />}
              </Link>
            );
          }

          if (item.type === 'street') {
            return (
              <Link key={item.href} href={item.href} className={`relative group transition-transform ${isActive ? 'scale-110' : 'hover:scale-105'} origin-center ml-12 rotate-2`}>
                <div className="absolute top-1/2 -left-6 -translate-y-1/2 w-12 h-4 bg-[#444] z-[-1]" />
                <div className="bg-[#007b3c] border-2 border-white rounded p-3 w-[240px] flex flex-col items-start justify-center text-left shadow-[0_15px_30px_rgba(0,0,0,0.4)]">
                  <div className="flex items-center gap-2">
                    <span className="text-white font-bold text-sm bg-[#005a2b] px-1 rounded">PL</span>
                    <span className="text-white font-bold text-sm bg-[#005a2b] px-1 rounded">4100</span>
                  </div>
                  <span className="text-white font-black text-3xl capitalize tracking-tight mt-1" style={{ fontFamily: 'Arial, sans-serif' }}>{item.label}</span>
                </div>
                {isActive && <div className="absolute -inset-2 bg-green-500/30 rounded-xl blur-lg pointer-events-none" />}
              </Link>
            );
          }

          if (item.type === 'caution') {
            return (
              <Link key={item.href} href={item.href} className={`relative group transition-transform ${isActive ? 'scale-110' : 'hover:scale-105'} origin-center mt-10`}>
                <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[80px] h-4 bg-[#444] z-[-1]" />
                <div className="w-[180px] h-[180px] rotate-45 bg-[#f68f1e] border-8 border-black rounded-xl flex items-center justify-center shadow-[0_15px_30px_rgba(0,0,0,0.4)] overflow-hidden">
                   <div className="-rotate-45 flex flex-col items-center justify-center text-center p-2 w-[200px]">
                     <span className="text-black font-black text-2xl uppercase tracking-tighter leading-none mb-1">CAUTION</span>
                     <svg className="w-12 h-12 text-black mb-1" viewBox="0 0 24 24" fill="currentColor">
                        <path d="M15 4a2 2 0 11-4 0 2 2 0 014 0zM5.5 19v-5.5H4L7.5 7h4c1 0 1.5.5 2 1.5l1.5 2.5c1 1.5 2.5 2.5 4 2.5v-2c-1 0-2-.5-3-1.5l-1-2c-.5-1-1.5-1.5-2.5-1.5H8.5L5.5 19h2zm8 0v-4h2v4h-2zm-3-8l1.5-3 2 3-3.5 0z" />
                     </svg>
                     <span className="text-black font-black text-[11px] uppercase tracking-wider">{item.label}</span>
                   </div>
                </div>
                {isActive && <div className="absolute inset-0 bg-orange-500/30 rounded-full blur-2xl pointer-events-none" />}
              </Link>
            );
          }
        })}



      </div>
    </aside>
  );
}
