"""The phone tab bar shared by every page outside the home page (styles in site-nav.css).

It links to the same six places as the home page's own bar. `up` is the path back to the site root
("" for root pages, "../../" for player pages); `current` marks the section the page belongs to.
"""

NAV_V = "20261019-phone"

ITEMS = [
    ("home", "#now", "Home", '<path d="M3 11l9-7 9 7v9a1 1 0 0 1-1 1h-5v-6h-6v6H4a1 1 0 0 1-1-1z"/>'),
    ("trading", "#trading", "Trading", '<path d="M3 17l6-6 4 4 7-7"/><path d="M14 8h6v6"/>'),
    ("players", "#players", "Players", '<rect x="5" y="3" width="14" height="18" rx="3"/><circle cx="12" cy="10" r="3"/><path d="M8 17.5c1-2 2.4-3 4-3s3 1 4 3"/>'),
    ("planner", "#calendar", "Planner", '<rect x="3" y="5" width="18" height="16" rx="2"/><path d="M3 10h18M8 3v4M16 3v4"/>'),
    ("tools", "#tools", "Tools", '<rect x="5" y="3" width="14" height="18" rx="2"/><path d="M8.5 7h7M8.5 11.5h1M12 11.5h1M15.5 11.5h0M8.5 15.5h1M12 15.5h1M15.5 15.5h0"/>'),
    ("builders", "tools.html", "Builders", '<path d="M4 5h16v14H4zM4 10h16M9 10v9"/>'),
]


def nav_css(up):
    return f'<link rel="stylesheet" href="{up}site-nav.css?v={NAV_V}">'


def bottom_nav(up, current=None):
    links = "".join(
        f'<a href="{up}{href}"{" aria-current=\"page\"" if key == current else ""}>'
        f'<svg viewBox="0 0 24 24" aria-hidden="true">{icon}</svg><span>{label}</span></a>'
        for key, href, label, icon in ITEMS)
    return f'<nav class="ezz-bnav" aria-label="Ezzcoins sections">{links}</nav>'


if __name__ == "__main__":
    print(nav_css("./") + bottom_nav("./", "builders"))
