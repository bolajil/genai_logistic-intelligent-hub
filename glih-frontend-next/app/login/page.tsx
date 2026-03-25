'use client';
import { useState, FormEvent } from 'react';
import { useAuth } from '../contexts/AuthContext';

export default function LoginPage() {
  const { login } = useAuth();
  const [email,    setEmail]    = useState('');
  const [password, setPassword] = useState('');
  const [error,    setError]    = useState('');
  const [loading,  setLoading]  = useState(false);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try { await login(email, password); }
    catch (err: any) { setError(err.message ?? 'Login failed. Please try again.'); }
    finally { setLoading(false); }
  };

  return (
    <div style={{ position: 'relative', minHeight: '100vh', overflow: 'hidden', background: '#070d1a', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>

      {/* Animated grid background */}
      <style>{`
        @keyframes gridPulse { 0%,100%{opacity:.08} 50%{opacity:.18} }
        @keyframes scanline  { 0%{transform:translateY(-100%)} 100%{transform:translateY(100vh)} }
        @keyframes fadeUp    { from{opacity:0;transform:translateY(20px)} to{opacity:1;transform:translateY(0)} }
        @keyframes spin      { to{transform:rotate(360deg)} }
        .login-card          { animation: fadeUp .5s ease forwards; }
      `}</style>

      {/* Grid */}
      <div style={{ position:'fixed', inset:0, backgroundImage:'linear-gradient(rgba(34,211,238,.12) 1px,transparent 1px),linear-gradient(90deg,rgba(34,211,238,.12) 1px,transparent 1px)', backgroundSize:'48px 48px', animation:'gridPulse 4s ease-in-out infinite' }} />
      {/* Teal glow orb */}
      <div style={{ position:'fixed', top:'20%', left:'50%', transform:'translateX(-50%)', width:600, height:600, background:'radial-gradient(circle,rgba(34,211,238,.07) 0%,transparent 70%)', pointerEvents:'none' }} />
      {/* Scan line */}
      <div style={{ position:'fixed', left:0, right:0, height:2, background:'linear-gradient(90deg,transparent,rgba(34,211,238,.3),transparent)', animation:'scanline 6s linear infinite', pointerEvents:'none' }} />

      {/* Card */}
      <div className="login-card" style={{ position:'relative', zIndex:10, width:'100%', maxWidth:420, padding:'0 16px' }}>
        <div style={{ background:'rgba(15,31,61,.85)', border:'1px solid rgba(34,211,238,.2)', borderRadius:16, padding:36, backdropFilter:'blur(20px)', boxShadow:'0 24px 48px rgba(0,0,0,.5),0 0 60px rgba(34,211,238,.06)' }}>

          {/* Logo */}
          <div style={{ display:'flex', alignItems:'center', gap:12, marginBottom:28 }}>
            <div style={{ width:44, height:44, borderRadius:12, background:'linear-gradient(135deg,#22d3ee,#0e7490)', display:'flex', alignItems:'center', justifyContent:'center', color:'#070d1a', fontWeight:900, fontSize:20, boxShadow:'0 0 20px rgba(34,211,238,.4)' }}>G</div>
            <div>
              <div style={{ fontWeight:800, color:'#f1f5f9', fontSize:18, letterSpacing:2 }}>GLIH OPS</div>
              <div style={{ fontSize:10, color:'#94a3b8', letterSpacing:4, textTransform:'uppercase' }}>Cold Chain Intelligence</div>
            </div>
          </div>

          <h1 style={{ fontSize:22, fontWeight:700, color:'#f1f5f9', margin:'0 0 4px' }}>Welcome back</h1>
          <p style={{ fontSize:13, color:'#64748b', margin:'0 0 24px' }}>Sign in to access the operations platform</p>

          {error && (
            <div style={{ marginBottom:20, padding:'12px 16px', borderRadius:8, background:'rgba(239,68,68,.1)', border:'1px solid rgba(239,68,68,.3)', color:'#f87171', fontSize:13 }}>
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} style={{ display:'flex', flexDirection:'column', gap:18 }}>
            <div>
              <label style={{ display:'block', fontSize:11, fontWeight:600, color:'#94a3b8', letterSpacing:'0.08em', textTransform:'uppercase', marginBottom:6 }}>Email</label>
              <input type="email" value={email} onChange={e => setEmail(e.target.value)} placeholder="you@glih.ops" required
                style={{ width:'100%', boxSizing:'border-box', background:'rgba(7,13,26,.8)', border:'1px solid #1e3a5f', borderRadius:8, padding:'12px 14px', fontSize:13, color:'#e2e8f0', outline:'none', fontFamily:'inherit' }}
                onFocus={e => e.target.style.borderColor='#22d3ee'}
                onBlur={e  => e.target.style.borderColor='#1e3a5f'}
              />
            </div>

            <div>
              <label style={{ display:'block', fontSize:11, fontWeight:600, color:'#94a3b8', letterSpacing:'0.08em', textTransform:'uppercase', marginBottom:6 }}>Password</label>
              <input type="password" value={password} onChange={e => setPassword(e.target.value)} placeholder="••••••••" required
                style={{ width:'100%', boxSizing:'border-box', background:'rgba(7,13,26,.8)', border:'1px solid #1e3a5f', borderRadius:8, padding:'12px 14px', fontSize:13, color:'#e2e8f0', outline:'none', fontFamily:'inherit' }}
                onFocus={e => e.target.style.borderColor='#22d3ee'}
                onBlur={e  => e.target.style.borderColor='#1e3a5f'}
              />
            </div>

            <button type="submit" disabled={loading} style={{ padding:'13px', borderRadius:8, border:'none', background: loading ? '#0e7490' : 'linear-gradient(135deg,#22d3ee,#0e7490)', color:'#070d1a', fontWeight:700, fontSize:14, cursor: loading ? 'not-allowed' : 'pointer', display:'flex', alignItems:'center', justifyContent:'center', gap:8, transition:'opacity .2s', boxShadow:'0 0 24px rgba(34,211,238,.25)' }}>
              {loading ? (
                <>
                  <span style={{ width:16, height:16, border:'2px solid rgba(7,13,26,.3)', borderTopColor:'#070d1a', borderRadius:'50%', animation:'spin .7s linear infinite', display:'inline-block' }} />
                  Authenticating…
                </>
              ) : 'Sign In →'}
            </button>
          </form>

          <div style={{ margin:'20px 0', height:1, background:'#1e3a5f' }} />

          <p style={{ textAlign:'center', fontSize:12, color:'#475569', margin:0 }}>
            🔒 JWT secured · bcrypt hashed · Rate limited
          </p>
        </div>

        <p style={{ textAlign:'center', fontSize:11, color:'#334155', marginTop:12 }}>
          Default admin: <span style={{ color:'#22d3ee', fontFamily:'monospace' }}>admin@glih.ops</span> — password change required on first login
        </p>
      </div>
    </div>
  );
}
