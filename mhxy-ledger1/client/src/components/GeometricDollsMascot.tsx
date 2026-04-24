import { useEffect, useRef, useState } from 'react';
import './GeometricDollsMascot.css';

type Mouse = { x: number; y: number };

function usePupilOffset(
  ref: React.RefObject<SVGCircleElement | SVGEllipseElement | null>,
  mouse: Mouse,
  lookAway: boolean,
  side: 'left' | 'right',
  max: number
) {
  const [off, setOff] = useState({ x: 0, y: 0 });

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const r = el.getBoundingClientRect();
    const scx = r.left + r.width / 2;
    const scy = r.top + r.height / 2;
    if (lookAway) {
      const dir = side === 'left' ? 1 : -1;
      setOff({ x: dir * (max * 0.85), y: max * 0.35 });
      return;
    }
    const dx = mouse.x - scx;
    const dy = mouse.y - scy;
    const dist = Math.hypot(dx, dy) || 1;
    const pull = Math.min(dist / 100, 1);
    setOff({
      x: (dx / dist) * max * pull,
      y: (dy / dist) * max * pull,
    });
  }, [mouse.x, mouse.y, lookAway, side, max]);

  return off;
}

/** 大白眼眶 + 黑瞳孔（蓝娃娃、黑娃娃） */
function BigEyePair({
  mouse,
  lookAway,
  leftCx,
  leftCy,
  rightCx,
  rightCy,
  pupilMax,
}: {
  mouse: Mouse;
  lookAway: boolean;
  leftCx: number;
  leftCy: number;
  rightCx: number;
  rightCy: number;
  pupilMax: number;
}) {
  const lRef = useRef<SVGCircleElement>(null);
  const rRef = useRef<SVGCircleElement>(null);
  const lo = usePupilOffset(lRef, mouse, lookAway, 'left', pupilMax);
  const ro = usePupilOffset(rRef, mouse, lookAway, 'right', pupilMax);

  return (
    <g>
      <circle ref={lRef} cx={leftCx} cy={leftCy} r={18} fill="#fff" />
      <circle ref={rRef} cx={rightCx} cy={rightCy} r={18} fill="#fff" />
      <circle cx={leftCx + lo.x} cy={leftCy + lo.y} r={7} fill="#0f172a" />
      <circle cx={rightCx + ro.x} cy={rightCy + ro.y} r={7} fill="#0f172a" />
    </g>
  );
}

/** 小圆点眼睛（橙、黄娃娃） */
function DotEyePair({
  mouse,
  lookAway,
  leftCx,
  leftCy,
  rightCx,
  rightCy,
}: {
  mouse: Mouse;
  lookAway: boolean;
  leftCx: number;
  leftCy: number;
  rightCx: number;
  rightCy: number;
}) {
  const max = 3.2;
  const lRef = useRef<SVGCircleElement>(null);
  const rRef = useRef<SVGCircleElement>(null);
  const lo = usePupilOffset(lRef, mouse, lookAway, 'left', max);
  const ro = usePupilOffset(rRef, mouse, lookAway, 'right', max);

  return (
    <g>
      <circle ref={lRef} cx={leftCx} cy={leftCy} r={2.8} fill="transparent" />
      <circle ref={rRef} cx={rightCx} cy={rightCy} r={2.8} fill="transparent" />
      <circle cx={leftCx + lo.x} cy={leftCy + lo.y} r={3.2} fill="#0f172a" />
      <circle cx={rightCx + ro.x} cy={rightCy + ro.y} r={3.2} fill="#0f172a" />
    </g>
  );
}

export function GeometricDollsMascot({ lookAway }: { lookAway: boolean }) {
  const [mouse, setMouse] = useState<Mouse>({ x: 0, y: 0 });

  useEffect(() => {
    const onMove = (e: MouseEvent) => setMouse({ x: e.clientX, y: e.clientY });
    window.addEventListener('mousemove', onMove);
    return () => window.removeEventListener('mousemove', onMove);
  }, []);

  return (
    <div className="geo-dolls-wrap" aria-hidden>
      <svg className="geo-dolls-svg" viewBox="0 0 340 380" role="img" aria-label="几何小人，眼睛跟随鼠标">
        {/* 蓝：高矩形 靠后左 */}
        <g className="geo-doll geo-doll-blue">
          <rect x={36} y={72} width={76} height={198} rx={4} fill="#3b7dd6" />
          <BigEyePair
            mouse={mouse}
            lookAway={lookAway}
            leftCx={58}
            leftCy={142}
            rightCx={90}
            rightCy={142}
            pupilMax={6.5}
          />
        </g>

        {/* 黑：高条 靠后右 */}
        <g className="geo-doll geo-doll-black">
          <rect x={196} y={48} width={44} height={232} rx={3} fill="#1a1a1e" />
          <BigEyePair
            mouse={mouse}
            lookAway={lookAway}
            leftCx={208}
            leftCy={128}
            rightCx={228}
            rightCy={128}
            pupilMax={5}
          />
        </g>

        {/* 橙：半圆顶 前左 */}
        <g className="geo-doll geo-doll-orange">
          <path d="M 52 298 A 52 52 0 0 1 156 298 L 156 318 L 52 318 Z" fill="#f97316" />
          <DotEyePair mouse={mouse} lookAway={lookAway} leftCx={88} leftCy={268} rightCx={120} rightCy={268} />
        </g>

        {/* 黄：圆角块 前右 + 嘴线 */}
        <g className="geo-doll geo-doll-yellow">
          <rect x={188} y={248} width={92} height={102} rx={36} fill="#eab308" />
          <DotEyePair mouse={mouse} lookAway={lookAway} leftCx={214} leftCy={288} rightCx={254} rightCy={288} />
          <line x1={210} y1={318} x2={258} y2={318} stroke="#0f172a" strokeWidth={2.2} strokeLinecap="round" />
        </g>
      </svg>
    </div>
  );
}
