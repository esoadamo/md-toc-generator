# MD TOC generator

$%TOC_BEGIN$

## Table of content

- [1 What is this?](#1-what-is-this?)
  - [1.1 What it does?](#11-what-it-does?)
  - [1.2 How does it find where to place the TOC?](#12-how-does-it-find-where-to-place-the-toc?)
  - [1.3 How to update the TOC after first generation?](#13-how-to-update-the-toc-after-first-generation?)
- [2 How to run?](#2-how-to-run?)
- [3 License?](#3-license?)
  $%TOC_END$

## 1 What is this?

This script allows for an easy generation of the table of content inside given markdown file.

### 1.1 What it does?

It parsed the markdown file, locates all headers and numbers them. Then, it generates the TOC (as seen in the beginning of this README).

### 1.2 How does it find where to place the TOC?

The script looks for `[TOC]` mark inside the file, which it then replaces with the TOC content.

### 1.3 How to update the TOC after first generation?

Just run the script again, the TOC will be updated automatically.

## 2 How to run?

```bash
$ ./md-toc-generator.py --help
> Usage: ./md-toc-generator.py file [TOC chapter name]
> The second parameter overrides default TOC_CHAPTER_NAME
```

## 3 License?

MIT.
