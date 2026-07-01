import { useEffect, useRef, useState } from 'react';
import './LoginDarkEyesMascot.css';

type Mouse = { x: number; y: number };

type TrackedBlackEyeProps = {
  mouse: Mouse;
  lookAway: boolean;
  side: 'left' | 'right';
  cx: number;
  cy: number;
  idle: { x: number; y: number };
};

function TrackedBlackEye({ mouse, lookAway, side, cx, cy, idle }: TrackedBlackEyeProps) {
  const socketRef = useRef<SVGEllipseElement>(null);
  const [off, setOff] = useState({ x: 0, y: 0 });

  useEffect(() => {
    const el = socketRef.current;
    if (!el) return;
    const r = el.getBoundingClientRect();
    const scx = r.left + r.width / 2;
    const scy = r.top + r.height / 2;
    if (lookAway) {
      const dir = side === 'left' ? 1 : -1;
      setOff({ x: dir * 5.5, y: 3.2 });
      return;
    }
    const dx = mouse.x - scx;
    const dy = mouse.y - scy;
    const dist = Math.hypot(dx, dy) || 1;
    const pull = Math.min(dist / 95, 1);
    const maxR = 6.2;
    setOff({
      x: (dx / dist) * maxR * pull + idle.x,
      y: (dy / dist) * maxR * pull + idle.y,
    });
  }, [mouse.x, mouse.y, lookAway, side, idle.x, idle.y]);

  return (
    <g className="login-dark-eye">
      <ellipse
        ref={socketRef}
        cx={cx}
        cy={cy}
        rx={22}
        ry={17}
        className="login-dark-eye-socket"
      />
      <g transform={`translate(${cx + off.x} ${cy + off.y})`}>
        <g className="login-dark-eye-ball">
          <circle r={12.5} className="login-dark-eye-sphere" />
          <circle r={2.1} cx={-3.4} cy={-3.2} className="login-dark-eye-glint" />
          <circle r={1.05} cx={2.2} cy={2} className="login-dark-eye-glint login-dark-eye-glint-sm" />
        </g>
      </g>
    </g>
  );
}

export function LoginDarkEyesMascot({ lookAway }: { lookAway: boolean }) {
  const [mouse, setMouse] = useState<Mouse>({ x: 0, y: 0 });
  const [idle, setIdle] = useState({ x: 0, y: 0 });

  useEffect(() => {
    const onMove = (e: MouseEvent) => setMouse({ x: e.clientX, y: e.clientY });
    window.addEventListener('mousemove', onMove);
    return () => window.removeEventListener('mousemove', onMove);
  }, []);

  useEffect(() => {
    let id = 0;
    let t0 = performance.now();
    const tick = (now: number) => {
      const t = (now - t0) / 1000;
      if (!lookAway) {
        setIdle({
          x: Math.sin(t * 1.15) * 0.85 + Math.sin(t * 0.37 + 1) * 0.35,
          y: Math.cos(t * 0.92) * 0.7 + Math.cos(t * 0.44) * 0.28,
        });
      } else {
        setIdle({ x: 0, y: 0 });
      }
      id = requestAnimationFrame(tick);
    };
    id = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(id);
  }, [lookAway]);

  return (
    <div className="login-dark-eyes-wrap" aria-hidden>
      <svg
        className="login-dark-eyes-svg"
        viewBox="0 0 280 140"
        role="img"
        aria-label="黑色眼珠跟随指针微动"
      >
        <defs>
          <radialGradient id="loginEyeBallGrad" cx="35%" cy="30%" r="65%">
            <stop offset="0%" stopColor="#2a3038" />
            <stop offset="55%" stopColor="#0a0c10" />
            <stop offset="100%" stopColor="#020203" />
          </radialGradient>
          <filter id="loginEyeSoft" x="-20%" y="-20%" width="140%" height="140%">
            <feGaussianBlur in="SourceGraphic" stdDeviation="0.8" result="b" />
            <feMerge>
              <feMergeNode in="b" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>
        <TrackedBlackEye mouse={mouse} lookAway={lookAway} side="left" cx={88} cy={82} idle={idle} />
        <TrackedBlackEye mouse={mouse} lookAway={lookAway} side="right" cx={192} cy={82} idle={idle} />
        <path
          className="login-dark-eyes-smile"
          d="M 108 118 Q 140 132 172 118"
          fill="none"
          strokeLinecap="round"
        />
      </svg>
    </div>
  );
}
