import { useEffect, useMemo, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api, setToken } from '../api';
import './LoginPageMHXY.css';

export function LoginPage() {
  const nav = useNavigate();
  const [mode, setMode] = useState<'login' | 'register'>('login');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [remember, setRemember] = useState(false);
  const [err, setErr] = useState('');
  const [loading, setLoading] = useState(false);

  const petalsRef = useRef<HTMLDivElement | null>(null);
  const particlesRef = useRef<HTMLDivElement | null>(null);
  const videoRef = useRef<HTMLVideoElement | null>(null);

  const titleText = useMemo(() => (mode === 'login' ? '登录游戏' : '注册账号'), [mode]);

  useEffect(() => {
    try {
      const rememberedUsername = localStorage.getItem('rememberedUsername') || '';
      const rememberedPassword = localStorage.getItem('rememberedPassword') || '';
      if (rememberedUsername && rememberedPassword) {
        setUsername(rememberedUsername);
        try {
          setPassword(atob(rememberedPassword));
        } catch {
          setPassword('');
        }
        setRemember(true);
      }
    } catch {
      /* ignore */
    }
  }, []);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setErr('');
    setLoading(true);
    try {
      if (remember) {
        localStorage.setItem('rememberedUsername', username);
        localStorage.setItem('rememberedPassword', btoa(password));
      } else {
        localStorage.removeItem('rememberedUsername');
        localStorage.removeItem('rememberedPassword');
      }
    } catch {
      /* ignore */
    }
    try {
      const fn = mode === 'login' ? api.login : api.register;
      const r = await fn({ username: username.trim(), password });
      setToken(r.token);
      nav('/app', { replace: true });
    } catch (ex) {
      setErr(ex instanceof Error ? ex.message : '失败');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    const v = videoRef.current;
    if (!v) return;
    const onTime = () => {
      if (v.currentTime >= 27) v.currentTime = 0;
    };
    v.addEventListener('timeupdate', onTime);
    return () => v.removeEventListener('timeupdate', onTime);
  }, []);

  useEffect(() => {
    const petals = petalsRef.current;
    if (!petals) return;
    const id = window.setInterval(() => {
      const el = document.createElement('div');
      el.className = 'petal';
      el.style.left = `${Math.random() * 100}%`;
      el.style.animationDuration = `${8 + Math.random() * 4}s`;
      petals.appendChild(el);
      window.setTimeout(() => el.remove(), 12000);
    }, 800);
    return () => window.clearInterval(id);
  }, []);

  useEffect(() => {
    const particles = particlesRef.current;
    if (!particles) return;
    const createParticle = () => {
      const el = document.createElement('div');
      el.className = 'particle';
      el.style.left = `${Math.random() * 100}%`;
      el.style.top = `${Math.random() * 100}%`;
      el.style.animationDelay = `${Math.random() * 2}s`;
      particles.appendChild(el);
    };
    for (let i = 0; i < 5; i++) createParticle();
  }, []);

  return (
    <div className="mhxy-login-page">
      <div className="background" aria-hidden>
        <div className="video-wrapper">
          <video ref={videoRef} className="video-bg" autoPlay loop muted playsInline>
            <source
              src="https://fc-transvideo.baidu.com/5b26f5011c3ab1dad2fb332b602ee4e2_1280_720.mp4"
              type="video/mp4"
            />
          </video>
        </div>
        <div className="video-overlay" />
        <div className="petals" ref={petalsRef}>
          {Array.from({ length: 10 }, (_, i) => (
            <div key={i} className="petal" />
          ))}
        </div>
        <div className="magic-particles" ref={particlesRef}>
          {Array.from({ length: 8 }, (_, i) => (
            <div key={i} className="particle" />
          ))}
        </div>
      </div>

      <div className="login-container">
        <h1 className="login-title">梦幻西游</h1>
        <form onSubmit={submit}>
          <div className="form-group">
            <label htmlFor="username">账号</label>
            <input
              type="text"
              id="username"
              placeholder="请输入您的账号"
              autoComplete="username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
            />
          </div>
          <div className="form-group">
            <label htmlFor="password">密码</label>
            <input
              type="password"
              id="password"
              placeholder="请输入您的密码"
              autoComplete={mode === 'login' ? 'current-password' : 'new-password'}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </div>

          <div className="remember-row">
            <input
              type="checkbox"
              id="remember-password"
              checked={remember}
              onChange={(e) => setRemember(e.target.checked)}
            />
            <label htmlFor="remember-password">
              记住密码
            </label>
          </div>

          {err ? <div className="login-error">{err}</div> : null}

          <button type="submit" className="login-btn" disabled={loading}>
            {loading ? '请稍候…' : titleText}
          </button>
        </form>

        <div className="links">
          <a
            href="#register"
            onClick={(e) => {
              e.preventDefault();
              setMode('register');
            }}
          >
            注册账号
          </a>
          <span>|</span>
          <a
            href="#login"
            onClick={(e) => {
              e.preventDefault();
              setMode('login');
            }}
          >
            忘记密码
          </a>
        </div>
      </div>
    </div>
  );
}
