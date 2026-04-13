import { useEffect, useRef, useState } from 'react';
import './RobotLoginMascot.css';

type Mouse = { x: number; y: number };

type TrackedEyeProps = {
  mouse: Mouse;
  lookAway: boolean;
  side: 'left' | 'right';
  cx: number;
  cy: number;
};

function TrackedEye({ mouse, lookAway, side, cx, cy }: TrackedEyeProps) {
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
      setOff({ x: dir * 4.8, y: 2.6 });
      return;
    }
    const dx = mouse.x - scx;
    const dy = mouse.y - scy;
    const dist = Math.hypot(dx, dy) || 1;
    const pull = Math.min(dist / 90, 1);
    const maxR = 5;
    setOff({
      x: (dx / dist) * maxR * pull,
      y: (dy / dist) * maxR * pull,
    });
  }, [mouse.x, mouse.y, lookAway, side]);

  return (
    <g>
      <ellipse
        ref={socketRef}
        cx={cx}
        cy={cy}
        rx={17}
        ry={13.5}
        fill="url(#robotEyeSocket)"
        stroke="rgba(0,229,255,0.5)"
        strokeWidth={1}
        className="robo-eye-ring"
      />
      <g transform={`translate(${cx + off.x} ${cy + off.y})`}>
        <circle r={6.5} fill="#00e5ff" filter="url(#robotEyeGlow)" />
        <circle r={2.2} cx={-2.2} cy={-2} fill="#fff" opacity={0.9} />
        <circle r={1} cx={1.5} cy={1.2} fill="#0a1620" opacity={0.65} />
      </g>
    </g>
  );
}

export function RobotLoginMascot({ lookAway }: { lookAway: boolean }) {
  const [mouse, setMouse] = useState<Mouse>({ x: 0, y: 0 });

  useEffect(() => {
    const onMove = (e: MouseEvent) => setMouse({ x: e.clientX, y: e.clientY });
    window.addEventListener('mousemove', onMove);
    return () => window.removeEventListener('mousemove', onMove);
  }, []);

  return (
    <div className="robot-mascot-wrap" aria-hidden>
      <svg
        className="robot-mascot-svg"
        viewBox="0 0 200 118"
        role="img"
        aria-label="酷炫机器人头像，双眼跟随指针移动"
      >
        <defs>
          <linearGradient id="robotMetal" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#1a2838" />
            <stop offset="45%" stopColor="#0d1520" />
            <stop offset="100%" stopColor="#060a10" />
          </linearGradient>
          <linearGradient id="robotCheek" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stopColor="rgba(0,229,255,0.12)" />
            <stop offset="100%" stopColor="rgba(0,0,0,0.4)" />
          </linearGradient>
          <radialGradient id="robotEyeSocket" cx="40%" cy="35%" r="65%">
            <stop offset="0%" stopColor="#0a1218" />
            <stop offset="100%" stopColor="#020508" />
          </radialGradient>
          <filter id="robotEyeGlow" x="-50%" y="-50%" width="200%" height="200%">
            <feGaussianBlur stdDeviation="1.2" result="b" />
            <feMerge>
              <feMergeNode in="b" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
          <linearGradient id="robotJaw" x1="50%" y1="0%" x2="50%" y2="100%">
            <stop offset="0%" stopColor="rgba(0,229,255,0.25)" />
            <stop offset="100%" stopColor="rgba(0,229,255,0.02)" />
          </linearGradient>
          <clipPath id="robotHudClip">
            <rect x={52} y={30} width={96} height={4} rx={1} />
          </clipPath>
        </defs>

        {/* 天线 */}
        <line x1={100} y1={18} x2={100} y2={8} stroke="rgba(0,229,255,0.55)" strokeWidth={2} strokeLinecap="round" />
        <circle className="robo-antenna-ball" cx={100} cy={6} r={4} fill="#00e5ff" />

        {/* 头部主体 */}
        <path
          className="robo-head-stroke"
          d="M 38 22 L 162 22 L 176 36 L 176 82 L 162 96 L 38 96 L 24 82 L 24 36 Z"
          fill="url(#robotMetal)"
          stroke="#00e5ff"
          strokeWidth={1.2}
          strokeLinejoin="round"
        />

        {/* 侧装甲 */}
        <path d="M 24 42 L 14 48 L 14 70 L 24 76 Z" fill="url(#robotCheek)" stroke="rgba(0,229,255,0.25)" strokeWidth={0.8} />
        <path d="M 176 42 L 186 48 L 186 70 L 176 76 Z" fill="url(#robotCheek)" stroke="rgba(0,229,255,0.25)" strokeWidth={0.8} />

        {/* 额头装饰条 */}
        <rect x={52} y={30} width={96} height={4} rx={1} fill="rgba(0,229,255,0.08)" stroke="rgba(0,229,255,0.2)" strokeWidth={0.5} />
        <g clipPath="url(#robotHudClip)">
          <rect className="robo-scan" x={48} y={30.5} width={28} height={3} rx={0.5} fill="rgba(122,240,255,0.55)" />
        </g>

        {/* 双眼 */}
        <TrackedEye mouse={mouse} lookAway={lookAway} side="left" cx={68} cy={56} />
        <TrackedEye mouse={mouse} lookAway={lookAway} side="right" cx={132} cy={56} />

        {/* 下颌线 / 嘴部灯条 */}
        <path
          d="M 56 88 L 144 88"
          stroke="url(#robotJaw)"
          strokeWidth={3}
          strokeLinecap="round"
          opacity={0.85}
        />
        <rect x={88} y={84} width={24} height={5} rx={1} fill="rgba(255,159,28,0.35)" stroke="rgba(255,159,28,0.5)" strokeWidth={0.5} />

        {/* 肩甲暗示 */}
        <path d="M 32 96 L 20 108 L 32 112 Z" fill="#0a1018" stroke="rgba(0,229,255,0.2)" strokeWidth={0.6} />
        <path d="M 168 96 L 180 108 L 168 112 Z" fill="#0a1018" stroke="rgba(0,229,255,0.2)" strokeWidth={0.6} />
      </svg>
    </div>
  );
}
