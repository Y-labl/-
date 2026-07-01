import { useRef, useState } from 'react';
import { api, type SmartAction } from '../api';

type Props = {
  bizDate: string;
  title?: string;
};

export function SmartLedgerPanel({ bizDate, title = '语音 / 截图智能录入' }: Props) {
  const [text, setText] = useState('');
  const [listening, setListening] = useState(false);
  const [ocrBusy, setOcrBusy] = useState(false);
  const [actions, setActions] = useState<SmartAction[]>([]);
  const [msg, setMsg] = useState('');
  const [err, setErr] = useState('');
  const fileRef = useRef<HTMLInputElement>(null);

  const speechSupported =
    typeof window !== 'undefined' && !!(window.SpeechRecognition || window.webkitSpeechRecognition);

  function startListen() {
    setErr('');
    setMsg('');
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SR) {
      setErr('当前浏览器不支持语音识别（请用 Chrome / Edge）');
      return;
    }
    const rec = new SR();
    rec.lang = 'zh-CN';
    rec.interimResults = false;
    rec.maxAlternatives = 1;
    rec.onresult = (ev: Event & { results: SpeechRecognitionResultList }) => {
      const t = ev.results[0]?.[0]?.transcript || '';
      setText((prev) => (prev ? `${prev} ${t}` : t));
      setListening(false);
    };
    rec.onerror = () => {
      setListening(false);
      setErr('语音识别出错，请重试');
    };
    rec.onend = () => setListening(false);
    setListening(true);
    rec.start();
  }

  async function runParse(source: string) {
    setErr('');
    setMsg('');
    if (!source.trim()) return setErr('没有可解析的文字');
    try {
      const r = await api.smartParse(source);
      setActions(r.actions);
      setMsg(r.actions.length ? `识别到 ${r.actions.length} 条意图，请确认后写入` : '未识别到现金/点卡/物品，请说得更具体些');
    } catch (e) {
      setErr(e instanceof Error ? e.message : '解析失败');
    }
  }

  async function onPickImage(f: File | null) {
    if (!f) return;
    setErr('');
    setMsg('');
    setOcrBusy(true);
    try {
      const r = await api.smartOcr(f);
      setText(r.ocrText || '');
      setActions(r.actions);
      setMsg(
        r.actions.length
          ? `OCR 完成，识别到 ${r.actions.length} 条意图（首次加载语言包可能较慢）`
          : 'OCR 完成，但未匹配到规则，可手动改字后再解析'
      );
    } catch (e) {
      setErr(e instanceof Error ? e.message : 'OCR 失败');
    } finally {
      setOcrBusy(false);
      if (fileRef.current) fileRef.current.value = '';
    }
  }

  async function apply() {
    setErr('');
    setMsg('');
    if (!actions.length) return setErr('没有待写入的记录');
    try {
      const r = await api.smartApply({ bizDate, actions });
      setMsg(`已写入 ${r.results.length} 条`);
      setActions([]);
      setText('');
    } catch (e) {
      setErr(e instanceof Error ? e.message : '写入失败');
    }
  }

  return (
    <div className="card" style={{ padding: '1rem', marginBottom: '1rem' }}>
      <h3 style={{ margin: '0 0 0.5rem' }}>{title}</h3>
      <p className="muted" style={{ fontSize: '0.85rem', marginBottom: '0.65rem' }}>
        语音在浏览器本地识别；截图上传到服务器 OCR（中英混合）。支持例如：「现金五十万」「点卡 50」「高级兽决」等，多条可分行或多次识别。
      </p>
      <div className="row" style={{ marginBottom: 8 }}>
        <button type="button" className="btn btn-ghost" disabled={!speechSupported || listening} onClick={startListen}>
          {listening ? '聆听中…' : '🎤 语音输入'}
        </button>
        <button type="button" className="btn btn-ghost" disabled={ocrBusy} onClick={() => fileRef.current?.click()}>
          {ocrBusy ? '识别中…' : '📷 上传截图 OCR'}
        </button>
        <input
          ref={fileRef}
          type="file"
          accept="image/*"
          style={{ display: 'none' }}
          onChange={(e) => onPickImage(e.target.files?.[0] ?? null)}
        />
        <button type="button" className="btn btn-ghost" onClick={() => runParse(text)}>
          解析文字
        </button>
      </div>
      <textarea
        className="input"
        rows={3}
        placeholder="语音识别结果、或 OCR 文本，可手动修改后再点「解析文字」"
        value={text}
        onChange={(e) => setText(e.target.value)}
        style={{ resize: 'vertical', minHeight: 72 }}
      />
      {actions.length > 0 && (
        <ul style={{ margin: '0.65rem 0', paddingLeft: '1.1rem', color: 'var(--muted)', fontSize: '0.9rem' }}>
          {actions.map((a, i) => (
            <li key={i} style={{ marginBottom: 4 }}>
              {a.type === 'cash' && <>现金 {a.amount}</>}
              {a.type === 'points' && <>点卡 {a.points}</>}
              {a.type === 'item' && <>物品 id={a.itemId} ×{a.quantity ?? 1}</>}
            </li>
          ))}
        </ul>
      )}
      <button type="button" className="btn btn-primary" style={{ marginTop: 8 }} disabled={!actions.length} onClick={apply}>
        确认写入账本
      </button>
      {msg && <p style={{ color: 'var(--accent)', marginTop: 8, fontSize: '0.9rem' }}>{msg}</p>}
      {err && <p style={{ color: 'var(--danger)', marginTop: 8, fontSize: '0.9rem' }}>{err}</p>}
    </div>
  );
}
