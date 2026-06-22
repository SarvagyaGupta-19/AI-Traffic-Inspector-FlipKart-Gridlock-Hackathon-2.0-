'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import api from '@/lib/api';
import { Lock, User, ArrowRight } from 'lucide-react';

export default function LoginPage() {
  const router = useRouter();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      await api.login(username, password);
      // On success, redirect to dashboard
      router.push('/upload');
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError('Login failed. Check your credentials.');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <style jsx global>{`
        @import url('https://fonts.googleapis.com/css2?family=Caveat:wght@700&family=Jost:wght@400;500;700&display=swap');
      `}</style>
      
      <div className="min-h-screen flex flex-col items-center justify-center bg-gradient-to-b from-[#e8b598] via-[#f2c19e] to-[#7f7d9c] relative overflow-hidden font-['Jost',sans-serif]">
        
        {/* Noise Overlay */}
        <div 
          className="absolute inset-0 opacity-20 pointer-events-none mix-blend-overlay z-0" 
          style={{ backgroundImage: 'url("data:image/svg+xml,%3Csvg viewBox=%220 0 400 400%22 xmlns=%22http://www.w3.org/2000/svg%22%3E%3Cfilter id=%22noiseFilter%22%3E%3CfeTurbulence type=%22fractalNoise%22 baseFrequency=%220.8%22 numOctaves=%223%22 stitchTiles=%22stitch%22/%3E%3C/filter%3E%3Crect width=%22100%25%22 height=%22100%25%22 filter=%22url(%23noiseFilter)%22/%3E%3C/svg%3E")' }} 
        />

        {/* Large Brush Title */}
        <div className="absolute top-[5%] sm:top-[2%] w-full text-center z-10 pointer-events-none">
          <h1 className="text-[120px] sm:text-[220px] text-[#fbf0a9] drop-shadow-[0_10px_20px_rgba(0,0,0,0.15)] leading-none" style={{ fontFamily: "'Caveat', cursive", transform: 'rotate(-4deg)' }}>
            ACCESS
          </h1>
        </div>

        {/* Top left and right aesthetic text */}
        <div className="absolute top-6 left-6 max-w-[250px] z-10 text-[#4a3b38] text-xs sm:text-sm font-bold uppercase tracking-[0.2em] leading-relaxed hidden md:block">
          Yearning for security and order.<br/>
          So don&apos;t be afraid of the gridlock.
        </div>
        
        <div className="absolute top-[30%] right-6 [writing-mode:vertical-rl] rotate-180 z-10 text-[#4a3b38] text-xs sm:text-sm font-bold uppercase tracking-[0.2em] leading-relaxed hidden md:block">
          AI TRAFFIC INSPECTOR
        </div>

        {/* Rearview Mirror Container */}
        <div className="relative z-20 w-[90%] max-w-[420px] mt-24 sm:mt-32 rounded-[2.5rem] sm:rounded-[3.5rem] border-[16px] sm:border-[24px] border-[#111] bg-[#1a1a1a] shadow-[0_40px_80px_rgba(0,0,0,0.4),0_10px_30px_rgba(0,0,0,0.3)] overflow-hidden flex flex-col justify-end ring-1 ring-black/50">
          
          {/* Mirror Reflection Background (Sunset Landscape) */}
          <div className="absolute inset-0 bg-gradient-to-b from-[#f5d198] via-[#eba48b] to-[#453754] z-0 pointer-events-none overflow-hidden">
            
            {/* The Sun */}
            <div className="absolute top-[25%] left-[20%] w-24 h-24 sm:w-32 sm:h-32 bg-[#ffecb3] rounded-full blur-[2px] shadow-[0_0_50px_#ffecb3]" />
            
            {/* Clouds / Silhouette Mountains */}
            <div className="absolute bottom-[35%] w-[150%] -left-[25%] h-32 bg-[#e28173] blur-[8px] opacity-70" style={{ clipPath: 'ellipse(60% 40% at 50% 100%)' }} />
            <div className="absolute bottom-[30%] w-[120%] -left-[10%] h-24 bg-[#392e47] blur-[2px]" style={{ clipPath: 'polygon(0% 100%, 15% 30%, 35% 70%, 60% 10%, 85% 60%, 100% 20%, 100% 100%)' }} />
            
            {/* Ocean / Road */}
            <div className="absolute bottom-0 w-full h-[40%] bg-gradient-to-t from-[#141524] to-[#2c2f4c] border-t-[3px] border-[#141524]/50">
               {/* Reflection highlights on water/road */}
               <div className="absolute top-0 left-[20%] w-32 h-full bg-gradient-to-b from-[#ffecb3]/20 to-transparent blur-md transform skew-x-12" />
            </div>

            {/* Powerlines (diagonal lines) */}
            <div className="absolute top-[35%] left-0 w-full h-[1px] bg-[#111] opacity-60 rotate-12 origin-left shadow-sm" />
            <div className="absolute top-[40%] left-0 w-full h-[1px] bg-[#111] opacity-60 rotate-12 origin-left shadow-sm" />

            {/* Mirror Inner Shadow for depth */}
            <div className="absolute inset-0 shadow-[inset_0_0_40px_rgba(0,0,0,0.8),inset_0_20px_20px_rgba(0,0,0,0.3)] mix-blend-multiply pointer-events-none" />
            <div className="absolute top-0 left-0 w-full h-full bg-gradient-to-bl from-white/10 to-transparent pointer-events-none" />
          </div>

          {/* Login Form over the reflection */}
          <div className="relative z-10 w-full px-8 pb-8 pt-20 bg-gradient-to-t from-[#0d0d16] via-[#0d0d16]/80 to-transparent">
            
            {error && (
              <div className="mb-6 p-3 bg-red-500/20 backdrop-blur-md border border-red-500/50 rounded-lg text-[#ff9999] text-xs text-center font-bold tracking-wide">
                {error}
              </div>
            )}

            <form onSubmit={handleLogin} className="space-y-4">
              <div className="space-y-1">
                <label className="text-[10px] font-bold text-[#b4b7cc] uppercase tracking-[0.15em]">Officer ID</label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                    <User className="h-4 w-4 text-[#8a8d9e]" />
                  </div>
                  <input
                    type="text"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    className="w-full bg-black/40 backdrop-blur-md border border-white/10 rounded-xl py-3 pl-11 pr-4 text-white text-sm placeholder-white/30 focus:outline-none focus:ring-2 focus:ring-[#eba48b] focus:border-transparent transition-all shadow-[inset_0_2px_4px_rgba(0,0,0,0.5)]"
                    placeholder="Enter your ID"
                    required
                  />
                </div>
              </div>

              <div className="space-y-1">
                <label className="text-[10px] font-bold text-[#b4b7cc] uppercase tracking-[0.15em]">Password</label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                    <Lock className="h-4 w-4 text-[#8a8d9e]" />
                  </div>
                  <input
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="w-full bg-black/40 backdrop-blur-md border border-white/10 rounded-xl py-3 pl-11 pr-4 text-white text-sm placeholder-white/30 focus:outline-none focus:ring-2 focus:ring-[#eba48b] focus:border-transparent transition-all shadow-[inset_0_2px_4px_rgba(0,0,0,0.5)]"
                    placeholder="Enter password"
                    required
                  />
                </div>
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full bg-gradient-to-r from-[#eba48b] to-[#e28173] hover:from-[#f2b39c] hover:to-[#eb8e80] text-[#1a1a1a] font-black text-sm uppercase tracking-[0.2em] py-3.5 rounded-xl shadow-[0_10px_20px_rgba(226,129,115,0.3)] transition-all active:scale-[0.98] disabled:opacity-70 disabled:cursor-not-allowed mt-6 flex items-center justify-center gap-2 group"
              >
                {loading ? 'Authenticating...' : 'Secure Login'}
                {!loading && <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />}
              </button>
            </form>
          </div>
        </div>

        {/* Cinematic Footer Text */}
        <div className="mt-8 mb-6 z-10 w-full px-6 flex flex-col md:flex-row justify-between items-center text-[#1a1a1a] opacity-80 gap-4">
          <div className="text-xs sm:text-sm font-bold tracking-[0.3em] uppercase">
            MEITU Kpacota
          </div>
          <div className="text-sm sm:text-base font-black tracking-[0.4em] uppercase text-center">
            A SYSTEM BY BENGALURU TRAFFIC POLICE
          </div>
          <div className="text-xs sm:text-sm font-bold tracking-[0.3em] uppercase">
            PICTURE фOTO
          </div>
        </div>
        
        {/* Story Text */}
        <div className="z-10 max-w-2xl text-center px-6 pb-6 pointer-events-none">
          <p className="text-[#3a2c2a] text-xs sm:text-sm uppercase font-bold tracking-[0.15em] leading-relaxed opacity-70">
            A red sun sprang up on the sea, bright and dazzling. The traffic flowed from the urban gridlock instantly filled with golden glow. The cameras watched from dawn to dusk.
          </p>
        </div>
      </div>
    </>
  );
}
