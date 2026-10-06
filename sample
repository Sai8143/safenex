import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import CountUp from "react-countup";
import {
  FaUsers,
  FaHeartbeat,
  FaBroadcastTower,
  FaGlobe,
  FaShieldAlt,
  FaChartLine,
} from "react-icons/fa";

import Container from "../Common/Container";
import GlassCard from "../Common/GlassCard";

const API_URL = import.meta.env.VITE_API_URL || "https://backend-ruby-nine-62.vercel.app";

function VisitorCounter({ onOpenAnalytics }) {
  const [count, setCount] = useState(42);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const registerVisitor = async () => {
      try {
        let deviceId = localStorage.getItem("portfolio_device_id");
        if (!deviceId) {
          deviceId = crypto.randomUUID();
          localStorage.setItem("portfolio_device_id", deviceId);
        }

        await fetch(`${API_URL}/api/visitor/register`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            device_id: deviceId,
            browser: navigator.userAgent,
            operating_system: navigator.platform,
          }),
        }).catch(() => {});

        const response = await fetch(`${API_URL}/api/visitor`);
        if (response.ok) {
          const data = await response.json();
          setCount(data.count || 42);
        }
      } catch (error) {
        console.error("Visitor tracking offline:", error);
      } finally {
        setLoading(false);
      }
    };

    registerVisitor();
  }, []);

  return (
    <section id="reach" className="py-20 relative">
      <Container>
        {/* HEADER */}
        <div className="text-center mb-14">
          <p className="terminal-label mb-4">PORTFOLIO REACH</p>
          <h2 className="text-4xl md:text-5xl font-black mb-5 text-white">
            Live Global Engagement
          </h2>
          <p className="text-slate-400 max-w-2xl mx-auto leading-8 text-sm md:text-base">
            Real-time visitor telemetry, device analytics, and portfolio interaction metrics powered by a live FastAPI database engine.
          </p>
        </div>

        <motion.div
          initial={{ opacity: 0, y: 40 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.8 }}
        >
          <GlassCard className="relative overflow-hidden p-8 lg:p-12 border border-white/10">
            {/* AMBIENT GLOW */}
            <motion.div
              animate={{ scale: [1, 1.08, 1] }}
              transition={{ duration: 6, repeat: Infinity }}
              className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[500px] rounded-full bg-white/[0.03] blur-[150px] pointer-events-none"
            />

            <div className="grid lg:grid-cols-[1fr_1.2fr] gap-12 items-center relative z-10">
              {/* LEFT: ORBITAL VISITOR COUNTER */}
              <div className="flex justify-center">
                <div className="relative w-[280px] h-[280px] flex items-center justify-center">
                  {/* OUTER ROTATING RING */}
                  <motion.div
                    animate={{ rotate: 360 }}
                    transition={{ duration: 30, repeat: Infinity, ease: "linear" }}
                    className="absolute inset-0 rounded-full border border-dashed border-white/20"
                  />

                  {/* INNER COUNTER RING */}
                  <motion.div
                    animate={{ rotate: -360 }}
                    transition={{ duration: 22, repeat: Infinity, ease: "linear" }}
                    className="absolute w-[220px] h-[220px] rounded-full border border-white/10"
                  />

                  {/* GLOW CORE */}
                  <motion.div
                    animate={{ scale: [1, 1.08, 1] }}
                    transition={{ duration: 4, repeat: Infinity }}
                    className="absolute w-[160px] h-[160px] rounded-full bg-white/[0.06] blur-[40px]"
                  />

                  {/* COUNT NUMBER */}
                  <div className="relative text-center z-10">
                    <div className="text-5xl md:text-6xl font-black text-white">
                      {loading ? (
                        "--"
                      ) : (
                        <CountUp end={count} duration={2.5} />
                      )}
                    </div>
                    <p className="mt-3 text-xs font-mono text-zinc-400 uppercase tracking-widest">
                      Unique Visitors
                    </p>
                  </div>
                </div>
              </div>

              {/* RIGHT: INSIGHTS & ANALYTICS ACTION */}
              <div className="text-center lg:text-left">
                <p className="terminal-label mb-4">LIVE SYSTEM TELEMETRY</p>
                <h3 className="text-3xl md:text-4xl font-black leading-tight mb-5 text-white">
                  Real-time activity &<br />global visitor reach
                </h3>
                <p className="text-slate-400 leading-8 mb-8 text-sm md:text-base">
                  Track website traffic, unique visitor devices, operating systems, and network sessions synced directly with the backend database node.
                </p>

                <div className="flex flex-wrap items-center gap-4 justify-center lg:justify-start">
                  <button
                    onClick={() => onOpenAnalytics && onOpenAnalytics(count)}
                    className="px-6 py-3.5 rounded-2xl border border-white/20 bg-white/10 text-white hover:bg-white/20 font-mono text-xs font-semibold transition-all duration-300 shadow-[0_0_20px_rgba(255,255,255,0.1)] flex items-center gap-2"
                  >
                    <FaChartLine className="w-4 h-4 text-white" />
                    <span>View Analytics & Visitor Logs</span>
                  </button>

                  <div className="flex items-center gap-2 px-4 py-3 rounded-2xl border border-white/10 bg-white/[0.03] text-xs font-mono text-zinc-400">
                    <div className="w-2 h-2 rounded-full bg-white animate-pulse" />
                    <span>Database Synced</span>
                  </div>
                </div>
              </div>
            </div>

            {/* BOTTOM STATUS BAR */}
            <div className="mt-12 pt-8 border-t border-white/10 grid grid-cols-1 md:grid-cols-3 gap-6 relative z-10">
              <div className="flex items-center gap-3">
                <div className="w-2.5 h-2.5 rounded-full bg-white animate-pulse" />
                <div>
                  <p className="terminal-label">SYSTEM STATUS</p>
                  <p className="text-xs font-mono text-slate-300 mt-0.5">Tracking Active (100% Online)</p>
                </div>
              </div>

              <div className="flex items-center gap-3">
                <FaUsers className="w-4 h-4 text-zinc-400" />
                <div>
                  <p className="terminal-label">VISITOR MODE</p>
                  <p className="text-xs font-mono text-slate-300 mt-0.5">Unique Visitor Tracking</p>
                </div>
              </div>

              <div className="flex items-center gap-3">
                <FaBroadcastTower className="w-4 h-4 text-zinc-400" />
                <div>
                  <p className="terminal-label">DATABASE NODE</p>
                  <p className="text-xs font-mono text-slate-300 mt-0.5">FastAPI Real-Time Telemetry</p>
                </div>
              </div>
            </div>
          </GlassCard>
        </motion.div>
      </Container>
    </section>
  );
}

export default VisitorCounter;