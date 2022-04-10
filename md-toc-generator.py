#!/usr/bin/env python3

"""
Numbers all chapters and rewrites file
Generates table of content by replacing every [TOC] occurrence inside the file
Subsequent updates of the generated TOC can be done by executing this script again

Usage: ./md-toc-generator.py file [TOC chapter name]

The second parameter overrides default TOC_CHAPTER_NAME
"""

import re
from sys import argv
from pathlib import Path
from typing import Optional, List, Dict, Iterable, TypeVar

T = TypeVar('T')

# The default name of the TOC chapter
TOC_CHAPTER_NAME = 'Table of content'
# Mark to be placed before generated TOC (for subsequent runs)
TOC_BEGIN = r'$%TOC_BEGIN$'
# Mark to be place after generated TOC (for subsequent runs)
TOC_END = r'$%TOC_END$'
# Text to replace with TOC
TOC_MARK = '[TOC]'
# Locates headers inside md file
RE_HEADER = re.compile(r'^(#+)\s+(.*)\s*$')
# Splits the number of chapter and the name of the chapter itself
RE_NUMBERED_HEADER_NAME = re.compile(r'^([.\d]+)\s+(.*)$')
# Finds TOC_MARK inside document
RE_TOC_INIT = re.compile(re.escape(TOC_MARK))
# Locates previously generated TOC
RE_TOC_FINISHED = re.compile(f"{re.escape(TOC_BEGIN)}(?:\n|.)*{re.escape(TOC_END)}", re.MULTILINE)

"""
Keys are the level of chapters, values are how many of the chapters of the level were already seen
"""
CHAPTER_INDEXES = Dict[int, int]


def skip_n(iterable: Iterable[T], n: int) -> Iterable[T]:
    """
    Skips first `n` elements of iterable from the beginning
    :param iterable: iterable to iterate
    :param n: how many elements to skip
    :return: iterable without first `n` elements
    """
    for i, x in enumerate(iterable):
        if i < n:
            continue
        yield x


def get_new_chapter_name(current_name, indexes: CHAPTER_INDEXES) -> str:
    """
    Recalculates the numbering of the chapter based on indexes
    :param current_name: then name of the chapter
    :param indexes: context
    :return: numbered chapter based on context
    """
    current_name = RE_NUMBERED_HEADER_NAME.sub(r"\2", current_name)
    return '.'.join([str(indexes[x]) for x in sorted(indexes.keys())]) + ' ' + current_name


def get_chapter_names(
        content_lines: List[str],
        start_line_index: int = 0,
        chapter_indexes: Optional[CHAPTER_INDEXES] = None,
        current_chapter_level: int = 0,
        min_toc_level: int = 2,
        new_content: Optional[List[str]] = None
            ) -> List[str]:
    """
    Retries chapter names from the lines of markdown file
    :param content_lines: lines to process
    :param start_line_index: first line to consider (default `0`)
    :param chapter_indexes: previous context (default `None`)
    :param current_chapter_level: currently processed level of chapter (default `0`)
    :param min_toc_level: minimal level of header to add to the TOC (default `2`)
    :param new_content: if passed, then new transformed lines are appended to this list
    and chapters are numbered (default `None`)
    :return: found chapter names in the content lines
    """

    output_new_content = new_content is not None
    chapter_indexes = chapter_indexes if chapter_indexes is not None else {min_toc_level: 0}
    current_chapter_level = max(min_toc_level, current_chapter_level)

    chapter_names: List[str] = []

    for i, line in enumerate(skip_n(content_lines, start_line_index)):
        for mach in RE_HEADER.finditer(line):
            level = len(mach.group(1))
            chapter_name = mach.group(2)

            if level < min_toc_level:
                continue

            if level < current_chapter_level:
                for key in filter(lambda x: x > level, list(chapter_indexes.keys())):
                    del chapter_indexes[key]
            elif level > current_chapter_level:
                if level - current_chapter_level > 1:
                    print(f'WARN: level ({level}) of chapter "{chapter_name}" '
                          f'is larger than expected ({current_chapter_level + 1})')
                while True:
                    key = max(chapter_indexes.keys())
                    if key >= level:
                        break
                    chapter_indexes[key + 1] = 0

            chapter_indexes[level] = chapter_indexes.get(level, 0) + 1
            new_chapter_name = get_new_chapter_name(chapter_name, chapter_indexes)
            print(new_chapter_name)

            if output_new_content:
                chapter_name = new_chapter_name
                new_content.append(f"{'#' * level} {chapter_name}")

            chapter_names.append(chapter_name)
            chapter_names.extend(get_chapter_names(
                content_lines=content_lines,
                start_line_index=start_line_index + i + 1,
                chapter_indexes=chapter_indexes,
                current_chapter_level=level,
                min_toc_level=min_toc_level,
                new_content=new_content
            ))
            break
        else:
            if output_new_content:
                new_content.append(line)
            continue
        break

    return chapter_names


def chapter_name_to_md_item(chapter_name: str) -> str:
    """
    Transform chapter name into a list item with link supported by GitHub syntax
    :param chapter_name: name of the chapter to transform
    :return: name of the chapter as correctly padded list item
    """
    chapter_level = next(RE_NUMBERED_HEADER_NAME.finditer(chapter_name)).group(1).count('.')
    chapter_link = chapter_name\
        .replace('.', '')\
        .replace('/', '') \
        .replace('#', '') \
        .replace('-', '') \
        .replace('&', '') \
        .replace(' ', '-')\
        .lower()
    return f"{'  ' * chapter_level}- [{chapter_name}](#{chapter_link})"


def generate_file_toc(file: Path, toc_chapter_name: Optional[str] = None) -> None:
    """
    Rewrites the file by numbering all chapters and generating TOC
    :param file: file to process
    :param toc_chapter_name: overrides default TOC_CHAPTER_NAME
    :return: `None`
    """
    if toc_chapter_name is None:
        toc_chapter_name = TOC_CHAPTER_NAME

    with file.open('r') as f:
        content = f.read()

    content = RE_TOC_FINISHED.sub(TOC_MARK, content)

    content_lines = content.split('\n')

    new_content_lines: List[str] = []
    chapter_names = get_chapter_names(content_lines, new_content=new_content_lines)

    toc_content = TOC_BEGIN + f'\n## {toc_chapter_name}\n' + '\n'.join(map(
        chapter_name_to_md_item,
        chapter_names
    )) + '\n' + TOC_END

    new_content = '\n'.join(new_content_lines)
    new_content = RE_TOC_INIT.sub(toc_content, new_content, re.MULTILINE)

    with file.open('w') as f:
        f.write(new_content)


def main() -> int:
    try:
        file = Path(argv[1])
        assert file.is_file()
    except (IndexError, AssertionError):
        print(f"usage: {argv[0]} md_file [TOC chapter name]")
        return 1

    try:
        toc_chapter_name = argv[2]
    except IndexError:
        toc_chapter_name = TOC_CHAPTER_NAME

    generate_file_toc(file, toc_chapter_name)
    return 0


if __name__ == '__main__':
    exit(main())
