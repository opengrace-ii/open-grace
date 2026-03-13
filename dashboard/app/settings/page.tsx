"use client";

import { Settings as SettingsIcon, Shield, Bell, User, Cpu, Database, Globe } from 'lucide-react';

export default function Settings() {
  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div>
        <h1 className="text-3xl font-bold text-white tracking-tight">Settings</h1>
        <p className="text-slate-400 mt-2">Configure your AI OS environment and security preferences.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
        <div className="md:col-span-1 space-y-2">
           <button className="w-full flex items-center gap-3 px-4 py-3 bg-blue-600/10 text-blue-400 rounded-xl font-bold text-sm tracking-wide transition-all border border-blue-500/20">
             <SettingsIcon className="w-4 h-4" />
             General
           </button>
           <button className="w-full flex items-center gap-3 px-4 py-3 hover:bg-slate-900 text-slate-400 rounded-xl font-bold text-sm tracking-wide transition-all group">
             <Shield className="w-4 h-4 group-hover:text-blue-400" />
             Security & Sandbox
           </button>
           <button className="w-full flex items-center gap-3 px-4 py-3 hover:bg-slate-900 text-slate-400 rounded-xl font-bold text-sm tracking-wide transition-all group">
             <Cpu className="w-4 h-4 group-hover:text-amber-400" />
             Model Router
           </button>
           <button className="w-full flex items-center gap-3 px-4 py-3 hover:bg-slate-900 text-slate-400 rounded-xl font-bold text-sm tracking-wide transition-all group">
             <Database className="w-4 h-4 group-hover:text-emerald-400" />
             Memory Persistence
           </button>
        </div>

        <div className="md:col-span-2 space-y-6">
           <div className="bg-slate-900/50 border border-slate-800 rounded-2xl p-8 backdrop-blur-sm">
              <h2 className="text-xl font-bold text-white mb-6">General Configuration</h2>
              <div className="space-y-6">
                 <div className="space-y-2">
                   <label className="text-xs font-bold text-slate-500 uppercase tracking-widest">Environment Name</label>
                   <input 
                     type="text" 
                     defaultValue="Open Grace Production" 
                     className="w-full bg-slate-950 border border-slate-800 rounded-lg px-4 py-2 text-white focus:ring-1 focus:ring-blue-500"
                   />
                 </div>
                 <div className="space-y-2">
                   <label className="text-xs font-bold text-slate-500 uppercase tracking-widest">API Endpoint</label>
                   <input 
                     type="text" 
                     defaultValue="http://127.0.0.1:8000" 
                     className="w-full bg-slate-950 border border-slate-800 rounded-lg px-4 py-2 text-white focus:ring-1 focus:ring-blue-500"
                   />
                 </div>
                 <div className="flex items-center justify-between p-4 bg-slate-950/50 border border-slate-800 rounded-xl">
                    <div>
                      <h4 className="text-sm font-bold text-white">Debug Mode</h4>
                      <p className="text-xs text-slate-500 mt-0.5">Show detailed agent reasoning in logs</p>
                    </div>
                    <div className="w-12 h-6 bg-blue-600 rounded-full relative cursor-pointer">
                       <div className="absolute right-1 top-1 w-4 h-4 bg-white rounded-full"></div>
                    </div>
                 </div>
              </div>

              <div className="mt-8 flex justify-end gap-4">
                 <button className="px-6 py-2 rounded-lg bg-slate-800 text-white font-bold text-xs uppercase hover:bg-slate-700 transition-all">Cancel</button>
                 <button className="px-6 py-2 rounded-lg bg-blue-600 text-white font-bold text-xs uppercase hover:bg-blue-500 transition-all shadow-lg shadow-blue-500/20">Save Changes</button>
              </div>
           </div>
        </div>
      </div>
    </div>
  );
}
