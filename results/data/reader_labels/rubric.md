# Rubric for Labeling Rows as Code or Not

*Written before any row was labeled. Every reader applies this rubric and nothing else. The labels are frozen once compiled and before any experiment on the paper's model reads them.*

## What a Row Is

Each row is 512 tokens of text from the Pile, decoded to characters. A row can contain more than one document; a line reading `----- [document boundary] -----` marks where one document ends and the next begins. The header line `=== ROW <set>:<index> ... ===` identifies the row; copy the `<set>:<index>` part exactly into your label.

## The Four Labels

Judge the row by what **more than half of its characters** are.

| Label | Give it when more than half of the row's characters are |
|---|---|
| `code` | source code in any programming language, shell or build scripts, markup or configuration or data files as found in a software repository (HTML, CSS, XML, JSON, YAML, TOML, CSV, Makefiles, Dockerfiles), or software licenses and READMEs that are mostly code or configuration |
| `prose` | natural-language text meant to be read: articles, web pages, encyclopedia entries, papers, books, emails, forum posts, legal or patent text, abstracts, subtitles, without substantial code |
| `mixed` | a genuine mixture, neither side above half: a forum post or documentation page with substantial code blocks and substantial explanation; or a row that straddles a document boundary between a code document and a prose document |
| `other` | mathematics (equations, symbolic problems), tables of numbers, chat or IRC logs, program output or log files, lists of names or references, garbled or non-English text, or anything that fits none of the above |

Rules of thumb, applied in this order:

1. A README or documentation page written mostly in sentences is `prose` even if it lives in a repository; one that is mostly commands, code blocks, or configuration is `code`.
2. LaTeX source of a paper is `prose` if the text dominates and `other` if equations and macros dominate; it is never `code`.
3. Comments inside source code count as code. Docstrings count as code when they sit inside a code file.
4. A StackExchange-style question and answer with code blocks is `mixed` unless the code clearly exceeds half, then `code`, or clearly falls below a quarter, then `prose`.
5. If a row straddles a boundary, judge the whole row's characters, not the first document; a row that is 60 percent code document and 40 percent prose document is `code`.
6. When two labels seem equally right, prefer `mixed` over `code` or `prose`, and `other` only when neither code nor prose describes the bulk.

## Confidence

After the label, add one of `sure` or `unsure`. Mark `unsure` when you would not be surprised if another careful reader chose differently.

## Output Format

Reply with one line per row and nothing else before the lines:

```
E:17	code	sure
E:18	prose	sure
E:19	mixed	unsure
```

Fields separated by a single tab: the row key exactly as in the header, the label, the confidence. Every row in your chunk must appear exactly once. After the lines you may add at most three sentences on anything that made the chunk hard to label.

## What Not to Do

Do not look up the text, do not guess where it came from, and do not use anything other than the characters in the row. Do not skip rows. Do not invent labels beyond the four.
