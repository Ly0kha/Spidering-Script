import argparse
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from collections import deque
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from tqdm import tqdm
import signal
import sys

console = Console()
visited = set()
all_internal_links = []
all_external_links = []
progress_bar = None

def accessi_logo():
    logo = """

     \_______/
 `.,-'\_____/`-.,'
  /`..'\ _ /`.,'\
 /  /`.,' `.,'\  \
/__/__/     \__\__\__
\  \  \     /  /  /
 \  \,'`._,'`./  /
  \,'`./___\,'`./
 ,'`-./_____\,-'`.
     /       \
     Ly0kha 
                      
    """
    console.print(logo, style="bold red")

def get_args():
    parser = argparse.ArgumentParser(description="web crawler for bug bounty recon")
    parser.add_argument("url", help="the target url", type=str)
    parser.add_argument("-d", "--depth", help="recon depth level", type=int, default=5)
    parser.add_argument("-b", "--breadth", help="use breadth-first search", action="store_true")
    parser.add_argument("-f", "--filter", help="filter out extensions like .jpg,.png,.pdf", type=str, default="")
    parser.add_argument("-t", "--timeout", help="timeout for http requests", type=int, default=10)
    parser.add_argument("-o", "--output", help="save recon results to html file", type=str, default=None)
    return parser.parse_args()

def fetch_page(url, timeout):
    try:
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()
        return response.content
    except requests.RequestException as e:
        if progress_bar is None:
            console.print(f"[bold red]error fetching {url}: {e}")
        return None

def extract_links(html, base_url, filter_exts):
    soup = BeautifulSoup(html, "html.parser")
    internal_links = set()
    external_links = set()

    for anchor in soup.find_all("a", href=True):
        href = anchor["href"]
        full_url = urljoin(base_url, href)
        if full_url.startswith("mailto:") or full_url.startswith("javascript:"):
            continue
        if any(full_url.endswith(ext) for ext in filter_exts):
            continue
        if urlparse(full_url).netloc == urlparse(base_url).netloc:
            internal_links.add(full_url)
        else:
            external_links.add(full_url)

    return internal_links, external_links

def display_results(url, internal_links, external_links):
    console.print(Panel(f"[bold cyan]recon results for {url}:", style="bold white"))
    table = Table(title="[bold green]internal links", show_lines=True)
    table.add_column("No.", justify="center")
    table.add_column("internal link", justify="left", style="green")
    for i, link in enumerate(internal_links, 1):
        table.add_row(str(i), link)
    console.print(table)

    if external_links:
        ext_table = Table(title="[bold red]external links", show_lines=True)
        ext_table.add_column("No.", justify="center")
        ext_table.add_column("external link", justify="left", style="red")
        for i, link in enumerate(external_links, 1):
            ext_table.add_row(str(i), link)
        console.print(ext_table)
    else:
        console.print("[bold yellow]no external links found.", style="bold yellow")

def save_results_to_html(output_file):
    spider_logo_url = "https://www.svgrepo.com/show/400766/spider.svg"
    html_content = f"""
    <html>
    <head>
        <title>Recon Results</title>
        <style>
            body {{
                font-family: "Courier New", Courier, monospace;
                background-color: #1e1e1e;  /* dark background */
                color: #dcdcdc;  /* soft white text */
            }}
            h1, h2 {{
                text-align: center;
                color: #c0c0c0;  /* light grey for headings */
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin: 20px 0;
                background-color: #2e2e2e;  /* slightly lighter dark grey for tables */
            }}
            th, td {{
                border: 1px solid #444;  /* dark grey borders */
                padding: 10px;
                text-align: left;
                font-family: "Courier New", Courier, monospace;
            }}
            th {{
                background-color: #3e3e3e;  /* darker grey for table headers */
                color: #dcdcdc;  /* soft white for table headers */
            }}
            td {{
                color: #f5f5f5;  /* soft white for table cells */
            }}
            a {{
                color: #5ac8fa;  /* soft blue for links */
                text-decoration: none;
            }}
            a:hover {{
                text-decoration: underline;
                color: #8fbcbb;  /* light hover effect on links */
            }}
            .spider-logo {{
                display: block;
                margin-left: auto;
                margin-right: auto;
                width: 150px;
            }}
            .internal-links td {{
                color: #b0e0e6;  /* light blue for internal links */
            }}
            .external-links td {{
                color: #f08080;  /* light red for external links */
            }}
        </style>
    </head>
    <body>
        <h1>Recon Results</h1>
        <img src="{spider_logo_url}" alt="Spider Logo" class="spider-logo" />
        <h2>Internal Links</h2>
        <table class="internal-links">
            <tr>
                <th>No.</th>
                <th>Internal Link</th>
            </tr>
    """
    
    for i, link in enumerate(all_internal_links, 1):
        html_content += f'<tr><td>{i}</td><td><a href="{link}">{link}</a></td></tr>'
    
    html_content += "</table>"

    html_content += """
        <h2>External Links</h2>
        <table class="external-links">
            <tr>
                <th>No.</th>
                <th>External Link</th>
            </tr>
    """
    
    for i, link in enumerate(all_external_links, 1):
        html_content += f'<tr><td>{i}</td><td><a href="{link}">{link}</a></td></tr>'
    
    html_content += """
        </table>
    </body>
    </html>
    """

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    console.print(f"Results saved to {output_file}")

def should_crawl(url, filter_exts):
    if url in visited:
        return False
    if any(url.endswith(ext) for ext in filter_exts):
        return False
    return True

def breadth_first_crawl(start_url, depth_limit, timeout, filter_exts):
    queue = deque([(start_url, 0)])
    while queue:
        url, depth = queue.popleft()
        if depth > depth_limit or url in visited:
            continue
        if progress_bar is None:
            console.print(f"[bold blue]crawling: {url} [depth: {depth}]")
        html = fetch_page(url, timeout)
        if not html:
            continue
        internal_links, external_links = extract_links(html, url, filter_exts)
        all_internal_links.extend(internal_links)
        all_external_links.extend(external_links)
        if progress_bar is None:
            display_results(url, internal_links, external_links)
        visited.add(url)
        for link in internal_links:
            if should_crawl(link, filter_exts):
                queue.append((link, depth + 1))
        if progress_bar is not None:
            progress_bar.update(1)

def depth_first_crawl(url, depth, depth_limit, timeout, filter_exts):
    if depth > depth_limit or url in visited:
        return
    if progress_bar is None:
        console.print(f"[bold blue]crawling: {url} [depth: {depth}]")
    html = fetch_page(url, timeout)
    if not html:
        return
    internal_links, external_links = extract_links(html, url, filter_exts)
    all_internal_links.extend(internal_links)
    all_external_links.extend(external_links)
    if progress_bar is None:
        display_results(url, internal_links, external_links)
    visited.add(url)
    for link in internal_links:
        if should_crawl(link, filter_exts):
            depth_first_crawl(link, depth + 1, depth_limit, timeout, filter_exts)
    if progress_bar is not None:
        progress_bar.update(1)

def handle_exit_signal(signal, frame):
    if args.output:
        console.print("\n[bold yellow]recon interrupted! saving results...")
        save_results_to_html(args.output)
    sys.exit(0)

def main():
    global args, progress_bar
    accessi_logo()
    args = get_args()
    filter_exts = args.filter.split(",") if args.filter else []
    console.print("[bold cyan]starting recon...", style="bold green")
    console.print(f"url: {args.url}")
    console.print(f"depth limit: {args.depth}")
    console.print(f"filter extensions: {filter_exts}")
    console.print(f"timeout: {args.timeout} seconds")
    
    if args.output:
        console.print(f"[bold magenta]saving to file: {args.output}")
        signal.signal(signal.SIGINT, handle_exit_signal)
        progress_bar = tqdm(total=100, desc="recon progress")

    if args.breadth:
        breadth_first_crawl(args.url, args.depth, args.timeout, filter_exts)
    else:
        depth_first_crawl(args.url, 0, args.depth, args.timeout, filter_exts)

    if progress_bar is not None:
        progress_bar.close()
    if args.output:
        save_results_to_html(args.output)

if __name__ == "__main__":
    main()
