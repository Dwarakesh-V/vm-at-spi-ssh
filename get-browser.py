from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp("http://localhost:9222")

    page = browser.contexts[0].pages[0]

    # Install mouse tracking
    page.evaluate("""
        () => {
            window.__mouse = {x: 0, y: 0};

            document.addEventListener('mousemove', e => {
                window.__mouse.x = e.clientX;
                window.__mouse.y = e.clientY;
            });
        }
    """)

    input("Move your mouse over an element and press Enter...")

    result = page.evaluate("""
        () => {
            const el = document.elementFromPoint(
                window.__mouse.x,
                window.__mouse.y
            );

            if (!el) return null;

            return {
                tag: el.tagName,
                text: el.innerText,
                textContent: el.textContent,
                id: el.id,
                className: el.className
            };
        }
    """)

    print(result)