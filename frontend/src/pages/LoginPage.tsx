import { useState } from 'react';
import type { FormEvent } from 'react';
import { useNavigate, useLocation, Link } from 'react-router-dom';
import {
  Sparkles,
  Mail,
  Lock,
  ArrowRight,
  AlertCircle,
  CheckCircle2,
  LogOut,
  Eye,
  EyeOff,
  ShieldCheck,
} from 'lucide-react';
import { Button } from '../components/ui/Button';
import { useAuth } from '../features/auth/AuthContext';

export function LoginPage() {
  const [isRegister, setIsRegister] = useState(false);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const { user, login, register, logout, isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const from = (location.state as any)?.from?.pathname || '/';

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!email.trim() || !password.trim()) {
      setError('Please provide both your email address and password.');
      return;
    }

    setSubmitting(true);
    setError(null);
    setSuccess(null);

    try {
      if (isRegister) {
        await register({ email, password });
        setSuccess('Account created successfully! Redirecting to study dashboard...');
      } else {
        await login({ email, password });
        setSuccess('Welcome back! Redirecting to study dashboard...');
      }
      setTimeout(() => {
        navigate(from, { replace: true });
      }, 700);
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      if (typeof detail === 'string') {
        setError(detail);
      } else if (Array.isArray(detail)) {
        setError(detail.map((d: any) => d.msg).join(', '));
      } else {
        setError(err.message || 'Authentication failed. Please verify your credentials.');
      }
    } finally {
      setSubmitting(false);
    }
  };

  const handleFillDemo = () => {
    setEmail('test@example.com');
    setPassword('password123');
    setIsRegister(false);
    setError(null);
  };

  if (isAuthenticated && user) {
    return (
      <div className="auth-page">
        <div className="auth-container">
          <div className="auth-header">
            <div className="brand">
              <div className="brand-mark"><Sparkles size={17} /></div>
              <span>Study<span className="brand-accent">mate</span></span>
            </div>
            <h1>Account Connected</h1>
            <p>You are currently signed in with active backend credentials.</p>
          </div>

          <div className="auth-card panel">
            <div style={{ display: 'flex', alignItems: 'center', gap: '16px', marginBottom: '22px' }}>
              <div className="profile-avatar" style={{ width: '52px', height: '52px', fontSize: '19px' }}>
                {user.email.slice(0, 2).toUpperCase()}
              </div>
              <div>
                <strong style={{ display: 'block', fontSize: 'var(--text-md)', color: 'var(--forest)' }}>
                  {user.email}
                </strong>
                <span style={{ fontSize: 'var(--text-xs)', color: 'var(--muted)', display: 'flex', alignItems: 'center', gap: '5px', marginTop: '3px' }}>
                  <ShieldCheck size={14} color="var(--sage)" /> Active Session · ID #{user.id}
                </span>
              </div>
            </div>

            <div style={{ display: 'grid', gap: '10px' }}>
              <Button onClick={() => navigate('/')} variant="primary" className="auth-submit-btn">
                Continue to Dashboard <ArrowRight size={16} />
              </Button>
              <Button onClick={logout} variant="ghost" style={{ display: 'inline-flex', alignItems: 'center', justifyContent: 'center', gap: '6px' }}>
                <LogOut size={15} /> Sign out of this account
              </Button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="auth-page">
      <div className="auth-container">
        <div className="auth-header">
          <div className="brand">
            <div className="brand-mark"><Sparkles size={17} /></div>
            <span>Study<span className="brand-accent">mate</span></span>
          </div>
          <h1>{isRegister ? 'Create your account' : 'Welcome back'}</h1>
          <p>{isRegister ? 'Sign up to start personalized, grounded study sessions' : 'Enter your credentials to access your courses and progress'}</p>
        </div>

        <div className="auth-card">
          <div className="auth-tabs" role="tablist">
            <button
              type="button"
              className={`auth-tab ${!isRegister ? 'selected' : ''}`}
              onClick={() => { setIsRegister(false); setError(null); }}
            >
              Sign In
            </button>
            <button
              type="button"
              className={`auth-tab ${isRegister ? 'selected' : ''}`}
              onClick={() => { setIsRegister(true); setError(null); }}
            >
              Create Account
            </button>
          </div>

          {error && (
            <div className="auth-error" role="alert" style={{ marginBottom: '16px' }}>
              <AlertCircle size={16} style={{ flexShrink: 0, marginTop: '2px' }} />
              <span>{error}</span>
            </div>
          )}

          {success && (
            <div className="auth-success" role="status" style={{ marginBottom: '16px' }}>
              <CheckCircle2 size={16} style={{ flexShrink: 0 }} />
              <span>{success}</span>
            </div>
          )}

          <form className="auth-form" onSubmit={handleSubmit}>
            {/* Email Field */}
            <div className="auth-field">
              <label htmlFor="auth-email">Email address</label>
              <div className="auth-input-wrapper">
                <span className="auth-input-icon">
                  <Mail size={16} />
                </span>
                <input
                  id="auth-email"
                  type="email"
                  className="auth-input"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="name@example.com"
                  autoComplete="email"
                  required
                />
              </div>
            </div>

            {/* Password Field */}
            <div className="auth-field">
              <div className="auth-field-header">
                <label htmlFor="auth-password">Password</label>
              </div>
              <div className="auth-input-wrapper">
                <span className="auth-input-icon">
                  <Lock size={16} />
                </span>
                <input
                  id="auth-password"
                  type={showPassword ? 'text' : 'password'}
                  className="auth-input auth-input-with-toggle"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  autoComplete={isRegister ? 'new-password' : 'current-password'}
                  required
                />
                <button
                  type="button"
                  className="auth-password-toggle"
                  onClick={() => setShowPassword(!showPassword)}
                  aria-label={showPassword ? 'Hide password' : 'Show password'}
                  title={showPassword ? 'Hide password' : 'Show password'}
                >
                  {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
            </div>

            {/* Submit Button */}
            <Button
              type="submit"
              disabled={submitting}
              className="auth-submit-btn"
            >
              {submitting ? 'Authenticating...' : isRegister ? 'Create Account' : 'Sign In'}
              {!submitting && <ArrowRight size={16} />}
            </Button>
          </form>

          {/* Quick Demo Fill Card */}
          <div className="auth-demo-card">
            <div className="auth-demo-info">
              <span className="auth-demo-label">Demo Credentials</span>
              <span className="auth-demo-creds">test@example.com</span>
            </div>
            <button
              type="button"
              className="auth-demo-btn"
              onClick={handleFillDemo}
            >
              Auto Fill
            </button>
          </div>
        </div>

        <div style={{ textAlign: 'center' }}>
          <Link to="/" style={{ color: 'var(--muted)', fontSize: 'var(--text-xs)', textDecoration: 'none' }}>
            ← Back to Home
          </Link>
        </div>
      </div>
    </div>
  );
}
