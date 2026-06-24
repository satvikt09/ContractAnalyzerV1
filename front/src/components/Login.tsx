export default function Login() {
  return (
    <>
      <style>{`
        .login-shell {
          min-height: 100vh;
          display: grid;
          place-items: center;
          padding: 24px;
          background: #ffffff;
        }
        .login-card {
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 16px;
          max-width: 520px;
          text-align: center;
        }
        .login-title {
          font-size: 42px;
          font-weight: 800;
          color: #810055;
          margin: 0;
        }
        .login-sub {
          margin: 0;
          color: #333;
          opacity: .9;
          font-size: 16px;
        }
        .ms-login-button {
          display: inline-flex;
          align-items: center;
          justify-content: center;
          border-radius: 12px;
          padding: 12px 18px;
          min-width: 240px;
          background: #810055;
          color: #fff;
          text-decoration: none;
          font-weight: 600;
          border: 1px solid #6a0048;
          box-shadow: 0 6px 18px rgba(129,0,85,.3);
          transition: transform .2s ease, box-shadow .2s ease;
          cursor: pointer;
        }
        .ms-login-button:hover {
          transform: translateY(-1px);
          box-shadow: 0 10px 30px rgba(129,0,85,.32);
        }
        .login-note {
          color: #4a4a4a;
          font-size: 13px;
          opacity: .8;
          margin: 0;
        }
      `}</style>
      <div className="login-shell">
        <div className="login-card">
          <img src="/logo.svg" alt="Logo" style={{ height: "40px" }} />
          <h1 className="login-title">Welcome</h1>
          <p className="login-sub">Use your Microsoft Entra ID account to sign in.</p>
          <a className="ms-login-button" href="/accounts/microsoft/login/?process=login">
            Login with SSO
          </a>
          <p className="login-note">Configure Entra credentials via environment variables or a SocialApp row.</p>
        </div>
      </div>
    </>
  )
}
