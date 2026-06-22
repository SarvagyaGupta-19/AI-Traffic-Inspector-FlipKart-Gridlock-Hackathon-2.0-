import Link from 'next/link';

export default function LandingPage() {
  return (
    <div className="relative min-h-screen bg-[#07707b] overflow-hidden selection:bg-[#f4a896] selection:text-[#07707b] flex flex-col" style={{ fontFamily: 'Impact, "Arial Black", sans-serif' }}>
      {/* Heavy Grain/Noise Texture */}
      <div 
        className="absolute inset-0 opacity-20 pointer-events-none mix-blend-overlay z-0" 
        style={{ 
          backgroundImage: 'url("data:image/svg+xml,%3Csvg viewBox=%220 0 400 400%22 xmlns=%22http://www.w3.org/2000/svg%22%3E%3Cfilter id=%22noiseFilter%22%3E%3CfeTurbulence type=%22fractalNoise%22 baseFrequency=%220.8%22 numOctaves=%223%22 stitchTiles=%22stitch%22/%3E%3C/filter%3E%3Crect width=%22100%25%22 height=%22100%25%22 filter=%22url(%23noiseFilter)%22/%3E%3C/svg%3E")' 
        }} 
      />
      
      {/* Peachy Cloud Gradient at bottom to mimic the image */}
      <div className="absolute -bottom-[20%] -left-[10%] w-[120%] h-[70%] bg-gradient-to-t from-[#f4a896] via-[#f4a896]/40 to-transparent opacity-80 mix-blend-screen pointer-events-none blur-[80px] z-0" />
      <div className="absolute -bottom-[30%] -left-[20%] w-[80%] h-[80%] bg-[#f4a896] opacity-60 mix-blend-screen pointer-events-none blur-[120px] rounded-full z-0" />

      {/* Header with small technical text */}
      <header className="absolute top-0 left-0 w-full z-20 flex justify-between items-start p-6 md:p-10 text-[#f0f0f0] uppercase text-xs md:text-sm tracking-[0.15em] leading-relaxed font-sans font-bold pointer-events-none">
        <div className="max-w-[320px]">
          EVERY SHIFTING LIGHT SERVES AS A REMINDER OF THE RULES WE&apos;VE MADE AND THE SAFE PATHS WE MUST EMBARK UPON.
        </div>
        
        <div className="absolute left-1/2 -translate-x-1/2 top-6 md:top-8 text-center">
          <h1 className="text-[#f4f4f4] font-black uppercase tracking-[0.3em] text-lg md:text-2xl drop-shadow-md whitespace-nowrap">
            AI TRAFFIC INSPECTOR
          </h1>
        </div>

        <div className="hidden md:block max-w-[500px] [writing-mode:vertical-rl] rotate-180 absolute right-6 md:right-10 top-6 md:top-10 opacity-80">
          IN THE SAME WAY THAT A TRAFFIC LIGHT DIRECTS THE FLOW OF TRAFFIC, OUR TECHNOLOGY STEERS THE SAFETY OF OUR CITY.
        </div>
      </header>

      {/* Central Poster Element */}
      <main className="relative z-10 flex-1 flex items-center justify-center w-full min-h-[50vh]">
        
        {/* Layer 1: Background Text */}
        <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none select-none z-10">
           <div className="flex flex-col items-center text-center p-4 sm:p-[3vh]">
             <div className="h-20 sm:h-[14vh] mb-4 sm:mb-[2.5vh] flex items-center justify-center">
               <h1 className="text-[120px] sm:text-[20vh] leading-[0.75] text-[#f4f4f4] tracking-tighter uppercase" style={{ textShadow: '0px 10px 30px rgba(0,0,0,0.15)' }}>STOP</h1>
             </div>
             <div className="h-20 sm:h-[14vh] mb-4 sm:mb-[2.5vh] flex items-center justify-center">
               <h1 className="text-[120px] sm:text-[20vh] leading-[0.75] text-[#f4f4f4] tracking-tighter uppercase" style={{ textShadow: '0px 10px 30px rgba(0,0,0,0.15)' }}>WAIT</h1>
             </div>
             <div className="h-20 sm:h-[14vh] flex items-center justify-center">
               <h1 className="text-[120px] sm:text-[20vh] leading-[0.75] text-[#f4f4f4] tracking-tighter uppercase" style={{ textShadow: '0px 10px 30px rgba(0,0,0,0.15)' }}>GO</h1>
             </div>
           </div>
        </div>

        {/* Layer 2: Traffic Light (CSS) */}
        <div className="relative z-20 flex flex-col items-center justify-center p-4 sm:p-[3vh] bg-[#121212] rounded-[30px] sm:rounded-[4vh] shadow-[20px_30px_60px_rgba(0,0,0,0.4),inset_-2px_-2px_10px_rgba(255,255,255,0.05),inset_2px_2px_10px_rgba(0,0,0,0.5)] border border-[#222]">
          
          {/* Traffic Light Pole */}
          <div className="absolute -bottom-[15vh] w-8 sm:w-[4vh] h-[15vh] bg-gradient-to-r from-[#111] via-[#2a2a2a] to-[#0a0a0a] shadow-[10px_0_20px_rgba(0,0,0,0.3)] z-[-1]" />

          {/* Red Light */}
          <div className="w-20 h-20 sm:w-[14vh] sm:h-[14vh] rounded-full bg-[#ff3b30] border-4 border-[#000] shadow-[0_0_80px_rgba(255,59,48,0.8),inset_0_0_30px_rgba(255,255,255,0.4)] mb-4 sm:mb-[2.5vh] relative overflow-hidden flex items-center justify-center">
             <div className="absolute inset-0 opacity-30 mix-blend-overlay" style={{ backgroundImage: 'radial-gradient(rgba(255,255,255,0.4) 2px, transparent 2.5px)', backgroundSize: '8px 8px' }} />
             <div className="absolute top-[10%] left-[15%] w-[70%] h-[30%] bg-white/40 rounded-full blur-[4px] rotate-[-15deg]" />
          </div>

          {/* Yellow Light */}
          <div className="w-20 h-20 sm:w-[14vh] sm:h-[14vh] rounded-full bg-[#ffcc00] border-4 border-[#000] shadow-[0_0_80px_rgba(255,204,0,0.8),inset_0_0_30px_rgba(255,255,255,0.5)] mb-4 sm:mb-[2.5vh] relative overflow-hidden flex items-center justify-center">
             <div className="absolute inset-0 opacity-30 mix-blend-overlay" style={{ backgroundImage: 'radial-gradient(rgba(255,255,255,0.4) 2px, transparent 2.5px)', backgroundSize: '8px 8px' }} />
             <div className="absolute top-[10%] left-[15%] w-[70%] h-[30%] bg-white/40 rounded-full blur-[4px] rotate-[-15deg]" />
          </div>

          {/* Green Light */}
          <div className="w-20 h-20 sm:w-[14vh] sm:h-[14vh] rounded-full bg-[#34c759] border-4 border-[#000] shadow-[0_0_80px_rgba(52,199,89,0.8),inset_0_0_30px_rgba(255,255,255,0.4)] relative overflow-hidden flex items-center justify-center">
             <div className="absolute inset-0 opacity-30 mix-blend-overlay" style={{ backgroundImage: 'radial-gradient(rgba(255,255,255,0.4) 2px, transparent 2.5px)', backgroundSize: '8px 8px' }} />
             <div className="absolute top-[10%] left-[15%] w-[70%] h-[30%] bg-white/40 rounded-full blur-[4px] rotate-[-15deg]" />
          </div>
        </div>

        {/* Layer 3: Foreground Outline Text */}
        <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none select-none z-30">
           <div className="flex flex-col items-center text-center p-4 sm:p-[3vh]">
             <div className="h-20 sm:h-[14vh] mb-4 sm:mb-[2.5vh] flex items-center justify-center">
               <h1 className="text-[120px] sm:text-[20vh] leading-[0.75] text-transparent tracking-tighter uppercase" style={{ WebkitTextStroke: '2px #f4f4f4' }}>STOP</h1>
             </div>
             <div className="h-20 sm:h-[14vh] mb-4 sm:mb-[2.5vh] flex items-center justify-center">
               <h1 className="text-[120px] sm:text-[20vh] leading-[0.75] text-transparent tracking-tighter uppercase" style={{ WebkitTextStroke: '2px #f4f4f4' }}>WAIT</h1>
             </div>
             <div className="h-20 sm:h-[14vh] flex items-center justify-center">
               <h1 className="text-[120px] sm:text-[20vh] leading-[0.75] text-transparent tracking-tighter uppercase" style={{ WebkitTextStroke: '2px #f4f4f4' }}>GO</h1>
             </div>
           </div>
        </div>
      </main>

      {/* Footer / CTA */}
      <footer className="relative z-40 p-6 sm:p-[4vh] flex justify-center mt-auto font-sans">
        <Link 
          href="/login"
          className="px-8 py-4 bg-[#f4f4f4] text-[#07707b] font-black uppercase tracking-[0.2em] text-sm sm:text-[2vh] hover:bg-[#f4a896] hover:text-[#111] transition-colors shadow-[6px_6px_0px_rgba(0,0,0,0.8)] border-2 border-[#111] active:translate-y-1 active:translate-x-1 active:shadow-[2px_2px_0px_rgba(0,0,0,0.8)]"
        >
          CLICK FOR OFFICER ACCESS
        </Link>
      </footer>
    </div>
  );
}
