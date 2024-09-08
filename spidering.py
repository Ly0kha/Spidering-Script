import argparse
import requests
from bs4 import BeautifulSoup, Comment
from urllib.parse import urljoin, urlparse
from collections import deque
from rich.console import Console
from rich.table import Table
from tqdm import tqdm
import re
import signal
import sys

console = Console()
visited_urls = set()
all_emails = set()
all_internal_links = set()
all_external_links = set()
all_js_files = set()
all_comments = set()
progress_bar = None  # Define progress_bar globally

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
     Ly0kha @                     
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
        console.print(f"[bold red]Error fetching {url}: {e}")
        return None

def extract_links_and_content(html, base_url, filter_exts):
    soup = BeautifulSoup(html, "html.parser")
    
    internal_links = set()
    external_links = set()
    emails = set(re.findall(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", str(soup)))
    js_files = set(script['src'] for script in soup.find_all("script", src=True))
    comments = [comment for comment in soup.find_all(string=lambda text: isinstance(text, Comment))]

    for anchor in soup.find_all("a", href=True):
        href = anchor["href"]
        full_url = urljoin(base_url, href)
        
        # skip unwanted links
        if full_url.startswith("mailto:") or full_url.startswith("javascript:"):
            continue
        if any(full_url.endswith(ext) for ext in filter_exts):
            continue
        
        # classify links as internal or external
        if urlparse(full_url).netloc == urlparse(base_url).netloc:
            internal_links.add(full_url)  # internal links
        else:
            external_links.add(full_url)  # external links

    return internal_links, external_links, emails, js_files, comments

def save_results_to_html(output_file):
    html_content = f"""
    <html>
    <head>
        <title>Recon Results</title>
        <style>
            body {{
                font-family: "Courier New", Courier, monospace;
                background-color: #1e1e1e;
                color: #dcdcdc;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin: 20px 0;
                background-color: #2e2e2e;
            }}
            th, td {{
                border: 1px solid #444;
                padding: 10px;
                text-align: left;
            }}
            th {{
                background-color: #3e3e3e;
                color: #dcdcdc;
            }}
            td {{
                color: #f5f5f5;
            }}
        </style>
    </head>
    <body>
        <h1>Recon Results</h1>
        <h2>Internal Links</h2><table><tr><th>No.</th><th>Internal Link</th></tr>
    """
    
    for i, link in enumerate(all_internal_links, 1):
        html_content += f'<tr><td>{i}</td><td>{link}</td></tr>'
    
    html_content += "</table>"

    html_content += """
        <h2>External Links</h2><table><tr><th>No.</th><th>External Link</th></tr>
    """
    
    for i, link in enumerate(all_external_links, 1):
        html_content += f'<tr><td>{i}</td><td>{link}</td></tr>'
    
    html_content += "</table>"

    html_content += """
        <h2>Emails</h2><table><tr><th>No.</th><th>Email</th></tr>
    """
    
    for i, email in enumerate(all_emails, 1):
        html_content += f'<tr><td>{i}</td><td>{email}</td></tr>'
    
    html_content += "</table>"

    html_content += """
        <h2>JavaScript Files</h2><table><tr><th>No.</th><th>JS File</th></tr>
    """
    
    for i, js_file in enumerate(all_js_files, 1):
        html_content += f'<tr><td>{i}</td><td>{js_file}</td></tr>'
    
    html_content += "</table>"

    html_content += """
        <h2>HTML Comments</h2><table><tr><th>No.</th><th>Comment</th></tr>
    """
    
    for i, comment in enumerate(all_comments, 1):
        html_content += f'<tr><td>{i}</td><td>{comment}</td></tr>'
    
    html_content += "</table>"

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)

    console.print(f"Results saved to {output_file}")

def display_results_in_terminal():
    # display internal links
    table = Table(title="Internal Links")
    table.add_column("No.", justify="center")
    table.add_column("Internal Link", justify="left")
    for i, link in enumerate(all_internal_links, 1):
        table.add_row(str(i), link)
    console.print(table)

    # display external links
    table = Table(title="External Links")
    table.add_column("No.", justify="center")
    table.add_column("External Link", justify="left")
    for i, link in enumerate(all_external_links, 1):
        table.add_row(str(i), link)
    console.print(table)

    # display emails
    table = Table(title="Emails")
    table.add_column("No.", justify="center")
    table.add_column("Email", justify="left")
    for i, email in enumerate(all_emails, 1):
        table.add_row(str(i), email)
    console.print(table)

    # display js files
    table = Table(title="JavaScript Files")
    table.add_column("No.", justify="center")
    table.add_column("JS File", justify="left")
    for i, js_file in enumerate(all_js_files, 1):
        table.add_row(str(i), js_file)
    console.print(table)

    # display comments
    table = Table(title="HTML Comments")
    table.add_column("No.", justify="center")
    table.add_column("Comment", justify="left")
    for i, comment in enumerate(all_comments, 1):
        table.add_row(str(i), comment)
    console.print(table)

def crawl(url, depth_limit, timeout, filter_exts, args, breadth_first=True):
    global progress_bar  
    queue = deque([(url, 0)])
    if args.output:
        progress_bar = tqdm(total=depth_limit, desc="Crawling Progress")
    
    while queue:
        current_url, depth = queue.popleft()
        if depth > depth_limit or current_url in visited_urls:
            continue

        html = fetch_page(current_url, timeout)
        if not html:
            continue
        
        internal_links, external_links, emails, js_files, comments = extract_links_and_content(html, current_url, filter_exts)

        
        all_internal_links.update(internal_links)
        all_external_links.update(external_links)
        all_emails.update(emails)
        all_js_files.update(js_files)
        all_comments.update(comments)

        visited_urls.add(current_url)

        for link in internal_links:
            if link not in visited_urls:
                queue.append((link, depth + 1))

        if args.output and progress_bar:
            progress_bar.update(1)

    if args.output and progress_bar:
        progress_bar.close()

def main():
    global all_emails, all_internal_links, all_external_links, all_js_files, all_comments
    accessi_logo()
    args = get_args()
    filter_exts = args.filter.split(",") if args.filter else []
    
    signal.signal(signal.SIGINT, lambda sig, frame: sys.exit(0))

    console.print(f"Starting recon for {args.url} up to depth {args.depth}")
    
    if args.breadth:
        crawl(args.url, args.depth, args.timeout, filter_exts, args, breadth_first=True)
    else:
        crawl(args.url, args.depth, args.timeout, filter_exts, args, breadth_first=False)

    if args.output:
        save_results_to_html(args.output)
    else:
        display_results_in_terminal()

if __name__ == "__main__":
    main()
