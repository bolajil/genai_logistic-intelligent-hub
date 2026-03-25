'use client';
import { useState, FormEvent } from 'react';
import { useAuth } from '../contexts/AuthContext';

export default function ChangePasswordPage() {
  const { user, changePassword, logout } = useAuth();
  const [currentPwd, setCurrentPwd] = useState('');
  const [newPwd,     setNewPwd]     = useState('');
  const [confirmPwd, setConfirmPwd] = useState('');
  const [error,      setError]      = useState('');
  const [loading,    setLoading]    = useState(false);

  const checks = [
    { ok: newPwd.length >= 8,          label: 'At least 8 characters' },
    { ok: /[A-Z]/.test(newPwd),        label: 'Uppercase letter' },
    { ok: /[0-9]/.test(newPwd),        label: 'Number' },
    { ok: /[^A-Za-z0-9]/.test(newPwd), label: 'Special character' },
  ];

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError('');
    if (newPwd !== confirmPwd)  { setError('New passwords do not match.'); return; }
    if (newPwd.length < 8)     { setError('New password must be at least 8 characters.'); return; }
    if (newPwd === currentPwd) { setError('New password must be different from the current password.'); return; }
    setLoading(true);
    try { await changePassword(currentPwd, newPwd); }
    catch (err: any) { setError(err.message ?? 'Password change failed.'); }
    finally { setLoading(false); }
  };

  return (
    <div style={{ position:'relative', minHeight:'100vh', overflow:'hidden', background:'#070d1a', display:'flex', alignItems:'center', justifyContent:'center' }}>
      <style>{`
        @keyframes gridPulse { 0%,100%{opacity:.08} 50%{opacity:.18} }
        @keyframes scanline  { 0%{transform:translateY(-100%)} 100%{transform:translateY(100vh)} }
        @keyframes fadeUp    { from{opacity:0;transform:translateY(20px)} to{opacity:1;transform:translateY(0)} }
        @keyframes spin      { to{transform:rotate(360deg)} }
        .cp-card             { animation: fadeUp .5s ease forwards; }
      `}</style>

      <div style={{ position:'fixed', inset:0, backgroundImage:'linear-gradient(rgba(245,158,11,.08) 1px,transparent 1px),linear-gradient(90deg,rgba(245,158,11,.08) 1px,transparent 1px)', backgroundSize:'48px 48px', animation:'gridPulse 4s ease-in-out infinite' }} />
      <div style={{ position:'fixed', top:'20%', left:'50%', transform:'translateX(-50%)', width:600, height:600, background:'radial-gradient(circle,rgba(245,158,11,.06) 0%,transparent 70%)', pointerEvents:'none' }} />
      <div style={{ position:'fixed', left:0, right:0, height:2, background:'linear-gradient(90deg,transparent,rgba(245,158,11,.3),transparent)', animation:'scanline 6s linear infinite', pointerEvents:'none' }} />

      <div className="cp-card" style={{ position:'relative', zIndex:10, width:'100%', maxWidth:420, padding:'0 16px' }}>
        <div style={{ background:'rgba(15,31,61,.85)', border:'1px solid rgba(245,158,11,.25)', borderRadius:16, padding:36, backdropFilter:'blur(20px)', boxShadow:'0 24px 48px rgba(0,0,0,.5),0 0 60px rgba(245,158,11,.06)' }}>

          {/* Header */}
          <div style={{ display:'flex', alignItems:'center', gap:12, marginBottom:20 }}>
            <div style={{ width:44, height:44, borderRadius:12, background:'linear-gradient(135deg,#f59e0b,#d97706)', display:'flex', alignItems:'center', justifyContent:'center', fontSize:22, boxShadow:'0 0 20px rgba(245,158,11,.4)' }}>🔑</div>
            <div>
              <div style={{ fontWeight:800, color:'#f1f5f9', fontSize:16 }}>Change Password</div>
              <div style={{ fontSize:10, color:'#94a3b8', letterSpacing:3, textTransform:'uppercase' }}>Required before continuing</div>
            </div>
          </div>

          {/* Notice banner */}
          <div style={{ marginBottom:20, padding:'12px 16px', borderRadius:8, background:'rgba(245,158,11,.08)', border:'1px solid rgba(245,158,11,.25)' }}>
            <p style={{ color:'#fbbf24', fontSize:13, fontWeight:600, margin:'0 0 2px' }}>Security requirement</p>
            <p style={{ color:'rgba(251,191,36,.7)', fontSize:12, margin:0 }}>
              {user?.role === 'admin'
                ? 'The default admin password must be changed before accessing the platform.'
                : 'You are required to set a new password before continuing.'}
            </p>
          </div>

          {error && (
            <div style={{ marginBottom:16, padding:'12px 16px', borderRadius:8, background:'rgba(239,68,68,.1)', border:'1px solid rgba(239,68,68,.3)', color:'#f87171', fontSize:13 }}>
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} style={{ display:'flex', flexDirection:'column', gap:14 }}>
            {[
              { label:'Current Password', val:currentPwd, set:setCurrentPwd, ph:'Your current password' },
              { label:'New Password',     val:newPwd,     set:setNewPwd,     ph:'Min. 8 characters' },
              { label:'Confirm New Password', val:confirmPwd, set:setConfirmPwd, ph:'••••••••' },
            ].map(({ label, val, set, ph }) => (
              <div key={label}>
                <label style={{ display:'block', fontSize:11, fontWeight:600, color:'#94a3b8', letterSpacing:'0.08em', textTransform:'uppercase', marginBottom:6 }}>{label}</label>
                <input type="password" value={val} onChange={e => set(e.target.value)} placeholder={ph} required
                  style={{ width:'100%', boxSizing:'border-box', background:'rgba(7,13,26,.8)', border:`1px solid ${label==='Confirm New Password' && confirmPwd && newPwd!==confirmPwd ? 'rgba(239,68,68,.5)' : '#1e3a5f'}`, borderRadius:8, padding:'12px 14px', fontSize:13, color:'#e2e8f0', outline:'none', fontFamily:'inherit' }}
                  onFocus={e => e.target.style.borderColor='#f59e0b'}
                  onBlur={e  => e.target.style.borderColor=(label==='Confirm New Password' && confirmPwd && newPwd!==confirmPwd ? 'rgba(239,68,68,.5)' : '#1e3a5f')}
                />
                {label==='Confirm New Password' && confirmPwd && newPwd!==confirmPwd && (
                  <p style={{ marginTop:4, fontSize:11, color:'#f87171' }}>Passwords do not match</p>
                )}
              </div>
            ))}

            {/* Strength indicators */}
            {newPwd && (
              <ul style={{ margin:0, padding:'0 4px', listStyle:'none', display:'flex', flexDirection:'column', gap:3 }}>
                {checks.map(({ ok, label }) => (
                  <li key={label} style={{ fontSize:11, color: ok ? '#10b981' : '#475569', display:'flex', alignItems:'center', gap:6 }}>
                    <span>{ok ? '✓' : '○'}</span>{label}
                  </li>
                ))}
              </ul>
            )}

            <button type="submit" disabled={loading || (!!confirmPwd && newPwd !== confirmPwd)} style={{ marginTop:4, padding:'13px', borderRadius:8, border:'none', background:'linear-gradient(135deg,#f59e0b,#d97706)', color:'#070d1a', fontWeight:700, fontSize:14, cursor:(loading || (!!confirmPwd && newPwd!==confirmPwd)) ? 'not-allowed' : 'pointer', display:'flex', alignItems:'center', justifyContent:'center', gap:8, opacity:(loading || (!!confirmPwd && newPwd!==confirmPwd)) ? .6 : 1, boxShadow:'0 0 24px rgba(245,158,11,.2)' }}>
              {loading ? (
                <><span style={{ width:16, height:16, border:'2px solid rgba(7,13,26,.3)', borderTopColor:'#070d1a', borderRadius:'50%', animation:'spin .7s linear infinite', display:'inline-block' }} />Updating…</>
              ) : 'Set New Password'}
            </button>
          </form>

          <button onClick={logout} style={{ marginTop:14, width:'100%', textAlign:'center', fontSize:12, color:'#475569', background:'none', border:'none', cursor:'pointer', padding:0 }}>
            Sign out instead
          </button>
        </div>
      </div>
    </div>
  );
}
