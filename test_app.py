#!/usr/bin/env python3
"""
Headless browser tests for WhisperBatch web app.
Uses Playwright (Chromium) to verify the app loads and works correctly.

Usage:
    python test_app.py

Starts a local HTTP server, runs tests in headless Chromium, then exits.
"""

import subprocess
import sys
import time
import socket

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def find_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        return s.getsockname()[1]


def start_server(port, directory):
    """Start python http.server in background, return Popen handle."""
    proc = subprocess.Popen(
        [sys.executable, "-m", "http.server", str(port), "--directory", directory],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    # Wait for server to be ready
    for _ in range(30):
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.5):
                return proc
        except OSError:
            time.sleep(0.1)
    proc.kill()
    raise RuntimeError("HTTP server did not start")


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

PASSED = 0
FAILED = 0
ERRORS = []


def test(name):
    """Decorator that runs a test function and tracks pass/fail."""
    def decorator(fn):
        def wrapper(*args, **kwargs):
            global PASSED, FAILED
            try:
                fn(*args, **kwargs)
                PASSED += 1
                print(f"  PASS  {name}")
            except Exception as e:
                FAILED += 1
                ERRORS.append((name, str(e)))
                print(f"  FAIL  {name}: {e}")
        return wrapper
    return decorator


def run_tests():
    global PASSED, FAILED, ERRORS

    import os
    from playwright.sync_api import sync_playwright

    port = find_free_port()
    app_dir = os.path.dirname(os.path.abspath(__file__))
    base_url = f"http://127.0.0.1:{port}"

    print(f"Starting server on port {port}...")
    server = start_server(port, app_dir)

    try:
        with sync_playwright() as p:
            # Use Chromium — supports Web Workers, Service Workers, SharedArrayBuffer
            browser = p.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()

            # Collect console messages for debugging
            console_msgs = []
            page.on("console", lambda msg: console_msgs.append(f"[{msg.type}] {msg.text}"))

            # Collect page errors
            page_errors = []
            page.on("pageerror", lambda err: page_errors.append(str(err)))

            # ------------------------------------------------------------------
            # TEST: Page loads without errors
            # ------------------------------------------------------------------
            @test("Page loads successfully")
            def _():
                response = page.goto(base_url, wait_until="networkidle", timeout=15000)
                assert response.status == 200, f"HTTP {response.status}"

            _()

            # Service worker may trigger a reload — wait for it
            time.sleep(2)

            # After potential SW reload, navigate again to get the isolated page
            @test("Page loads with cross-origin isolation (after SW reload)")
            def _():
                page.goto(base_url, wait_until="networkidle", timeout=15000)
                # Give SW time to intercept
                time.sleep(1)
                isolated = page.evaluate("window.crossOriginIsolated")
                assert isolated, "crossOriginIsolated is false — service worker not working"

            _()

            # ------------------------------------------------------------------
            # TEST: SharedArrayBuffer available
            # ------------------------------------------------------------------
            @test("SharedArrayBuffer is available")
            def _():
                has_sab = page.evaluate("typeof SharedArrayBuffer !== 'undefined'")
                assert has_sab, "SharedArrayBuffer not available"

            _()

            # ------------------------------------------------------------------
            # TEST: Key UI elements exist
            # ------------------------------------------------------------------
            @test("Title is WhisperBatch")
            def _():
                title = page.title()
                assert "WhisperBatch" in title, f"Title was: {title}"

            _()

            @test("Model selector exists with options")
            def _():
                options = page.locator("#modelSelect option").count()
                assert options >= 5, f"Only {options} model options"

            _()

            @test("Transcribe button exists and is disabled (no file selected)")
            def _():
                btn = page.locator("#transcribeBtn")
                assert btn.is_visible(), "Transcribe button not visible"
                assert btn.is_disabled(), "Transcribe button should be disabled without file"

            _()

            @test("Stop button exists and is hidden")
            def _():
                btn = page.locator("#stopBtn")
                # display:none means not visible
                assert not btn.is_visible(), "Stop button should be hidden initially"

            _()

            @test("Drop zone exists")
            def _():
                dz = page.locator("#dropZone")
                assert dz.is_visible(), "Drop zone not visible"

            _()

            @test("Error banner is NOT shown (system checks passed)")
            def _():
                banner = page.locator("#errorBanner")
                assert not banner.is_visible(), "Error banner is showing — multi-threading check failed"

            _()

            # ------------------------------------------------------------------
            # TEST: Backend info shows cores
            # ------------------------------------------------------------------
            @test("Backend info shows core count")
            def _():
                info = page.locator("#backendInfo").inner_text()
                assert "core" in info.lower(), f"Backend info doesn't mention cores: {info}"

            _()

            # ------------------------------------------------------------------
            # TEST: Web Worker can be created
            # ------------------------------------------------------------------
            @test("Web Worker (worker.js) loads without error")
            def _():
                result = page.evaluate("""
                    () => new Promise((resolve, reject) => {
                        const w = new Worker('./worker.js', { type: 'module' });
                        const timeout = setTimeout(() => {
                            w.terminate();
                            reject(new Error('Worker timed out'));
                        }, 10000);
                        w.addEventListener('message', (e) => {
                            if (e.data.type === 'capabilities') {
                                clearTimeout(timeout);
                                w.terminate();
                                resolve(e.data);
                            }
                        });
                        w.addEventListener('error', (e) => {
                            clearTimeout(timeout);
                            w.terminate();
                            reject(new Error('Worker error: ' + e.message));
                        });
                    })
                """)
                assert "cores" in result, f"Worker didn't report capabilities: {result}"
                assert result["cores"] >= 1, "Worker reported 0 cores"
                print(f"         Worker reports: {result['cores']} cores, webgpu={result.get('webgpu', '?')}, crossOriginIsolated={result.get('crossOriginIsolated', '?')}")

            _()

            # ------------------------------------------------------------------
            # TEST: Service worker registered
            # ------------------------------------------------------------------
            @test("Service worker is registered")
            def _():
                sw_count = page.evaluate("""
                    async () => {
                        const regs = await navigator.serviceWorker.getRegistrations();
                        return regs.length;
                    }
                """)
                assert sw_count >= 1, f"No service workers registered (count={sw_count})"

            _()

            # ------------------------------------------------------------------
            # TEST: Transformers.js CDN reachable (just check import doesn't crash)
            # ------------------------------------------------------------------
            @test("Transformers.js CDN import works in worker")
            def _():
                # The worker already imported it if capabilities came back.
                # Double-check by looking at console for errors.
                import_errors = [m for m in console_msgs if "failed" in m.lower() and "import" in m.lower()]
                assert len(import_errors) == 0, f"Import errors: {import_errors}"

            _()

            # ------------------------------------------------------------------
            # TEST: No page errors
            # ------------------------------------------------------------------
            @test("No JavaScript errors on page")
            def _():
                if page_errors:
                    # Filter out known benign errors
                    real_errors = [e for e in page_errors if "favicon" not in e.lower()]
                    assert len(real_errors) == 0, f"JS errors: {real_errors}"

            _()

            # ------------------------------------------------------------------
            # Print console log for debugging
            # ------------------------------------------------------------------
            wb_msgs = [m for m in console_msgs if "WhisperBatch" in m]
            if wb_msgs:
                print("\n  Console log:")
                for m in wb_msgs:
                    print(f"    {m}")

            browser.close()

    finally:
        server.kill()
        server.wait()

    # Summary
    print(f"\n{'=' * 50}")
    total = PASSED + FAILED
    if FAILED == 0:
        print(f"All {total} tests passed.")
    else:
        print(f"{PASSED}/{total} passed, {FAILED} failed:")
        for name, err in ERRORS:
            print(f"  - {name}: {err}")

    return FAILED == 0


if __name__ == "__main__":
    ok = run_tests()
    sys.exit(0 if ok else 1)
