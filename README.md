# 🕸️ Spidering Script 🕸️
Spidering Script uses Recursive Link Traversal to crawl websites and extract a variety of information including internal links, external links, emails, JavaScript files, and HTML comments. The script offers deep or broad search capabilities, filters out unwanted files, and provides a clean HTML report with all results. It’s an easy and efficient tool for collecting valuable information from any website.
### Usage

#### Basic Crawl:
```bash
python spidering.py https://example.com --depth 3
```
## Options

```python spidering.py https://example.com```
### --depth: Set crawl depth (Default: 5).
```python spidering.py https://example.com --depth 3```

### --breadth: Enable breadth-first crawling.
```python spidering.py https://example.com --breadth```

###  --filter: Exclude file types (e.g., .jpg, .pdf).
```python spidering.py https://example.com --filter .jpg,.pdf```
### --timeout: Set request timeout (Default: 10s).
```python spidering.py https://example.com --timeout 15```
### --output: Save results to HTML.
```python spidering.py https://example.com --output results.html```

## Clone the repo:
```bash
git clone https://github.com/Ly0kha/spidering-Script.git
```
### requirements
```bash
pip install requests beautifulsoup4 rich tqdm
```
# Shoot straight, stay safe
