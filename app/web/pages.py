"""Static HTML snippets served by FastAPI for lightweight UI flows."""

PORTAL_HTML = """
<!doctype html>
<html lang=\"en\">
<head>
    <meta charset=\"utf-8\" />
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
    <title>CivicBriefs.AI Workspace</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Manrope:wght@500;600;700;800&family=Public+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            color-scheme: light;
            --bg: #cfdbd5;
            --ink: #18332d;
            --ink-soft: #35534b;
            --muted: #5e736b;
            --hero-surface: rgba(231, 239, 235, 0.68);
            --panel-surface: rgba(248, 251, 249, 0.92);
            --line: #b8cac2;
            --line-strong: #9eb4aa;
            --accent: #21805f;
            --accent-deep: #176149;
            --accent-soft: #dbe7e1;
            --error: #b42318;
            --success: #0f766e;
        }

        * { box-sizing: border-box; }

        body {
            margin: 0;
            min-height: 100vh;
            color: var(--ink);
            font-family: "Public Sans", "Segoe UI", sans-serif;
            display: flex;
            align-items: flex-start;
            justify-content: center;
            padding: clamp(32px, 5.2vh, 54px) 16px 16px;
            background:
                radial-gradient(circle at 8% 10%, rgba(255,255,255,0.55), transparent 36%),
                radial-gradient(circle at 88% 8%, rgba(255,255,255,0.46), transparent 31%),
                linear-gradient(160deg, #c6d3cc 0%, #dce7e2 46%, #c2d0c8 100%);
            -webkit-font-smoothing: antialiased;
            text-rendering: optimizeLegibility;
        }

        .shell {
            width: min(1260px, 100%);
            display: grid;
            gap: clamp(24px, 2.3vw, 34px);
            grid-template-columns: minmax(560px, 0.95fr) minmax(540px, 1.05fr);
            align-items: stretch;
            padding: 2px;
        }

        .hero,
        .panel {
            border-radius: 28px;
            border: 1px solid var(--line);
            backdrop-filter: blur(7px);
            -webkit-backdrop-filter: blur(7px);
            box-shadow:
                0 36px 72px rgba(27, 45, 38, 0.16),
                inset 0 1px 0 rgba(255, 255, 255, 0.62);
            height: 100%;
        }

        .hero {
            background: linear-gradient(145deg, rgba(241, 247, 244, 0.62), var(--hero-surface));
            padding: clamp(30px, 2.7vw, 40px);
            position: relative;
            overflow: hidden;
            display: flex;
            flex-direction: column;
            align-items: center;
            text-align: center;
            justify-content: space-between;
            gap: 16px;
            min-height: clamp(540px, 63vh, 600px);
        }

        .hero > * {
            position: relative;
            z-index: 1;
        }

        .hero::after {
            content: "";
            position: absolute;
            inset: 0;
            background:
                radial-gradient(circle at 16% 16%, rgba(255,255,255,0.35), transparent 45%),
                linear-gradient(120deg, transparent 40%, rgba(255,255,255,0.2) 58%, transparent 70%);
            pointer-events: none;
        }

        .eyebrow {
            margin: 0;
            text-transform: uppercase;
            letter-spacing: 0.12em;
            color: #4f6962;
            font-size: 11px;
            font-weight: 800;
            font-family: "Manrope", "Public Sans", sans-serif;
            padding: 6px 12px;
            border-radius: 999px;
            border: 1px solid #b0c2ba;
            background: rgba(244, 249, 246, 0.78);
        }

        .hero h1 {
            margin: 0;
            font-family: "Manrope", "Public Sans", sans-serif;
            font-size: clamp(36px, 3vw, 50px);
            line-height: 1.08;
            letter-spacing: -0.035em;
            color: #304d46;
            max-width: 16.2ch;
            text-wrap: balance;
            font-weight: 800;
        }

        .hero p {
            margin: 2px 0 0;
            max-width: 54ch;
            color: #3d5c54;
            font-size: clamp(15px, 0.95vw, 18px);
            font-weight: 500;
            line-height: 1.58;
        }

        .hero ul {
            margin: 0;
            padding-left: 0;
            color: #4a655e;
            font-size: clamp(14px, 0.9vw, 16px);
            line-height: 1.56;
            font-weight: 550;
            max-width: 48ch;
            list-style: none;
            display: grid;
            gap: 8px;
        }

        .hero li {
            position: relative;
            padding-left: 18px;
            text-align: left;
        }

        .hero li::before {
            content: "";
            width: 7px;
            height: 7px;
            border-radius: 999px;
            background: linear-gradient(180deg, #2b8d69, #1f6f54);
            box-shadow: 0 0 0 3px rgba(43, 141, 105, 0.14);
            position: absolute;
            left: 0;
            top: 0.58em;
        }

        .hero-badges {
            margin-top: 4px;
            display: flex;
            flex-wrap: wrap;
            gap: 9px;
            justify-content: center;
        }

        .hero-badges span {
            display: inline-flex;
            align-items: center;
            border-radius: 999px;
            padding: 8px 14px;
            border: 1px solid #9fb4aa;
            background: linear-gradient(180deg, rgba(249, 252, 251, 0.96), rgba(239, 247, 243, 0.92));
            color: #4d655e;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            font-size: 11px;
            font-weight: 800;
            font-family: "Manrope", "Public Sans", sans-serif;
            white-space: nowrap;
            box-shadow: 0 8px 18px rgba(23, 53, 44, 0.08), inset 0 1px 0 rgba(255,255,255,0.8);
        }

        .panel {
            background: var(--panel-surface);
            padding: clamp(22px, 1.8vw, 28px);
            display: flex;
            flex-direction: column;
            gap: 4px;
            max-width: none;
            width: 100%;
            justify-self: stretch;
            align-self: stretch;
            overflow: visible;
        }

        .panel h2 {
            margin: 0;
            font-family: "Manrope", "Public Sans", sans-serif;
            font-size: clamp(34px, 2.6vw, 44px);
            letter-spacing: -0.03em;
            color: #102b25;
            line-height: 1.1;
        }

        .panel .sub {
            margin: 8px 0 14px;
            color: #54706a;
            font-size: 15px;
            line-height: 1.42;
        }

        .tabs {
            display: flex;
            gap: 6px;
            margin-bottom: 14px;
            background: var(--accent-soft);
            padding: 6px;
            border-radius: 999px;
            border: 1px solid var(--line);
        }

        .tab-btn {
            flex: 1;
            border-radius: 999px;
            border: 0;
            padding: 10px 16px;
            color: #5f746c;
            background: transparent;
            font-weight: 700;
            font-size: 16px;
            font-family: "Manrope", "Public Sans", sans-serif;
            cursor: pointer;
            transition: transform 0.2s ease, background 0.2s ease, color 0.2s ease, box-shadow 0.2s ease;
        }

        .tab-btn.active {
            background: linear-gradient(180deg, #238260, #1a6a4f);
            box-shadow: 0 2px 0 rgba(255,255,255,0.35) inset, 0 6px 16px rgba(36, 99, 76, 0.34);
            color: #f6fffb;
            transform: translateY(-1px);
        }

        .form-stage {
            position: relative;
            min-height: 0;
            height: auto;
        }

        .auth-form {
            position: static;
            flex-direction: column;
            gap: 10px;
            display: none;
        }

        .auth-form.active {
            display: flex;
        }

        h3 {
            margin: 0;
            font-family: "Manrope", "Public Sans", sans-serif;
            font-size: clamp(24px, 1.35vw, 30px);
            letter-spacing: -0.02em;
            color: #12302a;
            line-height: 1.12;
        }

        .form-note {
            margin: 2px 0 2px;
            color: #5e746c;
            font-size: 13px;
            line-height: 1.4;
        }

        label {
            display: flex;
            flex-direction: column;
            gap: 5px;
            font-size: 13px;
            color: #16362f;
            font-weight: 700;
            font-family: "Manrope", "Public Sans", sans-serif;
            line-height: 1.25;
            letter-spacing: -0.01em;
        }

        input {
            width: 100%;
            min-height: 42px;
            padding: 9px 13px;
            border-radius: 14px;
            border: 1px solid var(--line);
            background: #f5faf7;
            color: #132f29;
            font-size: 13px;
            font-family: "Public Sans", "Segoe UI", sans-serif;
            transition: border-color 0.18s ease, box-shadow 0.18s ease, background 0.18s ease;
        }

        input::placeholder {
            color: #7f938c;
        }

        input:focus {
            outline: none;
            border-color: var(--accent);
            background: #fbfffd;
            box-shadow: 0 0 0 4px rgba(33, 128, 95, 0.15);
        }

        .password-row {
            position: relative;
        }

        .password-row input {
            padding-right: 84px;
        }

        .toggle-pass {
            position: absolute;
            top: 50%;
            right: 8px;
            transform: translateY(-50%);
            border: 1px solid #aac0b6;
            background: #eaf3ef;
            color: #1f6a51;
            border-radius: 10px;
            font-size: 12px;
            padding: 6px 10px;
            font-weight: 700;
            cursor: pointer;
            font-family: "Manrope", "Public Sans", sans-serif;
            transition: background 0.15s ease, color 0.15s ease, border-color 0.15s ease;
        }

        .toggle-pass:hover {
            background: #e0ede7;
            border-color: #8daaa0;
        }

        button.primary {
            border: none;
            border-radius: 16px;
            padding: 11px 18px;
            margin-top: auto;
            background: linear-gradient(180deg, #238260, #185e46);
            color: #f1faf5;
            font-weight: 800;
            font-size: 16px;
            letter-spacing: 0.01em;
            font-family: "Manrope", "Public Sans", sans-serif;
            cursor: pointer;
            min-height: 44px;
            transition: transform 0.15s ease, box-shadow 0.15s ease;
            box-shadow: 0 12px 22px rgba(24, 97, 72, 0.28);
        }

        button.primary:disabled {
            opacity: 0.64;
            cursor: not-allowed;
            box-shadow: none;
        }

        button.primary:hover:not(:disabled) {
            transform: translateY(-1px);
            box-shadow: 0 16px 30px rgba(24, 97, 72, 0.34);
        }

        .status {
            min-height: 20px;
            font-size: 13px;
            color: var(--muted);
            margin-top: 2px;
        }

        .status.error { color: var(--error); }
        .status.success { color: var(--success); }

        .signup-extra {
            display: grid;
            grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
            gap: 14px;
            align-items: start;
        }

        @media (max-width: 1120px) {
            .shell {
                grid-template-columns: 1fr;
                max-width: 820px;
                gap: 18px;
            }
            .panel {
                max-width: 100%;
                justify-self: stretch;
                align-self: start;
            }
            .hero {
                padding: clamp(26px, 5vw, 38px);
                min-height: auto;
            }
            .panel {
                min-height: auto;
            }
            .hero h1,
            .hero p,
            .hero ul {
                max-width: 100%;
            }
            .hero h1 {
                font-size: clamp(38px, 8vw, 56px);
                text-wrap: pretty;
            }
            .hero {
                align-items: center;
                text-align: center;
                justify-content: flex-start;
                gap: 14px;
            }
            .hero ul {
                padding-left: 0;
            }
            .hero-badges {
                justify-content: center;
            }
        }

        @media (max-width: 640px) {
            body {
                padding: 14px 10px;
            }
            .shell {
                gap: 16px;
            }
            .hero,
            .panel {
                border-radius: 22px;
            }
            .hero p,
            .hero ul {
                font-size: 16px;
            }
            .panel h2 {
                font-size: 36px;
            }
            .tab-btn {
                font-size: 16px;
            }
            .form-stage {
                min-height: 0;
            }
            h3 {
                font-size: 30px;
            }
            label {
                font-size: 15px;
            }
            input {
                font-size: 15px;
                min-height: 46px;
            }
            .toggle-pass {
                font-size: 13px;
                padding: 6px 11px;
            }
            .signup-extra {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class=\"shell\">
        <section class=\"hero\">
            <p class="eyebrow">CivicBriefs.ai Aspirant Workspace</p>
            <h1>Manage your UPSC preparation from one unified command center</h1>
            <p>Build consistency with curated current-affairs briefings, adaptive assessments, and a structured, performance-driven study system.</p>
            <ul>
                <li>Review daily capsules mapped to UPSC-relevant topics</li>
                <li>Convert mock-test insights into targeted weekly action plans</li>
                <li>Resume every study session from your latest checkpoint</li>
            </ul>
            <div class="hero-badges">
                <span>Daily Briefs</span>
                <span>Personalized Planner</span>
                <span>Adaptive Assessments</span>
            </div>
        </section>

        <section class=\"panel\">
            <h2>Secure access</h2>
            <p class="sub">Sign in to continue your personalized UPSC workspace.</p>
            <div class=\"tabs\">
                <button class=\"tab-btn active\" data-tab=\"login\">Login</button>
                <button class=\"tab-btn\" data-tab=\"signup\">Sign up</button>
            </div>

            <div class="form-stage">
                <form id=\"loginForm\" class=\"auth-form active\">
                    <h3>Welcome back</h3>
                    <p class="form-note">Continue from your dashboard, capsule feed, and performance tracker.</p>
                    <label>Email
                        <input type=\"email\" id=\"loginEmail\" placeholder=\"you@example.com\" required />
                    </label>
                    <label>Password
                        <div class="password-row">
                            <input type=\"password\" id=\"loginPassword\" placeholder=\"********\" required minlength=\"6\" />
                            <button type="button" class="toggle-pass" data-target="loginPassword">Show</button>
                        </div>
                    </label>
                    <div class=\"status\" data-status=\"login\"></div>
                    <button class=\"primary\" type=\"submit\">Access dashboard</button>
                </form>

                <form id=\"signupForm\" class="auth-form">
                    <h3>Create account</h3>
                    <p class="form-note">Create your account to start a structured, high-impact prep workflow.</p>
                    <label>Full name
                        <input type=\"text\" id=\"signupName\" placeholder=\"Aditi Sharma\" required minlength=\"2\" />
                    </label>
                    <label>Email
                        <input type=\"email\" id=\"signupEmail\" placeholder=\"you@example.com\" required />
                    </label>
                    <div class="signup-extra">
                        <label>Phone number
                            <input type=\"tel\" id=\"signupPhone\" placeholder=\"+91 98xxxxxx\" />
                        </label>
                        <label>Password
                            <div class="password-row">
                                <input type=\"password\" id=\"signupPassword\" placeholder=\"Strong password\" required minlength=\"6\" />
                                <button type="button" class="toggle-pass" data-target="signupPassword">Show</button>
                            </div>
                        </label>
                    </div>
                    <div class=\"status\" data-status=\"signup\"></div>
                    <button class=\"primary\" type=\"submit\">Create account</button>
                </form>
            </div>
        </section>
    </div>

    <script>
    (function () {
        const existingToken = localStorage.getItem('cb_token');
        if (existingToken) {
            window.location.href = '/dashboard';
            return;
        }

        const tabButtons = document.querySelectorAll('.tab-btn');
        const formStage = document.querySelector('.form-stage');
        const forms = {
            login: document.getElementById('loginForm'),
            signup: document.getElementById('signupForm'),
        };

        function syncFormStageHeight(activeTab) {
            if (!formStage) return;
            formStage.style.height = 'auto';
        }

        function setActiveTab(tab) {
            tabButtons.forEach((btn) => {
                btn.classList.toggle('active', btn.dataset.tab === tab);
            });
            Object.entries(forms).forEach(([key, form]) => {
                form.classList.toggle('active', key === tab);
            });
            syncFormStageHeight(tab);
        }

        tabButtons.forEach((btn) => {
            btn.addEventListener('click', () => setActiveTab(btn.dataset.tab));
        });
        window.addEventListener('resize', () => {
            const active = document.querySelector('.tab-btn.active');
            syncFormStageHeight(active ? active.dataset.tab : 'login');
        });
        syncFormStageHeight('login');

        document.querySelectorAll('.toggle-pass').forEach((btn) => {
            btn.addEventListener('click', () => {
                const target = document.getElementById(btn.dataset.target);
                if (!target) return;
                const reveal = target.type === 'password';
                target.type = reveal ? 'text' : 'password';
                btn.textContent = reveal ? 'Hide' : 'Show';
            });
        });

        function setStatus(scope, message, tone) {
            const el = document.querySelector(`[data-status="${scope}"]`);
            if (!el) return;
            el.textContent = message || '';
            el.className = 'status' + (tone ? ` ${tone}` : '');
        }

        async function handleAuth(url, payload, scope, button) {
            setStatus(scope, 'Working...', '');
            button.disabled = true;
            try {
                const res = await fetch(url, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload),
                });
                const data = await res.json();
                if (!res.ok) {
                    throw new Error(data.detail || 'Request failed');
                }
                localStorage.setItem('cb_token', data.token);
                localStorage.setItem('cb_user', JSON.stringify(data.user));
                setStatus(scope, 'Success. Redirecting...', 'success');
                window.location.href = '/dashboard';
            } catch (err) {
                setStatus(scope, err.message || 'Unable to complete request', 'error');
            } finally {
                button.disabled = false;
            }
        }

        forms.login.addEventListener('submit', (event) => {
            event.preventDefault();
            const payload = {
                email: document.getElementById('loginEmail').value,
                password: document.getElementById('loginPassword').value,
            };
            handleAuth('/auth/login', payload, 'login', event.submitter);
        });

        forms.signup.addEventListener('submit', (event) => {
            event.preventDefault();
            const payload = {
                name: document.getElementById('signupName').value,
                email: document.getElementById('signupEmail').value,
                phone_number: document.getElementById('signupPhone').value || null,
                password: document.getElementById('signupPassword').value,
            };
            handleAuth('/auth/signup', payload, 'signup', event.submitter);
        });
    })();
    </script>
</body>
</html>
"""


DASHBOARD_HTML = """
<!doctype html>
<html lang=\"en\">
<head>
    <meta charset=\"utf-8\" />
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
    <title>CivicBriefs Dashboard</title>
    <style>
        :root {
            color-scheme: light;
            --bg: #e2ebe8;
            --panel: #f8fbfa;
            --panel-strong: #ffffff;
            --ink: #16342e;
            --muted: #587069;
            --accent: #1f7b5e;
            --accent-deep: #165e49;
            --border: #c8d7d1;
            --shadow: rgba(22, 42, 35, 0.11);
            --soft: #e8f0ec;
        }

        * { box-sizing: border-box; }

        body {
            margin: 0;
            background:
                radial-gradient(circle at 10% 8%, rgba(255,255,255,0.55), transparent 34%),
                radial-gradient(circle at 88% 6%, rgba(255,255,255,0.45), transparent 30%),
                linear-gradient(165deg, #d7e3de 0%, #e5eeea 48%, #d0ddd8 100%);
            font-family: 'Public Sans', 'Segoe UI', sans-serif;
            color: var(--ink);
            -webkit-font-smoothing: antialiased;
            text-rendering: optimizeLegibility;
        }

        header {
            width: 100%;
            margin: 0;
            padding: 10px clamp(10px, 1.8vw, 22px) 8px;
            display: flex;
            flex-wrap: wrap;
            justify-content: space-between;
            align-items: center;
            gap: 10px;
            position: sticky;
            top: 0;
            z-index: 60;
            background: rgba(230, 238, 234, 0.9);
            border-bottom: 1px solid rgba(186, 203, 196, 0.85);
            backdrop-filter: blur(10px) saturate(130%);
            -webkit-backdrop-filter: blur(10px) saturate(130%);
            box-shadow: 0 10px 28px rgba(27, 50, 43, 0.08);
        }

        header h1 {
            margin: 0;
            font-family: 'Manrope', 'Public Sans', sans-serif;
            font-size: clamp(24px, 2.4vw, 34px);
            letter-spacing: -0.03em;
        }

        header p {
            margin: 2px 0 0;
            color: var(--muted);
            font-size: 13px;
        }

        .logout {
            border: 1px solid var(--border);
            background: linear-gradient(180deg, #ffffff, #f3f8f6);
            border-radius: 999px;
            padding: 10px 18px;
            cursor: pointer;
            font-weight: 700;
            color: var(--ink);
            font-family: 'Manrope', 'Public Sans', sans-serif;
            transition: transform 0.15s ease, box-shadow 0.15s ease;
            box-shadow: 0 10px 20px rgba(29, 55, 47, 0.1);
        }

        .logout:hover {
            transform: translateY(-1px);
        }

        main {
            width: 100%;
            margin: 0;
            padding: 6px clamp(10px, 1.8vw, 22px) 44px;
            display: grid;
            gap: 12px;
        }

        .grid {
            display: grid;
            gap: 14px;
            grid-template-columns: repeat(auto-fit, minmax(230px, 1fr));
        }

        .card {
            background: var(--panel);
            border-radius: 20px;
            padding: 20px;
            border: 1px solid var(--border);
            box-shadow: 0 24px 50px var(--shadow), inset 0 1px 0 rgba(255,255,255,0.8);
        }

        .dashboard-triad {
            align-items: stretch;
        }

        @media (min-width: 1180px) {
            .dashboard-triad {
                grid-template-columns: 1fr 1fr 1.2fr;
            }
        }

        .dashboard-triad .card {
            padding: 20px;
            border-radius: 24px;
            box-shadow: 0 22px 46px rgba(21, 56, 45, 0.1), inset 0 1px 0 rgba(255,255,255,0.78);
            height: 100%;
        }

        .dashboard-triad h3 {
            margin: 0;
            font-size: clamp(28px, 1.6vw, 34px);
            letter-spacing: -0.03em;
            line-height: 1.08;
        }

        .section-subtitle {
            margin: 6px 0 12px;
            color: #56716a;
            font-size: 14px;
            line-height: 1.4;
        }

        .card--focus,
        .card--activity,
        .card--daily {
            display: flex;
            flex-direction: column;
            min-height: 0;
        }

        .news-card {
            display: flex;
            flex-direction: column;
            gap: 16px;
        }

        .chip-group {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 5px;
            border-radius: 999px;
            background: var(--soft);
            flex-wrap: wrap;
            border: 1px solid var(--border);
        }

        .chip {
            border: none;
            background: transparent;
            color: var(--muted);
            font-weight: 700;
            border-radius: 999px;
            padding: 8px 14px;
            cursor: pointer;
            font-size: 14px;
            font-family: 'Manrope', 'Public Sans', sans-serif;
            transition: background 0.2s ease, color 0.2s ease;
        }

        .chip.active {
            background: linear-gradient(180deg, var(--accent), var(--accent-deep));
            color: #f7fffb;
            box-shadow: 0 8px 20px rgba(29, 108, 82, 0.28);
        }

        .news-status {
            font-size: 14px;
            color: var(--muted);
            margin: 0;
        }

        .capsule-controls {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            margin-top: 6px;
            align-items: center;
        }

        .card--daily h3 {
            margin: 0;
            font-size: 42px;
            letter-spacing: -0.03em;
            line-height: 1.05;
            font-family: 'Manrope', 'Public Sans', sans-serif;
            color: #112f29;
        }

        .card--daily .section-subtitle {
            margin: 10px 0 14px;
            color: #4f6c64;
            font-size: 16px;
            line-height: 1.5;
            max-width: 46ch;
        }

        .card--daily #capsuleBadge {
            font-size: 13px;
            padding: 8px 14px;
            font-weight: 800;
            border-radius: 999px;
            border: 1px solid #b7cec6;
            background: linear-gradient(180deg, #d8ebe3 0%, #cfe5dc 100%) !important;
            color: #0f6449 !important;
        }

        .card--daily #pauseCapsuleBtn {
            min-height: 48px;
            padding: 10px 18px;
            border-radius: 14px;
            font-size: 16px;
            font-weight: 700;
            border-color: #abc3ba;
            background: linear-gradient(180deg, #f7fbf9 0%, #ebf4f1 100%);
            color: #1b5d49;
        }

        .card--daily #subscribeStatus {
            margin-top: 12px;
            font-size: 15px;
            font-weight: 500;
            letter-spacing: -0.01em;
        }

        .btn.btn-subtle {
            background: #eef5f2;
            color: #225845;
            border: 1px solid #b9cbc4;
            box-shadow: none;
        }

        .btn.btn-subtle:hover:not(:disabled),
        a.btn.btn-subtle:hover:not(:disabled) {
            box-shadow: none;
        }

        .daily-quote {
            margin-top: auto;
            padding: 14px;
            border: 1px solid #bdd2ca;
            border-radius: 14px;
            background: linear-gradient(180deg, #fcfffd 0%, #f2f8f5 100%);
            min-height: 220px;
            box-shadow: inset 0 1px 0 rgba(255,255,255,0.88);
        }

        .daily-quote__label {
            margin: 0 0 6px;
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 0.1em;
            color: #526a63;
            font-weight: 800;
        }

        .daily-quote__text {
            margin: 0;
            color: #274b42;
            font-size: 15px;
            line-height: 1.42;
            font-weight: 700;
        }

        .capsule-calendar-line {
            margin-top: 12px;
            display: flex;
            gap: 8px;
            overflow-x: auto;
            padding: 2px 2px 4px;
            scrollbar-width: thin;
            scrollbar-color: #9ab2a9 transparent;
        }

        .capsule-day-chip {
            border: 1px solid #bed1ca;
            border-radius: 10px;
            background: #f5faf8;
            color: #33564d;
            font-size: 12px;
            font-weight: 700;
            padding: 8px 12px;
            cursor: pointer;
            white-space: nowrap;
            font-family: 'Manrope', 'Public Sans', sans-serif;
            transition: background 0.15s ease, color 0.15s ease, border-color 0.15s ease;
        }

        .capsule-day-chip.active {
            background: linear-gradient(180deg, #1f7b5e, #165e49);
            color: #f2fffa;
            border-color: #165e49;
        }

        .capsule-day-chip.today {
            min-width: 92px;
            height: 50px;
            padding: 6px 8px;
            border-radius: 12px;
            border-color: #7daea0;
            box-shadow: 0 0 0 2px rgba(31, 123, 94, 0.08);
            display: grid;
            align-content: center;
            justify-items: center;
            gap: 1px;
        }

        .capsule-day-chip.today .capsule-day-num {
            font-size: 34px;
            line-height: 1;
            font-weight: 800;
            letter-spacing: -0.02em;
            font-family: 'Manrope', 'Public Sans', sans-serif;
        }

        .capsule-day-chip.today .capsule-day-mon {
            font-size: 10px;
            line-height: 1.1;
            text-transform: uppercase;
            letter-spacing: 0.04em;
            opacity: 0.95;
        }

        .capsule-day-chip.today.active .capsule-day-num,
        .capsule-day-chip.today.active .capsule-day-mon {
            color: #f2fffa;
        }

        .capsule-day-note {
            margin: 8px 2px 0;
            color: #48655e;
            font-size: 13px;
            line-height: 1.4;
        }

        .news-list {
            display: flex;
            flex-direction: column;
            gap: 14px;
        }

        .news-section {
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 14px;
            background: var(--panel-strong);
        }

        .news-section__header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
            gap: 10px;
        }

        .news-articles {
            display: flex;
            flex-direction: column;
            gap: 10px;
        }

        .news-item {
            border: 1px solid var(--border);
            border-radius: 14px;
            padding: 12px;
            background: #fbfdfc;
        }

        .news-item__head {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            gap: 10px;
            margin-bottom: 8px;
        }

        .news-item__head h5 {
            margin: 0;
            font-size: 15px;
            line-height: 1.35;
        }

        .news-item__head p {
            margin: 4px 0 0;
            font-size: 12px;
            color: var(--muted);
        }

        .news-item__head a {
            color: var(--accent);
            font-weight: 700;
            text-decoration: none;
            font-size: 12px;
            white-space: nowrap;
        }

        .news-points {
            margin: 0 0 10px;
            padding-left: 18px;
            color: var(--ink);
            font-size: 13px;
            line-height: 1.45;
        }

        .news-meta {
            font-size: 12px;
            color: var(--muted);
            display: flex;
            flex-direction: column;
            gap: 4px;
        }

        @media (min-width: 720px) {
            .news-meta {
                flex-direction: row;
                justify-content: space-between;
            }
        }

        .news-empty {
            margin: 0;
            color: var(--muted);
            font-style: italic;
        }

        .news-link-disabled {
            font-size: 12px;
            color: var(--muted);
            font-weight: 700;
        }

        .card h3 {
            margin: 0 0 12px;
            font-family: 'Manrope', 'Public Sans', sans-serif;
            font-size: 22px;
            letter-spacing: -0.02em;
            color: #102d27;
        }

        .metric {
            font-size: 36px;
            line-height: 1.1;
            font-weight: 800;
            margin: 8px 0 6px;
            font-family: 'Manrope', 'Public Sans', sans-serif;
            color: #0e2a24;
        }

        #metricGrid {
            gap: 10px;
        }

        #metricGrid .card {
            border-radius: 16px;
            padding: 12px 14px;
            min-height: 128px;
            box-shadow: 0 14px 28px rgba(18, 49, 39, 0.1), inset 0 1px 0 rgba(255,255,255,0.82);
            display: flex;
            flex-direction: column;
            justify-content: flex-start;
        }

        #metricGrid .tag {
            font-size: 10px;
            padding: 4px 10px;
            width: fit-content;
        }

        #metricGrid .metric {
            font-size: clamp(28px, 1.9vw, 40px);
            margin: 4px 0 2px;
            line-height: 1.06;
        }

        #metricGrid .metric.metric--compact {
            font-size: clamp(20px, 1.3vw, 30px);
            line-height: 1.2;
        }

        #metricGrid p {
            margin: 0;
            font-size: 12px;
            line-height: 1.35;
        }

        #metricGrid .metric-hint {
            margin-top: 6px;
        }

        .metric.metric--compact {
            font-size: 24px;
            line-height: 1.22;
            word-break: break-word;
        }

        .metric-card--clickable {
            cursor: pointer;
            transition: transform 0.16s ease, box-shadow 0.16s ease, border-color 0.16s ease;
        }

        .metric-card--clickable:hover {
            transform: translateY(-2px);
            border-color: rgba(31, 123, 94, 0.55);
            box-shadow: 0 18px 32px rgba(22, 94, 73, 0.16), inset 0 1px 0 rgba(255,255,255,0.8);
        }

        .metric-hint {
            margin-top: 8px;
            font-size: 12px;
            color: #1b6a50;
            font-weight: 700;
        }

        .tag {
            display: inline-flex;
            padding: 5px 11px;
            border-radius: 999px;
            font-size: 11px;
            letter-spacing: 0.01em;
            background: rgba(31, 123, 94, 0.13);
            color: #176046;
            font-weight: 700;
        }

        .list {
            list-style: none;
            padding: 0;
            margin: 0;
            display: flex;
            flex-direction: column;
            gap: 12px;
        }

        .list li {
            display: flex;
            justify-content: space-between;
            gap: 12px;
            font-size: 15px;
            color: var(--muted);
            line-height: 1.4;
            border: 1px solid rgba(200, 215, 209, 0.75);
            border-radius: 12px;
            padding: 10px 12px;
            background: #fbfdfc;
        }

        .list li.activity-card {
            border-radius: 16px;
            padding: 14px;
            align-items: flex-start;
            gap: 14px;
            background: linear-gradient(180deg, #fcfffd 0%, #f4faf7 100%);
        }

        .activity-main {
            min-width: 0;
            flex: 1;
            display: flex;
            flex-direction: column;
            gap: 6px;
        }

        .activity-title {
            margin: 0;
            color: #2c4d45;
            font-size: 19px;
            line-height: 1.25;
            font-weight: 600;
            font-family: 'Manrope', 'Public Sans', sans-serif;
            letter-spacing: -0.02em;
        }

        .activity-detail {
            margin: 0;
            color: #5c746d;
            font-size: 13px;
            line-height: 1.5;
            word-break: break-word;
        }

        .activity-time {
            color: #4f6861;
            font-size: 14px;
            line-height: 1.35;
            font-weight: 600;
            white-space: nowrap;
            padding-top: 2px;
        }

        .list small {
            color: var(--muted);
            font-size: 12px;
        }

        #activityList {
            display: grid;
            grid-template-columns: 1fr;
            gap: 12px;
            max-height: 338px;
            overflow-y: auto;
            padding-right: 4px;
            scrollbar-width: thin;
            scrollbar-color: #96aca4 transparent;
            margin-top: 2px;
        }

        .todo-composer {
            display: grid;
            grid-template-columns: minmax(0, 1fr) auto;
            gap: 10px;
            margin-bottom: 12px;
        }

        .todo-input {
            width: 100%;
            min-height: 46px;
            border-radius: 14px;
            border: 1px solid var(--border);
            background: #f8fcfa;
            padding: 11px 14px;
            color: #24463f;
            font-size: 15px;
            font-family: 'Public Sans', 'Segoe UI', sans-serif;
        }

        .todo-input:focus {
            outline: none;
            border-color: var(--accent);
            box-shadow: 0 0 0 3px rgba(31, 123, 94, 0.15);
            background: #ffffff;
        }

        .todo-add {
            border: 1px solid #9ebcb1;
            border-radius: 14px;
            background: linear-gradient(180deg, #f4faf7, #e9f3ef);
            color: #175b44;
            font-weight: 700;
            padding: 10px 16px;
            min-height: 46px;
            cursor: pointer;
            font-family: 'Manrope', 'Public Sans', sans-serif;
            transition: transform 0.15s ease, box-shadow 0.15s ease, border-color 0.15s ease;
        }

        .todo-add:hover {
            transform: translateY(-1px);
            border-color: #85aa9d;
            box-shadow: 0 10px 18px rgba(24, 91, 69, 0.12);
        }

        .todo-list li {
            align-items: center;
            border-radius: 16px;
            padding: 14px;
            background: linear-gradient(180deg, #fcfffd 0%, #f5faf8 100%);
        }

        #focusList {
            max-height: 360px;
            overflow-y: auto;
            padding-right: 4px;
            scrollbar-width: thin;
            scrollbar-color: #96aca4 transparent;
            margin-top: 2px;
        }

        .todo-main {
            min-width: 0;
            display: flex;
            align-items: center;
            gap: 10px;
            flex: 1;
        }

        .todo-toggle {
            width: 22px;
            height: 22px;
            border-radius: 999px;
            border: 1px solid #abc0b8;
            background: #f3f8f6;
            color: transparent;
            cursor: pointer;
            font-size: 14px;
            line-height: 1;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            padding: 0;
        }

        .todo-toggle.is-done {
            background: linear-gradient(180deg, #23906a, #1a6d51);
            border-color: #1a6d51;
            color: #ffffff;
        }

        .todo-text {
            color: #2f4f48;
            font-size: 15px;
            line-height: 1.35;
            word-break: break-word;
        }

        .todo-text.is-done {
            text-decoration: line-through;
            color: #7d918a;
        }

        .todo-inline-edit {
            width: 100%;
            min-height: 36px;
            border-radius: 9px;
            border: 1px solid #aac1b8;
            background: #ffffff;
            color: #223f38;
            font-size: 14px;
            line-height: 1.3;
            padding: 7px 10px;
            font-family: 'Public Sans', 'Segoe UI', sans-serif;
        }

        .todo-inline-edit:focus {
            outline: none;
            border-color: var(--accent);
            box-shadow: 0 0 0 3px rgba(31, 123, 94, 0.14);
        }

        .todo-actions {
            display: inline-flex;
            align-items: center;
            gap: 6px;
        }

        .todo-action {
            border: 1px solid #bfd0c9;
            background: #f4f9f7;
            color: #35564d;
            border-radius: 8px;
            font-size: 12px;
            font-weight: 700;
            padding: 6px 9px;
            cursor: pointer;
            font-family: 'Manrope', 'Public Sans', sans-serif;
        }

        .todo-action.todo-delete {
            color: #8f2a1f;
            border-color: #e3c2bd;
            background: #fbf2f1;
        }

        .btn,
        a.btn {
            text-decoration: none;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            padding: 12px 16px;
            border-radius: 12px;
            background: linear-gradient(180deg, var(--accent), var(--accent-deep));
            color: white;
            font-weight: 700;
            margin-top: 14px;
            border: none;
            cursor: pointer;
            transition: transform 0.16s ease, box-shadow 0.16s ease, opacity 0.2s ease;
            box-shadow: 0 14px 24px rgba(22, 94, 73, 0.24);
            font-family: 'Manrope', 'Public Sans', sans-serif;
        }

        .btn:hover:not(:disabled),
        a.btn:hover:not(:disabled) {
            transform: translateY(-1px);
            box-shadow: 0 18px 28px rgba(22, 94, 73, 0.3);
        }

        .btn:disabled,
        a.btn:disabled {
            opacity: 0.7;
            cursor: not-allowed;
            box-shadow: none;
        }

        .focus-cta {
            width: fit-content;
            margin-top: 16px;
            padding-inline: 20px;
            min-height: 48px;
            border-radius: 14px;
            font-size: 17px;
            letter-spacing: -0.01em;
        }

        .card--daily {
            min-width: 0;
        }

        #status {
            width: 100%;
            margin: 0;
            text-align: center;
            color: var(--muted);
            padding: 10px clamp(10px, 1.8vw, 22px);
        }

        .card--capsules {
            padding: 22px;
        }

        .capsule-header {
            display: flex;
            flex-wrap: wrap;
            justify-content: space-between;
            gap: 12px;
            align-items: center;
        }

        .capsule-header h3 {
            margin: 4px 0;
        }

        .capsule-tabs {
            background: rgba(31, 123, 94, 0.08);
        }

        .capsule-wrapper {
            display: grid;
            grid-template-columns: minmax(230px, 320px) 1fr;
            gap: 18px;
        }

        .capsule-list {
            display: flex;
            flex-direction: column;
            gap: 10px;
            max-height: 520px;
            overflow-y: auto;
            padding-right: 4px;
        }

        .capsule-card {
            border: 1px solid var(--border);
            border-radius: 14px;
            padding: 12px;
            background: #f4f9f7;
            display: flex;
            flex-direction: column;
            gap: 5px;
            cursor: pointer;
            text-align: left;
            font: inherit;
            transition: border-color 0.2s ease, background 0.2s ease, box-shadow 0.2s ease;
        }

        .capsule-card strong {
            font-size: 15px;
        }

        .capsule-card small {
            color: var(--muted);
            font-size: 12px;
        }

        .capsule-card.active {
            border-color: #3f9b7b;
            background: #eaf5f1;
            box-shadow: 0 12px 24px rgba(21, 66, 52, 0.15);
        }

        .capsule-detail {
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 16px;
            background: #ffffff;
            display: flex;
            flex-direction: column;
            gap: 16px;
            min-height: 320px;
        }

        .capsule-detail__meta {
            display: flex;
            justify-content: space-between;
            gap: 12px;
            flex-wrap: wrap;
            align-items: center;
        }

        .capsule-detail__eyebrow {
            text-transform: uppercase;
            letter-spacing: 0.08em;
            font-size: 11px;
            color: var(--muted);
            margin: 0;
            font-weight: 700;
        }

        .capsule-detail__stats {
            display: flex;
            gap: 10px;
            font-size: 12px;
            color: var(--muted);
        }

        .capsule-detail__coverage {
            margin: 0;
            color: var(--muted);
            font-size: 13px;
        }

        .capsule-detail__sections {
            display: flex;
            flex-direction: column;
            gap: 12px;
        }

        .capsule-section {
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 12px;
            background: #f9fcfb;
        }

        .capsule-section h4 {
            margin: 0 0 8px;
            font-size: 16px;
        }

        .capsule-article {
            border: 1px solid rgba(31, 123, 94, 0.18);
            border-radius: 12px;
            padding: 11px;
            background: #fff;
            margin-bottom: 9px;
        }

        .capsule-article:last-child {
            margin-bottom: 0;
        }

        .capsule-article__head {
            display: flex;
            justify-content: space-between;
            gap: 8px;
            align-items: flex-start;
            margin-bottom: 8px;
        }

        .capsule-article__head h5 {
            margin: 0;
            font-size: 14px;
            line-height: 1.4;
        }

        .capsule-article__head a {
            font-size: 12px;
            color: var(--accent);
            text-decoration: none;
            font-weight: 700;
            white-space: nowrap;
        }

        .capsule-points {
            margin: 0 0 8px;
            padding-left: 18px;
            color: var(--ink);
            font-size: 13px;
            line-height: 1.45;
        }

        .capsule-meta-tags {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            font-size: 11px;
            color: var(--muted);
        }

        .capsule-meta-tags span {
            background: rgba(15, 23, 42, 0.05);
            padding: 4px 8px;
            border-radius: 999px;
        }

        .capsule-placeholder {
            margin: 0;
            color: var(--muted);
            font-style: italic;
        }

        .score-modal-backdrop {
            position: fixed;
            inset: 0;
            background: rgba(15, 23, 42, 0.45);
            display: none;
            align-items: center;
            justify-content: center;
            padding: 16px;
            z-index: 2000;
        }

        .score-modal-backdrop.show {
            display: flex;
        }

        .score-modal {
            width: min(760px, 100%);
            max-height: min(78vh, 640px);
            overflow: auto;
            background: var(--panel);
            border: 1px solid var(--border);
            border-radius: 16px;
            box-shadow: 0 24px 56px rgba(22, 42, 35, 0.28);
            padding: 18px;
        }

        .score-modal__head {
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 8px;
            margin-bottom: 12px;
        }

        .score-modal__head h3 {
            margin: 0;
            font-size: 22px;
        }

        .score-modal__close {
            border: 1px solid var(--border);
            background: #f6fbf9;
            color: #22453d;
            border-radius: 10px;
            padding: 8px 12px;
            font-weight: 700;
            cursor: pointer;
            font-family: 'Manrope', 'Public Sans', sans-serif;
        }

        .score-history-list {
            list-style: none;
            padding: 0;
            margin: 0;
            display: grid;
            gap: 10px;
        }

        .score-history-list li {
            border: 1px solid rgba(200, 215, 209, 0.8);
            border-radius: 12px;
            padding: 11px 12px;
            background: #fbfdfc;
            display: flex;
            justify-content: space-between;
            gap: 8px;
            flex-wrap: wrap;
        }

        .score-insight {
            border: 1px solid var(--border);
            border-radius: 16px;
            background: var(--panel);
            box-shadow: 0 18px 42px rgba(18, 42, 35, 0.12);
            padding: 18px;
            margin-top: 12px;
        }

        .score-insight.hidden {
            display: none;
        }

        .score-insight__head {
            display: flex;
            justify-content: space-between;
            gap: 10px;
            flex-wrap: wrap;
            align-items: center;
            margin-bottom: 12px;
        }

        .score-insight__head h3 {
            margin: 0;
            font-size: 22px;
        }

        .score-insight__actions {
            display: flex;
            gap: 8px;
            flex-wrap: wrap;
        }

        .score-trend {
            display: grid;
            gap: 8px;
            margin-bottom: 14px;
        }

        .score-trend-row {
            display: grid;
            grid-template-columns: 108px 1fr 60px;
            gap: 10px;
            align-items: center;
        }

        .score-trend-date {
            font-size: 12px;
            color: var(--muted);
            font-weight: 600;
        }

        .score-trend-track {
            height: 11px;
            background: rgba(18, 52, 43, 0.08);
            border: 1px solid rgba(170, 195, 186, 0.65);
            border-radius: 999px;
            overflow: hidden;
            position: relative;
        }

        .score-trend-fill {
            height: 100%;
            background: linear-gradient(90deg, #1f7b5e 0%, #34a184 100%);
            border-radius: 999px;
        }

        .score-trend-val {
            font-size: 12px;
            font-weight: 700;
            color: #17483d;
            text-align: right;
        }

        .score-attempt-list {
            list-style: none;
            margin: 0;
            padding: 0;
            display: grid;
            gap: 10px;
        }

        .score-attempt-list li {
            border: 1px solid rgba(200, 215, 209, 0.88);
            border-radius: 12px;
            background: #fbfdfc;
            padding: 12px;
            display: grid;
            gap: 8px;
        }

        .score-attempt-head {
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 8px;
            flex-wrap: wrap;
        }

        .score-attempt-sections {
            display: flex;
            flex-wrap: wrap;
            gap: 7px;
        }

        .score-chip {
            font-size: 11px;
            border-radius: 999px;
            padding: 4px 8px;
            border: 1px solid rgba(172, 196, 187, 0.7);
            background: #f2f8f5;
            color: #245046;
            font-weight: 600;
        }

        .score-history-wrapper {
            display: grid;
            grid-template-columns: minmax(220px, 300px) 1fr;
            gap: 14px;
            margin-top: 10px;
        }

        .score-history-list-panel {
            display: flex;
            flex-direction: column;
            gap: 8px;
            max-height: 480px;
            overflow-y: auto;
            padding-right: 4px;
        }

        .score-history-card {
            border: 1px solid var(--border);
            border-radius: 12px;
            background: #f4f9f7;
            padding: 10px 11px;
            text-align: left;
            cursor: pointer;
            display: grid;
            gap: 4px;
            font: inherit;
            transition: border-color 0.2s ease, background 0.2s ease, box-shadow 0.2s ease;
        }

        .score-history-card strong {
            font-size: 14px;
        }

        .score-history-card small {
            color: var(--muted);
            font-size: 12px;
        }

        .score-history-card.active {
            border-color: #3f9b7b;
            background: #eaf5f1;
            box-shadow: 0 10px 20px rgba(21, 66, 52, 0.14);
        }

        .score-history-detail-panel {
            border: 1px solid var(--border);
            border-radius: 14px;
            background: #ffffff;
            padding: 14px;
            min-height: 280px;
            display: grid;
            gap: 12px;
        }

        .score-history-meta {
            display: flex;
            justify-content: space-between;
            gap: 10px;
            flex-wrap: wrap;
            align-items: center;
        }

        .score-history-meta h4 {
            margin: 4px 0 0;
            font-size: 20px;
            font-family: 'Manrope', 'Public Sans', sans-serif;
            color: #183f35;
        }

        .score-section-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 10px;
        }

        .score-section-item {
            border: 1px solid var(--border);
            border-radius: 12px;
            background: #f9fcfb;
            padding: 10px;
            display: grid;
            gap: 6px;
        }

        .score-section-item p {
            margin: 0;
            font-size: 13px;
            color: var(--muted);
        }

        .score-progress {
            height: 8px;
            border-radius: 999px;
            border: 1px solid rgba(181, 203, 194, 0.72);
            background: rgba(31, 123, 94, 0.1);
            overflow: hidden;
        }

        .score-progress span {
            display: block;
            height: 100%;
            border-radius: 999px;
            background: linear-gradient(90deg, #1f7b5e 0%, #2f9a7a 100%);
        }

        .dashboard-footer {
            margin: 14px auto 24px;
            max-width: 1180px;
            border: 1px solid var(--border);
            border-radius: 20px;
            background: linear-gradient(180deg, rgba(248, 251, 250, 0.96) 0%, rgba(241, 247, 244, 0.92) 100%);
            box-shadow: 0 16px 36px rgba(18, 42, 35, 0.12), inset 0 1px 0 rgba(255,255,255,0.86);
            padding: 18px 20px;
            display: grid;
            grid-template-columns: 1.1fr 0.9fr;
            gap: 18px;
        }

        .footer-block {
            min-width: 0;
        }

        .footer-eyebrow {
            margin: 0 0 6px;
            display: inline-flex;
            align-items: center;
            padding: 4px 10px;
            border-radius: 999px;
            border: 1px solid #bfd1ca;
            background: #edf5f1;
            color: #2f5c51;
            font-size: 10px;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            font-weight: 800;
            font-family: 'Manrope', 'Public Sans', sans-serif;
        }

        .dashboard-footer h4 {
            margin: 0 0 8px;
            font-size: 22px;
            color: #173e35;
            font-family: 'Manrope', 'Public Sans', sans-serif;
            letter-spacing: -0.02em;
        }

        .dashboard-footer p {
            margin: 0;
            color: var(--muted);
            font-size: 15px;
            line-height: 1.55;
        }

        .dashboard-footer ul {
            margin: 0;
            padding-left: 0;
            list-style: none;
            color: var(--muted);
            font-size: 15px;
            line-height: 1.55;
            display: grid;
            gap: 6px;
        }

        .dashboard-footer li {
            position: relative;
            padding-left: 16px;
        }

        .dashboard-footer li::before {
            content: "";
            width: 6px;
            height: 6px;
            border-radius: 999px;
            background: #2d7b61;
            position: absolute;
            left: 0;
            top: 0.58em;
        }

        .dashboard-footer a {
            color: var(--accent);
            font-weight: 700;
            text-decoration: none;
        }

        .dashboard-footer a:hover {
            text-decoration: underline;
        }

        @media (max-width: 960px) {
            .capsule-wrapper {
                grid-template-columns: 1fr;
            }
            .score-history-wrapper {
                grid-template-columns: 1fr;
            }
            .dashboard-footer {
                grid-template-columns: 1fr;
                margin: 12px 14px 22px;
                padding: 16px;
                gap: 12px;
            }
            header {
                padding-top: 14px;
            }
            .card {
                padding: 16px;
            }
            .dashboard-triad .card {
                padding: 18px;
            }
            .dashboard-triad h3 {
                font-size: 38px;
            }
            .list li.activity-card {
                flex-direction: column;
            }
            .activity-time {
                white-space: normal;
                font-size: 13px;
            }
            .todo-composer {
                grid-template-columns: 1fr;
            }
            .todo-actions {
                flex-wrap: wrap;
            }
        }
    </style>
</head>
<body>
    <header>
        <div>
            <h1 id=\"welcomeTitle\">Dashboard</h1>
            <p id=\"welcomeSub\">Loading your workspace...</p>
        </div>
        <button class=\"logout\" id=\"logoutBtn\" type=\"button\">Log out</button>
    </header>

    <div id=\"status\">Authenticating session...</div>

    <main id=\"content\" style=\"display:none;\">
        <section class=\"grid\" id=\"metricGrid\"></section>
        <section class="score-insight hidden" id="scoreInsightSection">
            <div class="score-insight__head">
                <div>
                    <h3>Date-wise Test Analysis</h3>
                    <p style="margin:4px 0 0;color:var(--muted);">Track score trend and section performance for each attempt.</p>
                </div>
                <div class="score-insight__actions">
                    <button class="btn btn-subtle" id="downloadScoreHistoryBtn" type="button">Download CSV</button>
                    <button class="btn btn-subtle" id="closeScoreInsightBtn" type="button">Close</button>
                </div>
            </div>
            <div class="score-history-wrapper">
                <div class="score-history-list-panel" id="scoreHistoryDates"></div>
                <div class="score-history-detail-panel" id="scoreHistoryDetail"></div>
            </div>
        </section>
        <section class=\"grid dashboard-triad\">
            <article class=\"card card--focus\">
                <h3>Focus for this week</h3>
                <p class="section-subtitle">Plan your next high-impact tasks and execute them consistently.</p>
                <div class="todo-composer">
                    <input id="focusInput" class="todo-input" type="text" maxlength="140" placeholder="Add a task for this week..." />
                    <button id="focusAddBtn" class="todo-add" type="button">Add task</button>
                </div>
                <ul class=\"list todo-list\" id=\"focusList\"></ul>
                <a class=\"btn focus-cta\" href=\"/agents/planner/ui\">Open Planner Lab</a>
            </article>
            <article class=\"card card--activity\">
                <h3>Recent activity</h3>
                <p class="section-subtitle">Live timeline of your mocks, planner actions, and capsule usage.</p>
                <ul class=\"list\" id=\"activityList\"></ul>
            </article>
            <article class="card card--daily">
                <h3>Daily news capsule</h3>
                <p class="section-subtitle">Get curated UPSC-relevant headlines in your inbox every morning.</p>
                <div class="capsule-controls">
                    <span class="tag" id="capsuleBadge" style="background:rgba(31,123,94,0.2);color:#0f6449;">Active by default</span>
                    <button class="btn btn-subtle" id="pauseCapsuleBtn" type="button" disabled>Pause delivery</button>
                </div>
                <p class="news-status" id="subscribeStatus" aria-live="polite"></p>
                <div class="daily-quote" id="dailyQuoteWrap">
                    <p class="daily-quote__label">Today's motivation</p>
                    <p class="daily-quote__text" id="dailyQuoteText">Loading daily quote...</p>
                    <div class="capsule-calendar-line" id="capsuleCalendarLine" aria-label="Motivation calendar"></div>
                    <p class="capsule-day-note" id="capsuleCalendarNote">Pick a day to view note.</p>
                </div>
            </article>
        </section>
        <section class="card card--capsules" id="capsuleBoard">
            <div class="capsule-header">
                <div>
                    <p class="capsule-detail__eyebrow">News capsules</p>
                    <h3>Browse daily, weekly, and monthly briefs</h3>
                    <p style="margin:4px 0 0;color:var(--muted);">Tap a window, pick any day, and read the curated capsule.</p>
                </div>
                <div class="chip-group capsule-tabs">
                    <button class="chip active" type="button" data-capsule-range="daily">Daily</button>
                    <button class="chip" type="button" data-capsule-range="weekly">Weekly</button>
                    <button class="chip" type="button" data-capsule-range="monthly">Monthly</button>
                </div>
            </div>
            <div class="capsule-wrapper">
                <div class="capsule-list" id="capsuleList">
                    <p class="capsule-placeholder">Choose a window above to load capsules.</p>
                </div>
                <div class="capsule-detail" id="capsuleDetail">
                    <p class="capsule-placeholder">Select a capsule to read its summary.</p>
                </div>
            </div>
            <p class="news-status" id="capsuleStatus" aria-live="polite">Waiting for selection...</p>
        </section>
    </main>

    <footer class="dashboard-footer">
        <div class="footer-block">
            <p class="footer-eyebrow">Platform</p>
            <h4>About CivicBriefs.AI</h4>
            <p>
                CivicBriefs.AI provides structured UPSC preparation support with mock-test analytics,
                personalized plans, and daily capsule insights. Use this dashboard to track progress and
                improve section-wise performance.
            </p>
        </div>
        <div class="footer-block">
            <p class="footer-eyebrow">Support</p>
            <h4>Need Help?</h4>
            <ul>
                <li>Technical issue or bug: <a href="mailto:admin@civicbriefs.ai">admin@civicbriefs.ai</a></li>
                <li>Account/subscription support: <a href="mailto:support@civicbriefs.ai">support@civicbriefs.ai</a></li>
                <li>Please include your registered email and a short issue description for faster resolution.</li>
            </ul>
        </div>
    </footer>

    <div class="score-modal-backdrop" id="scoreHistoryModal" aria-hidden="true">
        <div class="score-modal">
            <div class="score-modal__head">
                <h3>Test score history</h3>
                <button class="score-modal__close" id="scoreHistoryClose" type="button">Close</button>
            </div>
            <ul class="score-history-list" id="scoreHistoryList"></ul>
        </div>
    </div>

    <script>
    (function () {
        const statusEl = document.getElementById('status');
        const contentEl = document.getElementById('content');
        const logoutBtn = document.getElementById('logoutBtn');
        const metricGrid = document.getElementById('metricGrid');
        const focusList = document.getElementById('focusList');
        const activityList = document.getElementById('activityList');
        const focusInput = document.getElementById('focusInput');
        const focusAddBtn = document.getElementById('focusAddBtn');
        const welcomeTitle = document.getElementById('welcomeTitle');
        const welcomeSub = document.getElementById('welcomeSub');
        const capsuleBadge = document.getElementById('capsuleBadge');
        const pauseCapsuleBtn = document.getElementById('pauseCapsuleBtn');
        const subscribeStatus = document.getElementById('subscribeStatus');
        const dailyQuoteText = document.getElementById('dailyQuoteText');
        const capsuleCalendarLine = document.getElementById('capsuleCalendarLine');
        const capsuleCalendarNote = document.getElementById('capsuleCalendarNote');
        const capsuleTabs = document.querySelectorAll('[data-capsule-range]');
        const capsuleList = document.getElementById('capsuleList');
        const capsuleDetail = document.getElementById('capsuleDetail');
        const capsuleStatus = document.getElementById('capsuleStatus');
        const scoreHistoryModal = document.getElementById('scoreHistoryModal');
        const scoreHistoryClose = document.getElementById('scoreHistoryClose');
        const scoreHistoryList = document.getElementById('scoreHistoryList');
        const scoreInsightSection = document.getElementById('scoreInsightSection');
        const scoreHistoryDates = document.getElementById('scoreHistoryDates');
        const scoreHistoryDetail = document.getElementById('scoreHistoryDetail');
        const closeScoreInsightBtn = document.getElementById('closeScoreInsightBtn');
        const downloadScoreHistoryBtn = document.getElementById('downloadScoreHistoryBtn');

        const capsuleState = {
            activeRange: 'daily',
            capsules: [],
            selectedDate: null,
            initialized: false,
            isLoading: false,
        };
        const scoreInsightState = {
            selectedDate: null,
        };
        const dateFormatOptions = { day: 'numeric', month: 'short', year: 'numeric' };
        const motivationLines = [
            'Small daily wins compound into rank-defining results.',
            'Discipline today creates confidence on exam day.',
            'Clarity beats intensity. Focus on one strong session at a time.',
            'Your consistency is your competitive advantage.',
            'Strong revision turns effort into marks.',
            'Progress is built in focused hours, not rushed days.',
            'Treat each mock as a rehearsal for the final stage.',
            'Precision in basics creates speed in the paper.',
            'Stay steady. Deep work now pays back in prelims and mains.',
            'Every quality study block moves you closer to your target rank.',
        ];
        const capsuleQuoteLines = [
            'Consistency in small sessions builds extraordinary results.',
            'Focus on today. Momentum handles the rest.',
            'Every revised concept strengthens exam confidence.',
            'Clear notes and regular mocks create rank-ready clarity.',
            'Strong routines beat occasional intensity.',
            'Progress compounds when priorities stay simple.',
            'Preparation becomes power when tracked daily.',
            'One disciplined day is never a small thing.',
        ];

        let currentUser = null;
        let focusTodos = [];
        let editingTodoId = null;
        let capsulePrefs = { subscribed: false, paused: false };
        let scoreHistory = [];
        let latestReadStats = { total_read: 0, current_streak: 0, longest_streak: 0, last_read_on: null };
        const readMarkedDates = new Set();

        const token = localStorage.getItem('cb_token');
        if (!token) {
            window.location.href = '/';
            return;
        }

        function clearSession() {
            localStorage.removeItem('cb_token');
            localStorage.removeItem('cb_user');
        }

        function activityStorageKey() {
            const userId = currentUser && currentUser.id ? currentUser.id : 'guest';
            return `cb_activity_log_${userId}`;
        }

        function loadLocalActivity() {
            try {
                const raw = localStorage.getItem(activityStorageKey());
                const parsed = raw ? JSON.parse(raw) : [];
                return Array.isArray(parsed) ? parsed : [];
            } catch (err) {
                return [];
            }
        }

        function saveLocalActivity(entries) {
            try {
                localStorage.setItem(activityStorageKey(), JSON.stringify(entries.slice(0, 40)));
            } catch (err) {
                // non-blocking
            }
        }

        function logLocalActivity(title, detail, dateValue) {
            const entries = loadLocalActivity();
            entries.unshift({
                title: String(title || 'Activity'),
                detail: String(detail || ''),
                date: dateValue || new Date().toISOString(),
            });
            saveLocalActivity(entries);
        }

        function performLogout() {
            const liveToken = localStorage.getItem('cb_token');
            clearSession();
            window.location.replace('/');

            if (!liveToken) {
                return;
            }
            fetch('/auth/logout', {
                method: 'POST',
                headers: { Authorization: `Bearer ${liveToken}` },
                keepalive: true,
            }).catch(() => {
                // session already cleared on client
            });
        }

        logoutBtn.addEventListener('click', (event) => {
            event.preventDefault();
            logoutBtn.disabled = true;
            performLogout();
        });

        async function renderMetrics(user) {
            let readStats = { total_read: 0, current_streak: 0, longest_streak: 0, last_read_on: null };
            let reminderStatus = { subscribed: true, paused: false };
            let history = [];
            try {
                const [readRes, historyRes, subscriptionRes] = await Promise.all([
                    fetch('/news/capsules/read/stats', { headers: { Authorization: `Bearer ${token}` } }),
                    fetch('/agents/planner/report/history?limit=20', { headers: { Authorization: `Bearer ${token}` } }),
                    fetch('/auth/subscription', { headers: { Authorization: `Bearer ${token}` } }),
                ]);

                if (readRes.ok) {
                    const readData = await readRes.json();
                    readStats = {
                        total_read: Number(readData.total_read || 0),
                        current_streak: Number(readData.current_streak || 0),
                        longest_streak: Number(readData.longest_streak || 0),
                        last_read_on: readData.last_read_on || null,
                    };
                }
                if (historyRes.ok) {
                    const historyData = await historyRes.json();
                    history = Array.isArray(historyData.history) ? historyData.history : [];
                }
                if (subscriptionRes.ok) {
                    const subData = await subscriptionRes.json();
                    reminderStatus = {
                        subscribed: Boolean(subData.subscribed),
                        paused: Boolean(subData.paused),
                    };
                }
            } catch (err) {
                // fall back to defaults when metrics APIs are unavailable
            }

            scoreHistory = history;
            latestReadStats = readStats;
            const latestScore = history.length && history[0] && history[0].overall_accuracy !== null
                ? `${history[0].overall_accuracy}%`
                : 'No tests';

            const nextReminder = reminderStatus.paused ? 'Delivery paused' : 'Next at 6:00 AM';
            const streakValue = `${readStats.current_streak || 0} day${(readStats.current_streak || 0) === 1 ? '' : 's'}`;
            const metrics = [
                { label: 'Capsules read', value: readStats.total_read || 0, trend: `${streakValue} reading streak` },
                { label: 'Test score', value: latestScore, trend: 'Click to view date-wise history', interactive: true },
                { label: 'Streak', value: streakValue, trend: `Best streak: ${readStats.longest_streak || 0} days` },
                { label: 'Reminder', value: reminderStatus.subscribed ? (reminderStatus.paused ? 'Paused' : 'Active') : 'Inactive', trend: nextReminder },
            ];
            metricGrid.innerHTML = '';
            metrics.forEach((metric) => {
                const card = document.createElement('article');
                card.className = 'card' + (metric.interactive ? ' metric-card--clickable' : '');
                const valueText = String(metric.value || '');
                const metricClass = valueText.length > 16 ? 'metric metric--compact' : 'metric';
                card.innerHTML = `<div class="tag">${metric.label}</div><div class="${metricClass}">${valueText}</div><p style="color:var(--muted);margin:0;">${metric.trend}</p>${metric.interactive ? '<p class="metric-hint">Open score history</p>' : ''}`;
                if (metric.interactive) {
                    card.addEventListener('click', openScoreInsightPanel);
                }
                metricGrid.appendChild(card);
            });
            renderActivityFromState();
        }

        function classifyAccuracy(value) {
            const score = Number(value || 0);
            if (score >= 75) return 'Strong';
            if (score >= 60) return 'Average';
            return 'Weak';
        }

        function renderScoreDateList() {
            if (!scoreHistoryDates) return;
            scoreHistoryDates.innerHTML = '';
            scoreHistory.forEach((entry) => {
                const isActive = scoreInsightState.selectedDate === entry.date;
                const btn = document.createElement('button');
                btn.type = 'button';
                btn.className = 'score-history-card' + (isActive ? ' active' : '');
                const dateText = escapeHtml(formatDateLabel(entry.date));
                const score = entry.overall_accuracy !== null && entry.overall_accuracy !== undefined
                    ? `${Number(entry.overall_accuracy).toFixed(2)}%`
                    : 'No score';
                const totalQuestions = entry.total_questions || 0;
                btn.innerHTML = `
                    <small>Attempt</small>
                    <strong>${dateText}</strong>
                    <small>${escapeHtml(score)} • ${escapeHtml(String(totalQuestions))} questions</small>
                `;
                btn.addEventListener('click', () => selectScoreHistoryDate(entry.date));
                scoreHistoryDates.appendChild(btn);
            });
        }

        function renderScoreHistoryDetail(entry) {
            if (!scoreHistoryDetail) return;
            if (!entry) {
                scoreHistoryDetail.innerHTML = '<p class="capsule-placeholder">Select an attempt to view details.</p>';
                return;
            }
            const dateText = escapeHtml(formatDateLabel(entry.date));
            const overall = entry.overall_accuracy !== null && entry.overall_accuracy !== undefined
                ? Number(entry.overall_accuracy).toFixed(2)
                : '0.00';
            const total = Number(entry.total_questions || 0);
            const correct = Number(entry.total_correct || 0);
            const wrong = Math.max(0, total - correct);
            const sections = Array.isArray(entry.sections) ? entry.sections : [];

            const sectionItems = sections.length
                ? sections.map((section) => {
                    const acc = Number(section.accuracy || 0);
                    const label = escapeHtml(section.label || section.slug || 'Section');
                    const badge = classifyAccuracy(acc);
                    return `
                        <article class="score-section-item">
                            <p><strong>${label}</strong> <span class="score-chip">${badge}</span></p>
                            <p>${acc.toFixed(2)}% • ${Number(section.correct || 0)}/${Number(section.total || 0)} correct</p>
                            <div class="score-progress"><span style="width:${Math.max(0, Math.min(100, acc))}%"></span></div>
                        </article>
                    `;
                }).join('')
                : '<p class="capsule-placeholder">No section data available for this attempt.</p>';

            scoreHistoryDetail.innerHTML = `
                <div class="score-history-meta">
                    <div>
                        <p class="capsule-detail__eyebrow">Test Attempt</p>
                        <h4>${dateText}</h4>
                    </div>
                    <span class="tag">Overall ${escapeHtml(overall)}%</span>
                </div>
                <p class="capsule-detail__coverage">Right: ${correct} • Wrong: ${wrong} • Total: ${total}</p>
                <div class="score-section-grid">${sectionItems}</div>
                <p class="capsule-detail__coverage">${escapeHtml(entry.feedback_summary || 'Keep consistency and review weak sections to improve your next attempt.')}</p>
            `;
        }

        function selectScoreHistoryDate(dateValue) {
            scoreInsightState.selectedDate = dateValue;
            renderScoreDateList();
            const selected = scoreHistory.find((item) => item.date === dateValue) || null;
            renderScoreHistoryDetail(selected);
        }

        function renderScoreInsightPanel() {
            if (!scoreInsightSection || !scoreHistoryDates || !scoreHistoryDetail) return;

            scoreHistoryDates.innerHTML = '';
            scoreHistoryDetail.innerHTML = '';

            if (!Array.isArray(scoreHistory) || !scoreHistory.length) {
                scoreHistoryDates.innerHTML = '<p class="capsule-placeholder">No attempts found yet.</p>';
                scoreHistoryDetail.innerHTML = '<p class="capsule-placeholder">Take a mock test to unlock date-wise analysis.</p>';
                return;
            }

            if (!scoreInsightState.selectedDate || !scoreHistory.some((item) => item.date === scoreInsightState.selectedDate)) {
                scoreInsightState.selectedDate = scoreHistory[0].date;
            }
            renderScoreDateList();
            const selected = scoreHistory.find((item) => item.date === scoreInsightState.selectedDate) || scoreHistory[0];
            renderScoreHistoryDetail(selected);
        }

        function openScoreInsightPanel() {
            if (!scoreInsightSection) return;
            renderScoreInsightPanel();
            scoreInsightSection.classList.remove('hidden');
            scoreInsightSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }

        function closeScoreInsightPanel() {
            if (!scoreInsightSection) return;
            scoreInsightSection.classList.add('hidden');
        }

        function downloadScoreHistoryCsv() {
            if (!Array.isArray(scoreHistory) || !scoreHistory.length) {
                return;
            }
            const lines = ['date,overall_accuracy,section,section_accuracy'];
            scoreHistory.forEach((entry) => {
                const dateText = (entry.date || '').toString().replace(/,/g, ' ');
                const overall = entry.overall_accuracy !== null && entry.overall_accuracy !== undefined
                    ? Number(entry.overall_accuracy).toFixed(2)
                    : '';
                const sections = Array.isArray(entry.sections) ? entry.sections : [];
                if (!sections.length) {
                    lines.push(`${dateText},${overall},,`);
                    return;
                }
                sections.forEach((section) => {
                    const name = String(section.label || section.slug || '').replace(/,/g, ' ');
                    const acc = section.accuracy !== null && section.accuracy !== undefined
                        ? Number(section.accuracy).toFixed(2)
                        : '';
                    lines.push(`${dateText},${overall},${name},${acc}`);
                });
            });

            const blob = new Blob([lines.join('\\n')], { type: 'text/csv;charset=utf-8;' });
            const url = URL.createObjectURL(blob);
            const anchor = document.createElement('a');
            anchor.href = url;
            anchor.download = 'civicbriefs-score-history.csv';
            document.body.appendChild(anchor);
            anchor.click();
            document.body.removeChild(anchor);
            URL.revokeObjectURL(url);
        }

        function openScoreHistoryModal() {
            if (!scoreHistoryModal || !scoreHistoryList) return;
            scoreHistoryList.innerHTML = '';
            if (!Array.isArray(scoreHistory) || !scoreHistory.length) {
                const li = document.createElement('li');
                li.innerHTML = '<span>No test history found yet.</span>';
                scoreHistoryList.appendChild(li);
            } else {
                scoreHistory.forEach((entry) => {
                    const li = document.createElement('li');
                    const dateText = formatDateLabel(entry.date);
                    const scoreText = entry.overall_accuracy !== null && entry.overall_accuracy !== undefined
                        ? `${entry.overall_accuracy}%`
                        : 'No score';
                    li.innerHTML = `<span>${escapeHtml(dateText)}</span><span><strong>${escapeHtml(scoreText)}</strong></span>`;
                    scoreHistoryList.appendChild(li);
                });
            }
            scoreHistoryModal.classList.add('show');
            scoreHistoryModal.setAttribute('aria-hidden', 'false');
        }

        function closeScoreHistoryModal() {
            if (!scoreHistoryModal) return;
            scoreHistoryModal.classList.remove('show');
            scoreHistoryModal.setAttribute('aria-hidden', 'true');
        }

        if (scoreHistoryClose) {
            scoreHistoryClose.addEventListener('click', closeScoreHistoryModal);
        }
        if (scoreHistoryModal) {
            scoreHistoryModal.addEventListener('click', (event) => {
                if (event.target === scoreHistoryModal) {
                    closeScoreHistoryModal();
                }
            });
        }
        if (closeScoreInsightBtn) {
            closeScoreInsightBtn.addEventListener('click', closeScoreInsightPanel);
        }
        if (downloadScoreHistoryBtn) {
            downloadScoreHistoryBtn.addEventListener('click', downloadScoreHistoryCsv);
        }

        function renderFocus(user) {
            const presets = [
                'Revise polity NCERT summary before 8 PM',
                'Attempt 15-question mock on modern history',
                'Summarise one Hindu editorial into your notes',
            ];
            const saved = loadFocusTodos(user);
            if (saved.length) {
                focusTodos = saved;
            } else {
                focusTodos = presets.map((text, index) => ({
                    id: `${Date.now()}-${index}`,
                    text,
                    done: false,
                }));
                saveFocusTodos(user);
            }
            renderFocusList();
        }

        function focusStorageKey() {
            const userId = currentUser && currentUser.id ? currentUser.id : 'guest';
            return `cb_focus_todos_${userId}`;
        }

        function loadFocusTodos(user) {
            try {
                const raw = localStorage.getItem(`cb_focus_todos_${(user && user.id) || 'guest'}`);
                if (!raw) return [];
                const parsed = JSON.parse(raw);
                if (!Array.isArray(parsed)) return [];
                return parsed
                    .filter((item) => item && typeof item.text === 'string')
                    .map((item, index) => ({
                        id: item.id || `${Date.now()}-${index}`,
                        text: item.text.trim(),
                        done: Boolean(item.done),
                    }))
                    .filter((item) => item.text.length > 0);
            } catch (err) {
                return [];
            }
        }

        function saveFocusTodos() {
            localStorage.setItem(focusStorageKey(), JSON.stringify(focusTodos));
        }

        function renderFocusList() {
            if (!focusList) return;
            focusList.innerHTML = '';
            if (!focusTodos.length) {
                const li = document.createElement('li');
                li.innerHTML = '<span style="color:var(--muted);">No tasks yet. Add your first focus item.</span>';
                focusList.appendChild(li);
                return;
            }
            focusTodos.forEach((todo) => {
                const li = document.createElement('li');
                const safeText = escapeHtml(todo.text);
                const doneClass = todo.done ? 'is-done' : '';
                const isEditing = editingTodoId === todo.id;
                const textHtml = isEditing
                    ? `<input class="todo-inline-edit" type="text" maxlength="140" data-edit-id="${todo.id}" value="${safeText}" />`
                    : `<span class="todo-text ${doneClass}">${safeText}</span>`;
                const actionsHtml = isEditing
                    ? `
                        <button class="todo-action" type="button" data-action="save" data-id="${todo.id}">Save</button>
                        <button class="todo-action" type="button" data-action="cancel" data-id="${todo.id}">Cancel</button>
                    `
                    : `
                        <button class="todo-action" type="button" data-action="edit" data-id="${todo.id}">Edit</button>
                        <button class="todo-action todo-delete" type="button" data-action="delete" data-id="${todo.id}">Delete</button>
                    `;
                li.innerHTML = `
                    <div class="todo-main">
                        <button class="todo-toggle ${doneClass}" type="button" data-action="toggle" data-id="${todo.id}" aria-label="Toggle task">${todo.done ? '&#10003;' : ''}</button>
                        ${textHtml}
                    </div>
                    <div class="todo-actions">
                        ${actionsHtml}
                    </div>
                `;
                focusList.appendChild(li);
            });
            if (editingTodoId) {
                const input = focusList.querySelector(`input[data-edit-id="${editingTodoId}"]`);
                if (input) {
                    input.focus();
                    input.setSelectionRange(input.value.length, input.value.length);
                }
            }
        }

        function addFocusTodo() {
            if (!focusInput) return;
            const text = focusInput.value.trim();
            if (!text) return;
            focusTodos.unshift({
                id: `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
                text,
                done: false,
            });
            focusInput.value = '';
            saveFocusTodos();
            renderFocusList();
            logLocalActivity('Focus task added', text);
            renderActivityFromState();
        }

        focusAddBtn.addEventListener('click', addFocusTodo);
        focusInput.addEventListener('keydown', (event) => {
            if (event.key === 'Enter') {
                event.preventDefault();
                addFocusTodo();
            }
        });

        focusList.addEventListener('click', (event) => {
            const target = event.target;
            if (!(target instanceof HTMLElement)) return;
            const action = target.dataset.action;
            const id = target.dataset.id;
            if (!action || !id) return;
            const idx = focusTodos.findIndex((item) => item.id === id);
            if (idx < 0) return;

            if (action === 'toggle') {
                if (editingTodoId) return;
                focusTodos[idx].done = !focusTodos[idx].done;
                const msg = focusTodos[idx].done ? 'marked as done' : 'marked as pending';
                logLocalActivity('Focus task updated', `${focusTodos[idx].text} (${msg})`);
            } else if (action === 'delete') {
                if (editingTodoId === id) {
                    editingTodoId = null;
                }
                logLocalActivity('Focus task removed', focusTodos[idx].text);
                focusTodos.splice(idx, 1);
            } else if (action === 'edit') {
                editingTodoId = id;
                renderFocusList();
                return;
            } else if (action === 'cancel') {
                editingTodoId = null;
                renderFocusList();
                return;
            } else if (action === 'save') {
                const input = focusList.querySelector(`input[data-edit-id="${id}"]`);
                const trimmed = input ? input.value.trim() : '';
                if (!trimmed) return;
                focusTodos[idx].text = trimmed;
                logLocalActivity('Focus task edited', trimmed);
                editingTodoId = null;
            }
            saveFocusTodos();
            renderFocusList();
            renderActivityFromState();
        });

        focusList.addEventListener('keydown', (event) => {
            const target = event.target;
            if (!(target instanceof HTMLInputElement)) return;
            const id = target.dataset.editId;
            if (!id) return;
            const idx = focusTodos.findIndex((item) => item.id === id);
            if (idx < 0) return;

            if (event.key === 'Enter') {
                event.preventDefault();
                const trimmed = target.value.trim();
                if (!trimmed) return;
                focusTodos[idx].text = trimmed;
                editingTodoId = null;
                saveFocusTodos();
                renderFocusList();
                logLocalActivity('Focus task edited', trimmed);
                renderActivityFromState();
            } else if (event.key === 'Escape') {
                event.preventDefault();
                editingTodoId = null;
                renderFocusList();
            }
        });

        function dayHash(dateKey) {
            let hash = 0;
            for (let i = 0; i < dateKey.length; i += 1) {
                hash = (hash * 31 + dateKey.charCodeAt(i)) % 2147483647;
            }
            return hash;
        }

        function getDailyMotivation() {
            const now = new Date();
            const dateKey = `${now.getFullYear()}-${now.getMonth() + 1}-${now.getDate()}`;
            const index = dayHash(dateKey) % motivationLines.length;
            return motivationLines[index];
        }

        function getDailyCapsuleQuote() {
            const now = new Date();
            const dateKey = `${now.getFullYear()}-${now.getMonth() + 1}-${now.getDate()}-capsule`;
            const index = dayHash(dateKey) % capsuleQuoteLines.length;
            return capsuleQuoteLines[index];
        }

        function getCapsuleQuoteByDate(dateObj) {
            const dateKey = `${dateObj.getFullYear()}-${dateObj.getMonth() + 1}-${dateObj.getDate()}-capsule`;
            const index = dayHash(dateKey) % capsuleQuoteLines.length;
            return capsuleQuoteLines[index];
        }

        function renderCapsuleCalendarLine() {
            if (!capsuleCalendarLine || !capsuleCalendarNote || !dailyQuoteText) return;
            capsuleCalendarLine.innerHTML = '';
            const now = new Date();
            const start = new Date(now);
            start.setDate(now.getDate() - 3);
            let activeKey = `${now.getFullYear()}-${now.getMonth()}-${now.getDate()}`;

            for (let i = 0; i < 7; i += 1) {
                const day = new Date(start);
                day.setDate(start.getDate() + i);
                const key = `${day.getFullYear()}-${day.getMonth()}-${day.getDate()}`;
                const label = day.toLocaleDateString(undefined, { day: '2-digit', month: 'short' });
                const isToday = key === `${now.getFullYear()}-${now.getMonth()}-${now.getDate()}`;
                const btn = document.createElement('button');
                btn.type = 'button';
                btn.className = 'capsule-day-chip' + (key === activeKey ? ' active' : '') + (isToday ? ' today' : '');
                if (isToday) {
                    const dayNum = day.toLocaleDateString(undefined, { day: '2-digit' });
                    const dayMon = day.toLocaleDateString(undefined, { month: 'short' });
                    btn.innerHTML = `<span class="capsule-day-num">${dayNum}</span><span class="capsule-day-mon">${dayMon}</span>`;
                } else {
                    btn.textContent = label;
                }
                btn.addEventListener('click', () => {
                    activeKey = key;
                    const quote = getCapsuleQuoteByDate(day);
                    dailyQuoteText.textContent = quote;
                    capsuleCalendarNote.textContent = `${label}: ${quote}`;
                    Array.from(capsuleCalendarLine.querySelectorAll('.capsule-day-chip')).forEach((chip) => {
                        chip.classList.remove('active');
                    });
                    btn.classList.add('active');
                });
                capsuleCalendarLine.appendChild(btn);
            }

            const todayLabel = now.toLocaleDateString(undefined, { day: '2-digit', month: 'short' });
            const todayQuote = getCapsuleQuoteByDate(now);
            dailyQuoteText.textContent = todayQuote;
            capsuleCalendarNote.textContent = `${todayLabel}: ${todayQuote}`;
        }

        function renderDailyQuote() {
            if (!dailyQuoteText) return;
            dailyQuoteText.textContent = getDailyCapsuleQuote();
            renderCapsuleCalendarLine();
        }

        function updateCapsuleControls() {
            if (!pauseCapsuleBtn) return;
            if (!capsulePrefs.subscribed) {
                if (capsuleBadge) {
                    capsuleBadge.textContent = 'Subscription unavailable';
                    capsuleBadge.style.background = 'rgba(220,38,38,0.12)';
                    capsuleBadge.style.color = '#b42318';
                }
                pauseCapsuleBtn.textContent = 'Pause delivery';
                pauseCapsuleBtn.disabled = true;
                if (subscribeStatus) {
                    subscribeStatus.style.color = '#b42318';
                    subscribeStatus.textContent = 'Subscription is unavailable for this account.';
                }
                return;
            }

            if (capsuleBadge) {
                capsuleBadge.textContent = 'Subscribed by default';
                capsuleBadge.style.background = 'rgba(31,123,94,0.2)';
                capsuleBadge.style.color = '#0f6449';
            }
            pauseCapsuleBtn.disabled = false;

            if (capsulePrefs.paused) {
                pauseCapsuleBtn.textContent = 'Resume delivery';
                if (subscribeStatus) {
                    subscribeStatus.style.color = '#9a3412';
                    subscribeStatus.textContent = 'Delivery is paused. Resume to receive daily capsules.';
                }
            } else {
                pauseCapsuleBtn.textContent = 'Pause delivery';
                if (subscribeStatus) {
                    subscribeStatus.style.color = '#047857';
                    subscribeStatus.textContent = 'Daily capsule subscription is active.';
                }
            }
        }

        async function refreshSubscriptionState() {
            try {
                const res = await fetch('/auth/subscription', {
                    headers: { Authorization: `Bearer ${token}` },
                });
                const data = await res.json();
                if (!res.ok) {
                    throw new Error(data.detail || 'Unable to read subscription state.');
                }
                capsulePrefs.subscribed = Boolean(data.subscribed);
                capsulePrefs.paused = Boolean(data.paused);
            } catch (err) {
                capsulePrefs.subscribed = false;
                capsulePrefs.paused = false;
                if (subscribeStatus) {
                    subscribeStatus.style.color = '#dc2626';
                    subscribeStatus.textContent = err.message || 'Unable to load subscription state.';
                }
            } finally {
                updateCapsuleControls();
            }
        }

        function formatScore(value) {
            const num = Number(value);
            if (!Number.isFinite(num)) {
                return null;
            }
            if (Math.abs(num - Math.round(num)) < 0.05) {
                return `${Math.round(num)}%`;
            }
            return `${num.toFixed(1)}%`;
        }

        function buildActivityDetail(report) {
            const parts = [];
            const sectionTexts = Array.isArray(report.sections)
                ? report.sections
                      .filter((section) => section && typeof section.label === 'string')
                      .slice(0, 2)
                      .map((section) => {
                          const sectionScore = formatScore(section.accuracy);
                          return sectionScore ? `${section.label}: ${sectionScore}` : section.label;
                      })
                : [];
            if (sectionTexts.length) {
                parts.push(sectionTexts.join(' | '));
            }
            const totalCorrect = Number(report.total_correct);
            const totalQuestions = Number(report.total_questions);
            if (Number.isFinite(totalCorrect) && Number.isFinite(totalQuestions) && totalQuestions > 0) {
                parts.push(`${totalCorrect}/${totalQuestions} correct`);
            }
            return parts.join(' • ') || 'Section-wise breakdown unavailable.';
        }

        function renderActivityPlaceholder(message) {
            if (!activityList) {
                return;
            }
            activityList.innerHTML = '';
            const li = document.createElement('li');
            li.className = 'activity-card';
            const main = document.createElement('div');
            main.className = 'activity-main';
            const label = document.createElement('p');
            label.className = 'activity-title';
            label.textContent = message;
            const detail = document.createElement('p');
            detail.className = 'activity-detail';
            detail.textContent = 'Your latest actions will appear here.';
            const timeTag = document.createElement('span');
            timeTag.className = 'activity-time';
            timeTag.textContent = '';
            main.appendChild(label);
            main.appendChild(detail);
            li.appendChild(main);
            li.appendChild(timeTag);
            activityList.appendChild(li);
        }

        function renderActivityEntries(entries) {
            if (!activityList) {
                return;
            }
            activityList.innerHTML = '';
            if (!Array.isArray(entries) || !entries.length) {
                renderActivityPlaceholder('No activity recorded yet. Start a mock or read a capsule.');
                return;
            }
            entries.slice(0, 8).forEach((item) => {
                const entry = document.createElement('li');
                entry.className = 'activity-card';
                const main = document.createElement('div');
                main.className = 'activity-main';
                const label = document.createElement('p');
                label.className = 'activity-title';
                const detail = document.createElement('p');
                detail.className = 'activity-detail';
                label.textContent = item.title || 'Activity';
                detail.textContent = item.detail || '';
                const timeTag = document.createElement('span');
                timeTag.className = 'activity-time';
                timeTag.textContent = formatActivityDate(item.date);
                main.appendChild(label);
                main.appendChild(detail);
                entry.appendChild(main);
                entry.appendChild(timeTag);
                activityList.appendChild(entry);
            });
        }

        function buildRecentActivityEntries() {
            const feed = [];

            if (Array.isArray(scoreHistory)) {
                scoreHistory.slice(0, 5).forEach((report) => {
                    const scoreText = formatScore(report.overall_accuracy);
                    feed.push({
                        title: scoreText ? `Mock result • ${scoreText}` : 'Mock result',
                        detail: buildActivityDetail(report),
                        date: report.date,
                    });
                    if (report.feedback_summary) {
                        feed.push({
                            title: 'Planner feedback',
                            detail: report.feedback_summary,
                            date: report.date,
                        });
                    }
                });
            }

            if (latestReadStats && latestReadStats.last_read_on) {
                feed.push({
                    title: 'News capsule activity',
                    detail: `Capsules read: ${latestReadStats.total_read || 0} • Current streak: ${latestReadStats.current_streak || 0} day(s)`,
                    date: latestReadStats.last_read_on,
                });
            }

            loadLocalActivity().forEach((item) => {
                feed.push({
                    title: item.title || 'Dashboard activity',
                    detail: item.detail || '',
                    date: item.date,
                });
            });

            feed.sort((a, b) => {
                const at = new Date(a.date || 0).getTime() || 0;
                const bt = new Date(b.date || 0).getTime() || 0;
                return bt - at;
            });
            return feed;
        }

        function renderActivityFromState() {
            renderActivityEntries(buildRecentActivityEntries());
        }

        function formatActivityDate(value) {
            if (!value) {
                return '—';
            }
            const parsed = new Date(value);
            if (Number.isNaN(parsed.getTime())) {
                return value;
            }
            const now = new Date();
            const diffMs = now.getTime() - parsed.getTime();
            if (diffMs < 0) {
                return parsed.toLocaleDateString(undefined, dateFormatOptions);
            }
            const diffMinutes = Math.floor(diffMs / 60000);
            if (diffMinutes < 1) {
                return 'just now';
            }
            if (diffMinutes < 60) {
                return `${diffMinutes} min${diffMinutes === 1 ? '' : 's'} ago`;
            }
            const diffHours = Math.floor(diffMinutes / 60);
            if (diffHours < 24) {
                return `${diffHours} hr${diffHours === 1 ? '' : 's'} ago`;
            }
            return parsed.toLocaleDateString(undefined, dateFormatOptions);
        }

        async function loadRecentActivity() {
            renderActivityFromState();
        }

        if (pauseCapsuleBtn) {
            pauseCapsuleBtn.addEventListener('click', async () => {
                if (!capsulePrefs.subscribed) {
                    return;
                }
                pauseCapsuleBtn.disabled = true;
                try {
                    const res = await fetch('/auth/subscription/pause', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            Authorization: `Bearer ${token}`,
                        },
                        body: JSON.stringify({ paused: !capsulePrefs.paused }),
                    });
                    const data = await res.json();
                    if (!res.ok) {
                        throw new Error(data.detail || 'Unable to update pause state.');
                    }
                    capsulePrefs.subscribed = Boolean(data.subscribed);
                    capsulePrefs.paused = Boolean(data.paused);
                    updateCapsuleControls();
                    logLocalActivity(
                        'Capsule reminder updated',
                        capsulePrefs.paused ? 'Daily capsule delivery paused.' : 'Daily capsule delivery resumed.'
                    );
                    renderActivityFromState();
                } catch (err) {
                    if (subscribeStatus) {
                        subscribeStatus.style.color = '#dc2626';
                        subscribeStatus.textContent = err.message || 'Unable to update delivery state.';
                    }
                } finally {
                    pauseCapsuleBtn.disabled = false;
                }
            });
        }

        capsuleTabs.forEach((tab) => {
            tab.addEventListener('click', () => {
                const range = tab.dataset.capsuleRange;
                if (!range || capsuleState.isLoading || capsuleState.activeRange === range) {
                    return;
                }
                setActiveCapsuleTab(range);
                fetchCapsules(range);
            });
        });

        function setActiveCapsuleTab(range) {
            capsuleState.activeRange = range;
            capsuleTabs.forEach((tab) => {
                tab.classList.toggle('active', tab.dataset.capsuleRange === range);
            });
        }

        function toggleCapsuleTabs(disabled) {
            capsuleTabs.forEach((tab) => {
                tab.disabled = disabled;
            });
        }

        function initializeCapsuleBoard() {
            if (capsuleState.initialized || !capsuleList || !capsuleStatus) {
                return;
            }
            capsuleState.initialized = true;
            setActiveCapsuleTab(capsuleState.activeRange);
            fetchCapsules(capsuleState.activeRange);
        }

        async function fetchCapsules(range) {
            if (!capsuleList || !capsuleDetail || !capsuleStatus) {
                return;
            }
            capsuleState.isLoading = true;
            toggleCapsuleTabs(true);
            capsuleState.capsules = [];
            capsuleState.selectedDate = null;
            capsuleList.innerHTML = `<p class="capsule-placeholder">Loading ${range} capsules...</p>`;
            capsuleDetail.innerHTML = '<p class="capsule-placeholder">Loading capsule details...</p>';
            capsuleStatus.textContent = 'Fetching capsules...';
            try {
                const res = await fetch(`/news/capsules?window=${range}`, {
                    headers: { Authorization: `Bearer ${token}` },
                });
                const data = await res.json();
                if (res.status === 401) {
                    clearSession();
                    window.location.href = '/';
                    return;
                }
                if (!res.ok) {
                    throw new Error(data.detail || 'Unable to fetch capsules.');
                }
                capsuleState.capsules = Array.isArray(data.capsules) ? data.capsules : [];
                if (!capsuleState.capsules.length) {
                    capsuleStatus.textContent = 'No capsules available for this window yet.';
                    capsuleList.innerHTML = '<p class="capsule-placeholder">Generate a capsule and check back soon.</p>';
                    capsuleDetail.innerHTML = '<p class="capsule-placeholder">No capsule selected.</p>';
                    return;
                }
                capsuleStatus.textContent = `Showing ${capsuleState.capsules.length} ${range} capsule${capsuleState.capsules.length > 1 ? 's' : ''} - ${formatWindowRange(data.window)}`;
                renderCapsuleList();
                selectCapsule(capsuleState.capsules[0].date);
            } catch (err) {
                capsuleStatus.textContent = err.message || 'Failed to load capsules.';
                capsuleList.innerHTML = '<p class="capsule-placeholder">Unable to load capsules right now.</p>';
                capsuleDetail.innerHTML = '<p class="capsule-placeholder">Try reloading in a moment.</p>';
            } finally {
                capsuleState.isLoading = false;
                toggleCapsuleTabs(false);
            }
        }

        function renderCapsuleList() {
            if (!capsuleList) {
                return;
            }
            capsuleList.innerHTML = '';
            capsuleState.capsules.forEach((capsule) => {
                const btn = document.createElement('button');
                btn.type = 'button';
                btn.className = 'capsule-card' + (capsuleState.selectedDate === capsule.date ? ' active' : '');
                const weekdayText = escapeHtml(capsule.weekday || '');
                const dateText = escapeHtml(formatDateLabel(capsule.date));
                const briefsText = escapeHtml(`${(capsule.totals && capsule.totals.articles) || 0} briefs`);
                const coverageText = escapeHtml(deriveCoverageLabel(capsule));
                btn.innerHTML = `
                    <small>${weekdayText}</small>
                    <strong>${dateText}</strong>
                    <small>${briefsText}</small>
                    <p style="margin:4px 0 0;">${coverageText}</p>
                `;
                btn.addEventListener('click', () => selectCapsule(capsule.date));
                capsuleList.appendChild(btn);
            });
        }

        function selectCapsule(date) {
            const capsule = capsuleState.capsules.find((item) => item.date === date);
            if (!capsule) {
                return;
            }
            capsuleState.selectedDate = date;
            renderCapsuleList();
            renderCapsuleDetail(capsule);
            markCapsuleRead(date);
        }

        async function markCapsuleRead(date) {
            if (!date || readMarkedDates.has(date)) {
                return;
            }
            readMarkedDates.add(date);
            try {
                await fetch('/news/capsules/read', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        Authorization: `Bearer ${token}`,
                    },
                    body: JSON.stringify({ date }),
                });
                if (currentUser) {
                    await renderMetrics(currentUser);
                }
                logLocalActivity('Capsule opened', `Read capsule for ${formatDateLabel(date)}`, date);
                renderActivityFromState();
            } catch (err) {
                // non-blocking metrics enrichment
            }
        }

        function renderCapsuleDetail(capsule) {
            if (!capsuleDetail) {
                return;
            }
            capsuleDetail.innerHTML = '';
            const header = document.createElement('div');
            header.className = 'capsule-detail__meta';
            const weekday = escapeHtml(capsule.weekday || '');
            const dateText = escapeHtml(formatDateLabel(capsule.date));
            const articleCount = escapeHtml(((capsule.totals && capsule.totals.articles) || 0).toString());
            const categoryCount = escapeHtml(((capsule.totals && capsule.totals.categories) || 0).toString());
            header.innerHTML = `
                <div>
                    <p class="capsule-detail__eyebrow">${weekday}</p>
                    <h4 style="margin:4px 0;">${dateText}</h4>
                </div>
                <div class="capsule-detail__stats">
                    <span>${articleCount} articles</span>
                    <span>${categoryCount} categories</span>
                </div>
            `;
            capsuleDetail.appendChild(header);

            const coverageLine = document.createElement('p');
            coverageLine.className = 'capsule-detail__coverage';
            coverageLine.textContent = deriveCoverageDetail(capsule);
            capsuleDetail.appendChild(coverageLine);

            const sectionGroup = document.createElement('div');
            sectionGroup.className = 'capsule-detail__sections';
            const sections = Array.isArray(capsule.sections) ? capsule.sections : [];
            if (!sections.length) {
                sectionGroup.innerHTML = '<p class="capsule-placeholder">No category breakdown yet.</p>';
            } else {
                sections.forEach((section) => {
                    const sectionEl = document.createElement('section');
                    sectionEl.className = 'capsule-section';
                    const label = escapeHtml(section.label || 'General');
                    const total = escapeHtml((section.total_articles || 0).toString());
                    sectionEl.innerHTML = `<h4>${label}<span style="color:var(--muted);font-weight:400;margin-left:8px;">${total} articles</span></h4>`;
                    const articles = Array.isArray(section.articles) ? section.articles : [];
                    if (!articles.length) {
                        const empty = document.createElement('p');
                        empty.className = 'capsule-placeholder';
                        empty.textContent = 'No articles available for this section.';
                        sectionEl.appendChild(empty);
                    } else {
                        articles.forEach((article) => {
                            sectionEl.appendChild(buildCapsuleArticle(article));
                        });
                    }
                    sectionGroup.appendChild(sectionEl);
                });
            }
            capsuleDetail.appendChild(sectionGroup);
        }

        function buildCapsuleArticle(article) {
            const wrapper = document.createElement('article');
            wrapper.className = 'capsule-article';
            const head = document.createElement('div');
            head.className = 'capsule-article__head';
            const textWrap = document.createElement('div');
            const sourceLabel = article.source || 'Unknown source';
            const safeTitle = escapeHtml(article.title || 'Untitled brief');
            const safeSource = escapeHtml(sourceLabel);
            textWrap.innerHTML = `<h5>${safeTitle}</h5><p style="margin:4px 0 0;color:var(--muted);">${safeSource}</p>`;
            head.appendChild(textWrap);
            if (article.url) {
                const link = document.createElement('a');
                link.href = article.url;
                link.target = '_blank';
                link.rel = 'noopener noreferrer';
                link.textContent = 'Open link';
                head.appendChild(link);
            } else {
                const span = document.createElement('span');
                span.className = 'news-link-disabled';
                span.textContent = 'No link available';
                head.appendChild(span);
            }
            wrapper.appendChild(head);

            wrapper.appendChild(buildBulletList(article.summary_points));

            const metaTags = document.createElement('div');
            metaTags.className = 'capsule-meta-tags';
            const pyqLabel = escapeHtml(firstValue(article.pyq_points));
            const syllabusLabel = escapeHtml(firstValue(article.syllabus_points));
            metaTags.innerHTML = `<span>PYQ: ${pyqLabel}</span><span>Syllabus: ${syllabusLabel}</span>`;
            wrapper.appendChild(metaTags);
            return wrapper;
        }

        function buildBulletList(points) {
            const list = document.createElement('ul');
            list.className = 'capsule-points';
            const safePoints = Array.isArray(points) ? points : [];
            if (!safePoints.length) {
                const li = document.createElement('li');
                li.textContent = 'Summary coming soon.';
                list.appendChild(li);
                return list;
            }
            safePoints.slice(0, 3).forEach((point) => {
                const li = document.createElement('li');
                li.textContent = point;
                list.appendChild(li);
            });
            if (safePoints.length > 3) {
                const more = document.createElement('li');
                more.textContent = `+${safePoints.length - 3} more points`;
                more.style.color = 'var(--muted)';
                list.appendChild(more);
            }
            return list;
        }

        function firstValue(items) {
            if (!Array.isArray(items) || !items.length) {
                return 'None';
            }
            return items[0];
        }

        function deriveCoverageLabel(capsule) {
            const coverage = capsule && capsule.totals && Array.isArray(capsule.totals.coverage)
                ? capsule.totals.coverage
                : [];
            if (!coverage.length) {
                return 'Coverage TBD';
            }
            return coverage.slice(0, 2).map((item) => item.category || 'General').join(' | ');
        }

        function deriveCoverageDetail(capsule) {
            const coverage = capsule && capsule.totals && Array.isArray(capsule.totals.coverage)
                ? capsule.totals.coverage
                : [];
            if (!coverage.length) {
                return 'Coverage snapshot not available yet.';
            }
            return coverage.slice(0, 3).map((item) => `${item.category} (${item.count})`).join(' | ');
        }

        const HTML_ESCAPE_ENTITIES = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#39;',
        };

        function escapeHtml(value) {
            if (value === undefined || value === null) {
                return '';
            }
            return String(value).replace(/[&<>"']/g, (char) => HTML_ESCAPE_ENTITIES[char] || char);
        }

        function formatDateLabel(value) {
            if (!value) {
                return '';
            }
            const parsed = new Date(value);
            if (Number.isNaN(parsed.getTime())) {
                return value;
            }
            return parsed.toLocaleDateString(undefined, dateFormatOptions);
        }

        function formatWindowRange(meta) {
            if (!meta || !meta.start || !meta.end) {
                return '';
            }
            const start = formatDateLabel(meta.start);
            const end = formatDateLabel(meta.end);
            return start === end ? start : `${start} - ${end}`;
        }

        async function hydrate() {
            try {
                const res = await fetch('/auth/session', {
                    headers: { Authorization: `Bearer ${token}` },
                });
                const data = await res.json();
                if (!res.ok) {
                    throw new Error(data.detail || 'Session invalid');
                }
                const user = data.user;
                currentUser = user;
                welcomeTitle.textContent = `Hi, ${user.name}`;
                welcomeSub.textContent = getDailyMotivation();
                await renderMetrics(user);
                renderFocus(user);
                loadRecentActivity();
                if (pauseCapsuleBtn) {
                    await refreshSubscriptionState();
                }
                renderDailyQuote();
                initializeCapsuleBoard();
                statusEl.style.display = 'none';
                contentEl.style.display = 'grid';
            } catch (err) {
                statusEl.textContent = 'Session expired. Please log in again.';
                clearSession();
                setTimeout(() => window.location.href = '/', 1500);
            }
        }

        hydrate();
    })();
    </script>
</body>
</html>
"""


def render_portal_page() -> str:
    return PORTAL_HTML


def render_dashboard_page() -> str:
    return DASHBOARD_HTML
