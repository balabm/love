"""Playwright page checker for LOVE UI"""
import asyncio
import json
from playwright.async_api import async_playwright

PAGES = [
    ("chat", None, "Chat Stream"),
    ("swarm", None, "Swarm Panel"),
    ("mind", "wave", "Autonomy Wave"),
    ("mind", "supervisor", "Autonomy Supervisor"),
    ("mind", "sentinel", "Autonomy Sentinel"),
    ("mind", "orchestrator", "Autonomy Orchestrator"),
    ("mind", "intelligence", "Autonomy Intelligence"),
    ("evolution", "matrix", "Evolution Matrix"),
    ("evolution", "terminal", "Neural Terminal"),
    ("biometrics", "lifelog", "Pulse Lifelog"),
    ("biometrics", "focus", "Pulse Focus"),
    ("biometrics", "ritual", "Pulse Ritual"),
    ("biometrics", "homeostasis", "Pulse Homeostasis"),
    ("finance", None, "Finance Manager"),
    ("constellation", "map", "Cosmos Map"),
    ("constellation", "notifications", "Cosmos Notifications"),
    ("constellation", "integrations", "Cosmos Integrations"),
    ("settings", None, "Settings Manager"),
]

async def main():
    results = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1400, "height": 900})
        page = await context.new_page()

        console_errors = []
        def handle_console(msg):
            if msg.type == "error":
                console_errors.append((msg.type, msg.text))
        page.on("console", handle_console)

        page.on("pageerror", lambda err: console_errors.append(("pageerror", str(err))))

        # Navigate to main app
        print("Loading http://localhost:5173 ...")
        await page.goto("http://localhost:5173", wait_until="domcontentloaded")
        await page.wait_for_timeout(2000)

        # Check backend health
        health_ok = False
        try:
            health = await page.evaluate("async () => { const r=await fetch('http://localhost:8000/health'); return r.ok }")
            health_ok = health
            print(f"Backend health: {'OK' if health_ok else 'FAIL'}")
        except Exception as e:
            print(f"Backend health check error: {e}")

        # Main pages
        for view, sub, label in PAGES:
            print(f"Checking {label} ...")
            errors_before = len(console_errors)

            # Click main nav tab
            btn = page.locator(f'button.nav-tab-btn:has-text("{view_to_tab_label(view)}")')
            try:
                await btn.click(timeout=3000)
            except Exception as e:
                print(f"  WARN: could not click nav for {label}: {e}")

            await page.wait_for_timeout(800)

            # Click sub-nav if present
            if sub:
                sub_btn = page.locator(f'button.sub-nav-btn:has-text("{sub_to_tab_label(sub)}")')
                try:
                    await sub_btn.first.click(timeout=3000)
                except Exception as e:
                    print(f"  WARN: could not click sub-nav for {label}: {e}")
                await page.wait_for_timeout(800)

            # Take screenshot
            safe_label = label.replace(" ", "_").replace("/", "_")
            screenshot_path = f"C:/Users/balab/OneDrive/Documents/Projects/LLove/love/screenshots/{safe_label}.png"
            await page.screenshot(path=screenshot_path, full_page=False)

            new_errors = console_errors[errors_before:]
            status = "OK" if not new_errors else "ERRORS"
            results.append({"page": label, "view": view, "sub": sub, "status": status, "errors": new_errors})
            print(f"  -> {status} ({len(new_errors)} errors)")

        # Static evolution dashboard
        print("Checking static evolution dashboard ...")
        errors_before = len(console_errors)
        await page.goto("http://localhost:8000/static/evolution_dashboard.html", wait_until="domcontentloaded")
        await page.wait_for_timeout(1500)
        await page.screenshot(path="C:/Users/balab/OneDrive/Documents/Projects/LLove/love/screenshots/Static_Evolution_Dashboard.png", full_page=False)
        new_errors = console_errors[errors_before:]
        status = "OK" if not new_errors else "ERRORS"
        results.append({"page": "Static Evolution Dashboard", "view": "static", "sub": None, "status": status, "errors": new_errors})
        print(f"  -> {status} ({len(new_errors)} errors)")

        await browser.close()

    # Save report
    report_path = "C:/Users/balab/OneDrive/Documents/Projects/LLove/love/page_check_report.json"
    with open(report_path, "w") as f:
        json.dump(results, f, indent=2)

    # Print summary
    print("\n=== SUMMARY ===")
    ok = [r for r in results if r["status"] == "OK"]
    bad = [r for r in results if r["status"] == "ERRORS"]
    print(f"OK: {len(ok)} / {len(results)}")
    for r in bad:
        print(f"FAIL: {r['page']}")
        for err in r['errors'][:5]:
            print(f"  {err[0]}: {err[1][:200]}")
    print(f"\nReport saved to {report_path}")


def view_to_tab_label(view):
    mapping = {
        "chat": "STREAM",
        "swarm": "SWARM",
        "mind": "AUTONOMY",
        "evolution": "EVOLUTION",
        "biometrics": "Pulse",
        "finance": "FINANCE",
        "constellation": "COSMOS",
        "settings": "SETTINGS",
    }
    return mapping.get(view, view.upper())


def sub_to_tab_label(sub):
    mapping = {
        "wave": "WAVE",
        "supervisor": "SUPERVISOR",
        "sentinel": "SENTINEL",
        "orchestrator": "ORCHESTRATOR",
        "intelligence": "INTELLIGENCE",
        "matrix": "MATRIX",
        "terminal": "TERMINAL",
        "lifelog": "DOMAINS",
        "focus": "FOCUS",
        "ritual": "RITUAL",
        "homeostasis": "HOMEOSTASIS",
        "map": "MAP",
        "notifications": "NOTIFICATION",
        "integrations": "INTEGRATIONS",
    }
    return mapping.get(sub, sub.upper())


if __name__ == "__main__":
    import os
    os.makedirs("C:/Users/balab/OneDrive/Documents/Projects/LLove/love/screenshots", exist_ok=True)
    asyncio.run(main())
