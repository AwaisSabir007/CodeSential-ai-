'use client';

import React from 'react';
import {
  ArrowRight,
  ChevronRight,
  Shield,
  Search,
  Activity,
  Zap,
  Lock,
  BrainCircuit,
  ShieldAlert,
} from 'lucide-react';
import { cn } from '../../lib/utils';

interface LandingHeroProps {
  onGetStarted: () => void;
}

export const LandingHero: React.FC<LandingHeroProps> = ({ onGetStarted }) => {
  return (
    <section className="relative flex min-h-screen w-full flex-col items-center bg-[#040814] font-sans text-white selection:bg-white selection:text-black overflow-hidden">

      {/* Background glow blobs */}
      <div className="pointer-events-none absolute inset-0 overflow-hidden">
        <div className="absolute -top-40 left-1/2 -translate-x-1/2 w-[900px] h-[500px] rounded-full bg-indigo-900/20 blur-[120px]" />
        <div className="absolute top-[60%] left-[10%] w-[400px] h-[400px] rounded-full bg-violet-900/10 blur-[100px]" />
        <div className="absolute top-[40%] right-[5%] w-[300px] h-[300px] rounded-full bg-indigo-800/10 blur-[80px]" />
      </div>

      {/* Subtle grid overlay */}
      <div
        className="pointer-events-none absolute inset-0 opacity-[0.03]"
        style={{
          backgroundImage:
            'linear-gradient(rgba(255,255,255,0.5) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.5) 1px, transparent 1px)',
          backgroundSize: '64px 64px',
        }}
      />

      {/* Nav bar */}
      <div className="relative z-10 w-full border-b border-white/[0.06] h-16 flex items-center justify-between px-8 md:px-16 bg-black/20 backdrop-blur-md">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-indigo-600 to-violet-500 flex items-center justify-center shadow-glow">
            <ShieldAlert className="w-4 h-4 text-white" />
          </div>
          <span className="font-semibold text-sm tracking-wide text-white">CodeSentinel AI</span>
          <span className="hidden md:block text-[10px] text-indigo-400 tracking-widest font-mono uppercase ml-1">
            Local-First SecOps
          </span>
        </div>
        <div className="flex items-center gap-4">
          <span className="hidden md:block text-xs text-gray-500">v1.0.0</span>
          <button
            onClick={onGetStarted}
            className="rounded-full bg-white/[0.08] hover:bg-white/[0.13] border border-white/[0.12] text-white text-xs font-medium px-4 py-1.5 transition-all duration-200"
          >
            Sign In
          </button>
        </div>
      </div>

      {/* Main content */}
      <main className="relative z-10 flex w-full max-w-[1000px] flex-col items-center px-6 pt-24 pb-32 text-center md:pt-32">

        {/* Announcement pill */}
        <div className="group mb-10 flex cursor-pointer items-center gap-2 rounded-full border border-white/[0.12] bg-white/[0.03] py-1.5 pl-1.5 pr-3 text-xs font-medium text-neutral-400 backdrop-blur-md transition-colors hover:bg-white/[0.06]">
          <span className="rounded-full bg-indigo-600 px-2.5 py-0.5 text-[10px] font-bold uppercase tracking-widest text-white">
            New
          </span>
          <span>Real-time CodeBERT neural vulnerability scoring</span>
          <ChevronRight className="h-3.5 w-3.5 text-neutral-500 transition-transform group-hover:translate-x-0.5" />
        </div>

        {/* Headline */}
        <h1 className="mb-6 max-w-4xl text-5xl font-semibold tracking-tighter text-white sm:text-7xl lg:text-8xl leading-[1.05]">
          Secure your code.{' '}
          <br className="hidden sm:block" />
          <span className="text-neutral-600">Automatically.</span>
        </h1>

        <p className="mx-auto mb-10 max-w-[580px] text-base leading-relaxed text-neutral-400 sm:text-lg">
          Local-first AI security platform that continuously watches your codebase, detects vulnerabilities
          in real time, and autonomously proposes verified fixes — without sending your code to the cloud.
        </p>

        {/* CTAs */}
        <div className="flex w-full flex-col items-center justify-center gap-3 sm:flex-row">
          <button
            onClick={onGetStarted}
            className="flex h-11 w-full items-center justify-center gap-2 rounded-md bg-white px-7 text-sm font-semibold text-black transition-all hover:bg-neutral-200 active:scale-[0.98] sm:w-auto"
          >
            Start Now
            <ArrowRight className="h-4 w-4" />
          </button>
          <button className="flex h-11 w-full items-center justify-center rounded-md border border-white/[0.12] bg-transparent px-7 text-sm font-medium text-white transition-all hover:bg-white/[0.05] active:scale-[0.98] sm:w-auto">
            View Documentation
          </button>
        </div>

        {/* Trust bar */}
        <div className="mt-10 flex items-center gap-6 text-xs text-neutral-600">
          <span className="flex items-center gap-1.5"><Lock className="w-3.5 h-3.5" /> 100% Local</span>
          <span className="w-px h-4 bg-white/10" />
          <span className="flex items-center gap-1.5"><Shield className="w-3.5 h-3.5" /> Zero Cloud Leaks</span>
          <span className="w-px h-4 bg-white/10" />
          <span className="flex items-center gap-1.5"><BrainCircuit className="w-3.5 h-3.5" /> CodeBERT Neural Engine</span>
        </div>

        {/* Mock UI window */}
        <div className="mt-20 w-full max-w-4xl rounded-t-2xl border border-white/[0.10] bg-[#080d1a] shadow-2xl overflow-hidden">

          {/* Window chrome */}
          <div className="flex items-center gap-4 border-b border-white/[0.07] bg-white/[0.02] px-4 py-3">
            <div className="flex gap-1.5">
              <div className="h-2.5 w-2.5 rounded-full bg-white/[0.12]" />
              <div className="h-2.5 w-2.5 rounded-full bg-white/[0.12]" />
              <div className="h-2.5 w-2.5 rounded-full bg-white/[0.12]" />
            </div>
            <div className="mx-auto flex h-7 w-full max-w-md items-center gap-2 rounded-md border border-white/[0.08] bg-black/50 px-2.5 text-xs text-neutral-500">
              <Search className="h-3.5 w-3.5" />
              <span>Scanning project — 3 vulnerabilities found...</span>
              <div className="ml-auto flex items-center gap-1 opacity-60">
                <Activity className="h-3 w-3 text-emerald-400" />
                <span className="text-emerald-400 text-[10px]">Live</span>
              </div>
            </div>
          </div>

          {/* Mock scan output */}
          <div className="h-64 w-full bg-[#060b18] p-6 text-left font-mono text-sm leading-relaxed">

            <div className="flex items-center gap-2 text-neutral-400">
              <span className="text-indigo-400">❯</span>
              <span>codesentinel scan ./src --level 2</span>
            </div>

            <div className="mt-4 space-y-1 text-neutral-600 text-xs">
              <p><span className="text-emerald-500">✔</span> Bandit — Python AST scanner ready</p>
              <p><span className="text-emerald-500">✔</span> Semgrep — 847 rules loaded</p>
              <p><span className="text-emerald-500">✔</span> Gitleaks — Secret pattern engine active</p>
              <p><span className="text-emerald-500">✔</span> CodeBERT neural head — loaded (CPU)</p>
            </div>

            <div className="mt-4 space-y-1 text-xs">
              <p className="text-red-400">    [CRITICAL] routes/auth.py:42 — SQL Injection via string concat (CWE-89)</p>
              <p className="text-amber-400">    [HIGH]     utils/crypto.py:17 — Hardcoded API secret key (CWE-798)</p>
              <p className="text-yellow-500">    [MEDIUM]   app/views.py:88 — Command injection risk (CWE-78)</p>
            </div>

            <div className="mt-4 flex items-center gap-2">
              <div className="h-2 w-2 rounded-full bg-indigo-500 animate-pulse" />
              <span className="text-indigo-400 text-xs">Multi-agent investigation initiated...</span>
            </div>
          </div>
        </div>

        {/* Feature grid */}
        <div className="mt-24 w-full grid grid-cols-1 sm:grid-cols-3 gap-4">
          {[
            {
              icon: <Activity className="w-5 h-5 text-emerald-400" />,
              title: 'Real-Time Watchdog',
              desc: 'Filesystem observer detects every save with 1.5s debounce and SHA-256 deduplication.',
              color: 'from-emerald-950/30',
            },
            {
              icon: <BrainCircuit className="w-5 h-5 text-indigo-400" />,
              title: 'Neural Risk Scoring',
              desc: 'Fine-tuned CodeBERT transformer returns a statistical vulnerability risk score on every change.',
              color: 'from-indigo-950/30',
            },
            {
              icon: <Zap className="w-5 h-5 text-violet-400" />,
              title: 'Autonomous Remediation',
              desc: 'Multi-agent pipeline proposes minimal, verified patches. You approve — nothing applies silently.',
              color: 'from-violet-950/30',
            },
          ].map((f, i) => (
            <div
              key={i}
              className={cn(
                'rounded-2xl border border-white/[0.08] bg-gradient-to-b p-6 text-left transition-all duration-200 hover:border-white/[0.14] hover:scale-[1.02]',
                f.color,
                'to-transparent'
              )}
            >
              <div className="mb-3 inline-flex rounded-xl bg-white/[0.05] p-2.5">{f.icon}</div>
              <h3 className="mb-2 text-sm font-semibold text-white">{f.title}</h3>
              <p className="text-xs text-neutral-500 leading-relaxed">{f.desc}</p>
            </div>
          ))}
        </div>

        {/* Bottom CTA */}
        <div className="mt-24 flex flex-col items-center gap-4">
          <p className="text-sm text-neutral-500">Ready to ship secure code?</p>
          <button
            onClick={onGetStarted}
            className="flex h-12 items-center justify-center gap-2 rounded-full bg-indigo-600 hover:bg-indigo-500 px-8 text-sm font-semibold text-white shadow-glow transition-all duration-200 active:scale-[0.98]"
          >
            Open Dashboard
            <ArrowRight className="h-4 w-4" />
          </button>
        </div>

      </main>

      {/* Bottom fade */}
      <div className="pointer-events-none absolute bottom-0 left-0 right-0 h-32 bg-gradient-to-t from-[#040814] to-transparent" />
    </section>
  );
};
