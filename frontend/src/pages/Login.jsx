import React, { useState } from 'react';
import { ArrowRight, CheckCircle2, Eye, EyeOff, Lock, Mail, Moon, Sparkles, Sun, User as UserIcon } from 'lucide-react';
import {
  registerWithEmail,
  loginWithEmail,
  signInWithGoogle,
  sendFirebasePasswordReset,
  sendFirebaseEmailVerification,
  firebaseSignOut,
} from '../firebase-client';
import { api } from '../api';
import GoogleMark from '../components/GoogleMark';

const EMAIL_REGEX = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;

export default function Login({ onLoginSuccess, darkMode, onToggleDarkMode }) {
  const [authMode, setAuthMode] = useState('signin');

  // Form fields
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);

  // UI states
  const [loading, setLoading] = useState(false);
  const [googleLoading, setGoogleLoading] = useState(false);
  const [error, setError] = useState('');

  // Password Reset states
  const [resetOpen, setResetOpen] = useState(false);
  const [resetEmail, setResetEmail] = useState('');
  const [resetLoading, setResetLoading] = useState(false);
  const [resetError, setResetError] = useState('');
  const [resetSuccess, setResetSuccess] = useState('');

  const resetState = () => setError('');
  const switchMode = (m) => { setAuthMode(m); resetState(); };

  /**
   * Helper: after Firebase auth, sync user to backend and call onLoginSuccess
   */
  const syncWithBackend = async ({ idToken, displayName, email: userEmail }) => {
    const res = await api.loginWithGoogle(idToken, displayName, userEmail);
    onLoginSuccess(res.user);
  };

  /**
   * Email + Password Register
   */
  const handleRegister = async (e) => {
    e.preventDefault();
    setError('');
    const norm = email.trim().toLowerCase();
    if (!EMAIL_REGEX.test(norm)) return setError('Please enter a valid email address.');
    if (password.length < 6) return setError('Password must contain at least 6 characters.');
    if (!name.trim()) return setError('Please enter your full name.');

    setLoading(true);
    try {
      const result = await registerWithEmail(name.trim(), norm, password);
      await sendFirebaseEmailVerification();
      await firebaseSignOut();
      setPassword('');
      setError('Account created. Please verify your email from the verification link we sent before signing in.');
      setAuthMode('signin');
      return;
    } catch (err) {
      const msg = err.message?.includes('already') || err.message?.includes('Password')
        ? err.message
        : (firebaseErrorMessage(err) || 'Registration failed. Please try again.');
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  /**
   * Email + Password Sign In
   */
  const handleSignIn = async (e) => {
    e.preventDefault();
    setError('');
    const norm = email.trim().toLowerCase();
    if (!EMAIL_REGEX.test(norm)) return setError('Please enter a valid email address.');
    if (password.length < 6) return setError('Password must contain at least 6 characters.');

    setLoading(true);
    try {
      const result = await loginWithEmail(norm, password);
      if (!result.user.emailVerified) {
        await firebaseSignOut();
        setError('Please verify your email address before signing in. Check your inbox for the verification link.');
        return;
      }
      await syncWithBackend(result);
      return;
    } catch (err) {
      const msg = err.message?.includes('Invalid') || err.message?.includes('password') || err.message?.includes('Account')
        ? err.message
        : (firebaseErrorMessage(err) || 'Invalid email or password. Please check your credentials.');
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  /**
   * Google Sign In
   */
  const googleLogin = async () => {
    setError('');
    setGoogleLoading(true);
    try {
      const result = await signInWithGoogle();
      if (result) {
        await syncWithBackend(result);
      }
    } catch (err) {
      console.error('Google sign-in error:', err);
      const msg = firebaseErrorMessage(err) || err.message;
      setError(msg || 'Google sign-in failed. Please try again.');
    } finally {
      setGoogleLoading(false);
    }
  };

  /**
   * Firebase Password Reset Email
   */
  const handleSendReset = async (e) => {
    e.preventDefault();
    setResetError('');
    setResetSuccess('');
    const norm = resetEmail.trim().toLowerCase();
    if (!EMAIL_REGEX.test(norm)) return setResetError('Please enter a valid email address.');

    setResetLoading(true);
    try {
      await sendFirebasePasswordReset(norm);
      setResetSuccess(`Password reset link sent to ${norm}. Please check your inbox (and spam folder).`);
    } catch (err) {
      const msg = firebaseErrorMessage(err);
      setResetError(msg || 'Failed to send reset email. Please try again.');
    } finally {
      setResetLoading(false);
    }
  };

  const handleOpenReset = () => {
    setResetEmail(email || '');
    setResetError('');
    setResetSuccess('');
    setResetOpen(true);
  };

  const busy = loading || googleLoading;

  return (
    <div className="login-page">
      <div className="login-shell premium-login-shell">
        {/* Left editorial panel */}
        <section className="login-editorial">
          <div className="login-topline">
            <button className="brand-block login-brand" type="button" aria-label="NEXORA AI">
              <span className="brand-mark"><Sparkles size={18} /></span>
              <span className="brand-copy">
                <span className="brand-name">NEXORA</span>
                <span className="brand-subtitle">Intelligent Documents,<br />Smarter Workflows</span>
              </span>
            </button>
            <button className="header-icon-btn login-theme-button" type="button" onClick={onToggleDarkMode} aria-label="Toggle dark mode">
              {darkMode ? <Sun size={15} /> : <Moon size={15} />}
            </button>
          </div>

          <div className="login-editorial-copy">
            <div className="page-kicker">Document intelligence</div>
            <h1>Turn<br />documents<br /><em>into decisions.</em></h1>
            <p>Read business documents with AI, surface risk, and move every approval through a workflow that feels deliberate rather than mechanical.</p>
            <div className="login-points">
              {['PDF, DOCX and TXT extraction', 'Risk scoring and approval routing', 'Firebase-backed audit history'].map((item) => (
                <div key={item}><CheckCircle2 size={15} /><span>{item}</span></div>
              ))}
            </div>
          </div>

          <div className="login-credit">Developed and Designed by <strong>Deepak Gupta</strong></div>

          <svg className="login-rajput-ornament" viewBox="0 0 460 460" aria-hidden="true" focusable="false">
            <defs>
              <g id="nexora-raj-paisley" stroke="#214b3a" strokeWidth="1.8" strokeLinejoin="round">
                <path d="M0 -23 C-12 -31 -27 -19 -25 -4 C-23 10 -8 24 0 31 C8 22 23 8 25 -5 C27 -20 12 -31 0 -23Z" fill="#eadcc0" />
                <path d="M0 20 C-10 9 -9 -8 0 -13 C10 -19 19 -9 15 1 C12 9 3 10 1 4 C0 1 3 -2 6 -1" fill="none" stroke="#aa7a24" strokeWidth="2.2" strokeLinecap="round" />
                <path d="M0 -18 C-4 -13 -5 -8 -3 -4" fill="none" stroke="#2e6450" strokeWidth="1.5" strokeLinecap="round" />
                <circle cx="0" cy="-23" r="2.5" fill="#aa7a24" stroke="none" />
              </g>
              <g id="nexora-raj-lotus" stroke="#214b3a" strokeWidth="1.45" strokeLinejoin="round">
                <g fill="#eadcc0">
                  <path d="M0 -17 C-10 -12 -10 -2 0 5 C10 -2 10 -12 0 -17Z" />
                  <path d="M0 -17 C-10 -12 -10 -2 0 5 C10 -2 10 -12 0 -17Z" transform="rotate(45)" />
                  <path d="M0 -17 C-10 -12 -10 -2 0 5 C10 -2 10 -12 0 -17Z" transform="rotate(90)" />
                  <path d="M0 -17 C-10 -12 -10 -2 0 5 C10 -2 10 -12 0 -17Z" transform="rotate(135)" />
                  <path d="M0 -17 C-10 -12 -10 -2 0 5 C10 -2 10 -12 0 -17Z" transform="rotate(180)" />
                  <path d="M0 -17 C-10 -12 -10 -2 0 5 C10 -2 10 -12 0 -17Z" transform="rotate(225)" />
                  <path d="M0 -17 C-10 -12 -10 -2 0 5 C10 -2 10 -12 0 -17Z" transform="rotate(270)" />
                  <path d="M0 -17 C-10 -12 -10 -2 0 5 C10 -2 10 -12 0 -17Z" transform="rotate(315)" />
                </g>
                <circle r="6.2" fill="#aa7a24" />
                <circle r="2.2" fill="#214b3a" stroke="none" />
              </g>
              <g id="nexora-raj-feather" stroke="#214b3a" strokeWidth="1.6" strokeLinejoin="round">
                <path d="M0 27 C-19 9 -24 -10 -12 -26 C-5 -36 8 -38 18 -29 C31 -17 20 2 0 27Z" fill="#e8d8b8" />
                <path d="M0 24 C2 5 6 -12 15 -28" fill="none" stroke="#aa7a24" strokeWidth="2" strokeLinecap="round" />
                <path d="M5 -15 C-5 -22 -12 -12 -7 -4 C-3 2 7 1 10 -6 C12 -11 9 -14 5 -15Z" fill="#2e6450" />
                <circle cx="3" cy="-8" r="3.2" fill="#aa7a24" stroke="none" />
              </g>
            </defs>

            <circle cx="230" cy="230" r="226" fill="none" stroke="#214b3a" strokeWidth="1.15" opacity=".24" />
            <circle cx="230" cy="230" r="217" fill="none" stroke="#aa7a24" strokeWidth=".9" strokeDasharray="1.5 7" strokeLinecap="round" opacity=".48" />

            <g opacity=".92">
              <use href="#nexora-raj-feather" transform="translate(43 238) rotate(-33) scale(.62)" />
              <use href="#nexora-raj-paisley" transform="translate(78 385) rotate(-38) scale(.62)" />
              <use href="#nexora-raj-lotus" transform="translate(230 454) scale(.72)" />
              <use href="#nexora-raj-paisley" transform="translate(382 385) rotate(38) scale(.62)" />
              <use href="#nexora-raj-feather" transform="translate(417 238) rotate(33) scale(.62)" />
            </g>

            <g fill="#aa7a24" opacity=".68">
              <circle cx="26" cy="305" r="2" />
              <circle cx="126" cy="438" r="1.7" />
              <circle cx="334" cy="438" r="1.7" />
              <circle cx="434" cy="305" r="2" />
            </g>
            <g fill="none" stroke="#2e6450" strokeWidth="1.2" opacity=".55">
              <path d="M57 337 l5 -5 l5 5 l-5 5Z" />
              <path d="M398 337 l5 -5 l5 5 l-5 5Z" />
            </g>
          </svg>
        </section>

        {/* Right auth panel */}
        <section className="login-side premium-login-side">
          <div className="login-form-shell">
            <div className="page-kicker">{authMode === 'signin' ? 'WELCOME BACK' : 'CREATE AN ACCOUNT'}</div>
            <h2>{authMode === 'signin' ? 'Sign in.' : 'Register.'}</h2>
            <p>{authMode === 'signin' ? 'Use your email or continue with Google.' : 'Create your account to start managing document workflows.'}</p>

            {error && <div className="login-error" role="alert">{error}</div>}

            {/* Google & Demo Sign In */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              <button className="google-login" type="button" onClick={googleLogin} disabled={busy}>
                <GoogleMark />
                <span>{googleLoading ? 'Connecting to Google…' : 'Continue with Google'}</span>
              </button>

            </div>

            <div className="login-divider">
              <span>{authMode === 'signin' ? 'or continue with email' : 'or sign up with email'}</span>
            </div>

            {/* Email / Password form */}
            <form className="login-form" onSubmit={authMode === 'signup' ? handleRegister : handleSignIn} noValidate>
              {authMode === 'signup' && (
                <label>
                  <span className="login-label">Full Name</span>
                  <div className="login-field">
                    <UserIcon size={15} />
                    <input
                      type="text"
                      value={name}
                      onChange={(e) => setName(e.target.value)}
                      placeholder="Deepak Gupta"
                      required
                    />
                  </div>
                </label>
              )}
              <label>
                <span className="login-label">Email address</span>
                <div className="login-field">
                  <Mail size={15} />
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="name@example.com"
                    autoComplete="email"
                    required
                  />
                </div>
              </label>
              <label>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
                  <span className="login-label" style={{ marginBottom: 0 }}>Password</span>
                  {authMode === 'signin' && (
                    <button
                      type="button"
                      onClick={handleOpenReset}
                      style={{ background: 'none', border: 'none', color: '#8e6b32', fontSize: 11, fontWeight: 600, cursor: 'pointer', textDecoration: 'underline' }}
                    >
                      Forgot password?
                    </button>
                  )}
                </div>
                <div className="login-field password-field">
                  <Lock size={15} />
                  <input
                    type={showPassword ? 'text' : 'password'}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="At least 6 characters"
                    autoComplete={authMode === 'signin' ? 'current-password' : 'new-password'}
                    minLength={6}
                    required
                  />
                  <button
                    type="button"
                    className="password-toggle"
                    onClick={() => setShowPassword((value) => !value)}
                    aria-label={showPassword ? 'Hide password' : 'Show password'}
                    title={showPassword ? 'Hide password' : 'Show password'}
                  >
                    {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                  </button>
                </div>
              </label>

              <button className="primary-btn login-submit" type="submit" disabled={busy}>
                <span>{loading ? (authMode === 'signin' ? 'Signing in…' : 'Creating account…') : (authMode === 'signin' ? 'Sign in' : 'Create Account')}</span>
                <ArrowRight size={14} />
              </button>
            </form>

            <div className="login-toggle-footer">
              {authMode === 'signin' ? (
                <>Don&apos;t have an account? <button type="button" onClick={() => switchMode('signup')}>Create Account</button></>
              ) : (
                <>Already have an account? <button type="button" onClick={() => switchMode('signin')}>Sign in</button></>
              )}
            </div>
          </div>
        </section>
      </div>

      {/* Password Reset Modal */}
      {resetOpen && (
        <div className="editorial-modal-backdrop" role="presentation" onClick={(e) => { if (e.target === e.currentTarget) setResetOpen(false); }}>
          <div className="editorial-modal" style={{ maxWidth: 420, borderRadius: 20, padding: '28px 28px 24px' }} role="dialog" aria-modal="true">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 12 }}>
              <div>
                <div className="page-kicker" style={{ color: '#a9814c', letterSpacing: '0.08em', fontWeight: 700 }}>PASSWORD RECOVERY</div>
                <h2 style={{ fontSize: 22, margin: '4px 0 6px', color: '#1d2233' }}>Forgot your password?</h2>
              </div>
              <button
                type="button"
                onClick={() => setResetOpen(false)}
                style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: 20, lineHeight: 1, color: '#666' }}
                aria-label="Close"
              >×</button>
            </div>

            <p style={{ fontSize: 12, color: '#5a6178', lineHeight: 1.5, margin: '0 0 16px' }}>
              Enter your account email and we&apos;ll send a password reset link to your inbox.
            </p>

            {resetError && <div className="login-error" style={{ marginBottom: 14 }} role="alert">{resetError}</div>}

            {resetSuccess ? (
              <div style={{ padding: '12px 14px', borderRadius: 10, background: '#eef8f2', border: '1px solid #c8e8d4', color: '#1f6b43', fontSize: 12, fontWeight: 600, marginBottom: 16 }}>
                ✓ {resetSuccess}
              </div>
            ) : (
              <form onSubmit={handleSendReset}>
                <label style={{ display: 'block', marginBottom: 16 }}>
                  <span className="login-label" style={{ fontSize: 10, letterSpacing: '0.06em' }}>EMAIL ADDRESS</span>
                  <div className="login-field" style={{ marginTop: 6 }}>
                    <Mail size={15} />
                    <input
                      type="email"
                      value={resetEmail}
                      onChange={(e) => setResetEmail(e.target.value)}
                      placeholder="name@example.com"
                      required
                    />
                  </div>
                </label>
                <button
                  className="primary-btn"
                  type="submit"
                  disabled={resetLoading}
                  style={{ width: '100%', justifyContent: 'center', padding: '12px 16px', background: '#1f4333', color: '#fff', borderRadius: 24 }}
                >
                  {resetLoading ? 'Sending…' : <><span>Send reset link</span> <ArrowRight size={14} /></>}
                </button>
              </form>
            )}

            {resetSuccess && (
              <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: 12 }}>
                <button
                  className="primary-btn"
                  type="button"
                  onClick={() => setResetOpen(false)}
                  style={{ background: '#1f4333', color: '#fff', borderRadius: 24, padding: '10px 20px' }}
                >
                  Done
                </button>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

/**
 * Convert Firebase Auth error codes to human-friendly messages.
 */
function firebaseErrorMessage(err) {
  const code = err?.code || '';
  const messages = {
    'auth/email-already-in-use': 'An account with this email already exists. Try signing in instead.',
    'auth/invalid-email': 'Please enter a valid email address.',
    'auth/weak-password': 'Password must be at least 6 characters.',
    'auth/user-not-found': 'No account found with this email. Please register first.',
    'auth/wrong-password': 'Incorrect password. Please try again.',
    'auth/invalid-credential': 'Incorrect email or password. Please try again.',
    'auth/too-many-requests': 'Too many failed attempts. Please wait a moment and try again.',
    'auth/network-request-failed': 'Network error. Please check your connection and try again.',
    'auth/popup-blocked': 'Google sign-in popup was blocked. Please allow popups or allow the popup and try again.',
    'auth/user-disabled': 'This account has been disabled. Please contact support.',
    'auth/unauthorized-domain': 'This domain is not authorized in Firebase Console.',
    'auth/operation-not-allowed': 'Google Sign-In is disabled in Firebase Console.',
    'auth/api-key-not-valid': 'Firebase API key is invalid. Please check configuration.',
  };
  if (err?.message && err.message.includes('api-key-not-valid')) {
    return 'Firebase API key is invalid. Please check configuration.';
  }
  return messages[code] || err?.message || null;
}
