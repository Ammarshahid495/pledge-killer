import React from 'react';
import { Link } from 'react-router-dom';
import { Navbar } from '../components/Navbar';
import {
  Shield,
  ArrowRight,
  CheckCircle2,
  FileCode2,
  Sparkles,
  EyeOff,
  Scale,
  Users,
} from 'lucide-react';

export const LandingPage: React.FC = () => {
  return (
    <div className="min-h-screen bg-olive-950 text-cream-100 flex flex-col relative overflow-hidden">
      <Navbar />

      {/* Decorative diagonal beige stripe reminiscent of the sneaker poster reference */}
      <div className="absolute -top-32 -right-32 w-[600px] h-[1200px] bg-gradient-to-b from-cream-200/10 via-cream-200/5 to-transparent rotate-12 pointer-events-none -z-0" />

      {/* Hero Section */}
      <section className="relative pt-16 pb-24 md:pt-28 md:pb-36 z-10">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="max-w-3xl">
            <div className="inline-flex items-center space-x-2 px-3.5 py-1.5 rounded-full bg-cream-200/10 border border-cream-200/20 text-cream-200 text-xs font-semibold mb-8 uppercase tracking-widest">
              <Sparkles className="w-3.5 h-3.5" />
              <span>Stanford MOSS Winnowing Engine</span>
            </div>

            <h1 className="text-5xl sm:text-7xl md:text-8xl font-display font-extrabold uppercase tracking-tight text-cream-200 leading-[0.95] mb-8">
              CHECK SIMILARITY.<br />
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-cream-200 via-cream-100 to-olive-300">
                KEEP CODE PRIVATE.
              </span>
            </h1>

            <p className="text-base sm:text-xl text-olive-300 mb-10 max-w-xl leading-relaxed font-sans">
              The first privacy-first, peer-to-peer code similarity detection platform.
              No teachers. No classroom owners. All participants have identical permissions.
            </p>

            <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-4">
              <Link
                to="/register"
                className="px-8 py-4 rounded-full bg-cream-200 hover:bg-cream-100 text-olive-950 font-display font-bold text-sm tracking-wider uppercase shadow-xl shadow-cream-200/15 flex items-center justify-center space-x-2 transition-all hover:scale-105"
              >
                <span>GET STARTED NOW</span>
                <ArrowRight className="w-4 h-4 stroke-[2.5]" />
              </Link>
              <Link
                to="/login"
                className="px-8 py-4 rounded-full bg-olive-900 hover:bg-olive-850 text-cream-200 font-display font-semibold text-sm tracking-wider uppercase border border-olive-700 transition flex items-center justify-center"
              >
                Sign In to Session
              </Link>
            </div>
          </div>

          {/* Quick Pillars */}
          <div className="mt-20 pt-8 border-t border-olive-700/80 grid grid-cols-1 sm:grid-cols-3 gap-6 text-xs text-olive-300">
            <div className="flex items-center space-x-3 p-4 rounded-2xl bg-olive-900/60 border border-olive-700/50">
              <div className="w-8 h-8 rounded-xl bg-cream-200/10 text-cream-200 flex items-center justify-center font-bold">
                <Scale className="w-4 h-4 text-cream-200" />
              </div>
              <div>
                <strong className="text-cream-200 block text-xs uppercase tracking-wider">Equal Rights</strong>
                <span>No teacher or admin privileges</span>
              </div>
            </div>

            <div className="flex items-center space-x-3 p-4 rounded-2xl bg-olive-900/60 border border-olive-700/50">
              <div className="w-8 h-8 rounded-xl bg-cream-200/10 text-cream-200 flex items-center justify-center font-bold">
                <EyeOff className="w-4 h-4 text-cream-200" />
              </div>
              <div>
                <strong className="text-cream-200 block text-xs uppercase tracking-wider">Zero Code Leakage</strong>
                <span>Classmates cannot view your raw source</span>
              </div>
            </div>

            <div className="flex items-center space-x-3 p-4 rounded-2xl bg-olive-900/60 border border-olive-700/50">
              <div className="w-8 h-8 rounded-xl bg-cream-200/10 text-cream-200 flex items-center justify-center font-bold">
                <Users className="w-4 h-4 text-cream-200" />
              </div>
              <div>
                <strong className="text-cream-200 block text-xs uppercase tracking-wider">Configurable Threshold</strong>
                <span>Trigger analysis at 2, 3, 5, or any count</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section className="py-20 bg-olive-900/50 border-y border-olive-700 relative z-10">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="mb-14">
            <span className="text-xs font-display uppercase tracking-widest text-cream-300 font-bold">Workflow</span>
            <h2 className="text-3xl sm:text-4xl font-display font-extrabold uppercase text-cream-200 mt-1">
              Automated Code Similarity
            </h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            <div className="p-6 rounded-3xl bg-olive-850 border border-olive-700/80">
              <span className="text-3xl font-display font-black text-cream-300 block mb-4">01</span>
              <h3 className="text-base font-bold text-cream-200 mb-2 font-display uppercase">Create Session</h3>
              <p className="text-xs text-olive-400 leading-relaxed">
                Create a classroom, choose your submission threshold (e.g. 2, 3, or 5), and get an invitation link.
              </p>
            </div>

            <div className="p-6 rounded-3xl bg-olive-850 border border-olive-700/80">
              <span className="text-3xl font-display font-black text-cream-300 block mb-4">02</span>
              <h3 className="text-base font-bold text-cream-200 mb-2 font-display uppercase">Share Link</h3>
              <p className="text-xs text-olive-400 leading-relaxed">
                Send the link to classmates. Everyone joins as equals with anonymous labels (<code className="text-cream-200 font-mono">Peer A</code>, <code className="text-cream-200 font-mono">Peer B</code>).
              </p>
            </div>

            <div className="p-6 rounded-3xl bg-olive-850 border border-olive-700/80">
              <span className="text-3xl font-display font-black text-cream-300 block mb-4">03</span>
              <h3 className="text-base font-bold text-cream-200 mb-2 font-display uppercase">Submit Code</h3>
              <p className="text-xs text-olive-400 leading-relaxed">
                Upload your C++ assignment. Code is safely tokenized and fingerprinted without execution.
              </p>
            </div>

            <div className="p-6 rounded-3xl bg-olive-850 border border-olive-700/80">
              <span className="text-3xl font-display font-black text-cream-300 block mb-4">04</span>
              <h3 className="text-base font-bold text-cream-200 mb-2 font-display uppercase">Private Report</h3>
              <p className="text-xs text-olive-400 leading-relaxed">
                Once the threshold is reached, private reports generate. See matching regions highlighted exclusively on your code.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="mt-auto py-8 border-t border-olive-700 bg-olive-950 text-center text-xs text-olive-400">
        <p>© 2026 Pledge Fighter — Peer-to-Peer Code Similarity Platform. Designed for privacy.</p>
      </footer>
    </div>
  );
};
