# TPDS format verification

Verified on 2026-11-11 against the current IEEE Computer Society author page and an actual download from the IEEE Template Selector. This is a formatting decision record for the new manuscript, not a modification to the old paper.

## Decision

Retain `\documentclass[10pt,journal,compsoc]{IEEEtran}` and the unmodified IEEEtran 1.8b class. Produce a main paper of at most 12 pages and a separate supplementary PDF. Keep the class's body font, leading, text area, and column widths. Do not manually apply 9.5-point text, 11.5-point leading, narrow margins, or a smaller body font to reach the page target.

The current `source/manuscript.tex` already selects the recommended Computer Society journal mode. `source/IEEEtran.cls` identifies itself as 2015/08/26 V1.8b. The checked preamble does not override body font size, leading, text width, or margins. The preprint-only style must remain disabled for the TPDS PDF.

## Current official requirements

The [TPDS author page](https://www.computer.org/csdl/journal/td/write-for-us/15085), read in the rendered browser because its initial HTML does not include the policy text, specifies 12 double-column pages for a regular paper. It currently allows submissions of up to 18 pages subject to mandatory overlength charges. References and author biographies count. Thus 12 pages is our editorial target and the regular-paper baseline, not the current absolute submission maximum.

That page describes a formatted page as 7.875 by 10.75 inches, with 9.5-point type and 11.5-point vertical spacing. Supplementary material must be submitted as separate files rather than appended to the main PDF; its length is not limited by the main-paper limit.

The [Computer Society author resources](https://www.computer.org/publications/author-resources) require the journal template and a 100–200-word abstract for regular and special-issue papers. The abstract should not contain mathematical expressions or bibliographic citations. Its double-anonymous option is a request to the editor with an explanation, subject to editorial discretion; TPDS is not in the listed exclusions. We therefore retain the named author in this draft and do not assert that TPDS mandates anonymous manuscripts.

## Actual official template download

The [IEEE Author Center template page](https://journals.ieeeauthorcenter.ieee.org/create-your-ieee-journal-article/authoring-tools-and-templates/tools-for-ieee-authors/ieee-article-templates/) directs authors to the IEEE Template Selector.

The selector was traversed for **Journals → IEEE Transactions on Parallel and Distributed Systems → Original Research → LaTeX**. Its final page explicitly identified the download as the template for an original research article for TPDS.

- Selector: <https://template-selector.ieee.org/secure/templateSelector/publicationType>
- Selected download page: <https://template-selector.ieee.org/secure/templateSelector/downloadTemplate?publicationTypeId=1&titleId=155&articleId=1&fileId=200>
- Saved archive: `tpds_official_template/ieee_tpds_original_research_latex.zip`
- Archive size: 541,768 bytes.
- SHA-256: `f1abd5e9ed440e4263d9e9c2d941eeb4d4cfcfdfece43ccfa10e87613c7bdde9`.

The downloaded generic sample begins with `[lettersize,journal]`. The guide in the same official archive, `New_IEEEtran_how-to.tex`, explicitly gives `[10pt,journal,compsoc]` for a Computer Society journal article and describes IEEEtran 1.8b. This is the relevant style selection for TPDS and is already used by the manuscript. The guide explains that the templates approximate final appearance and page length; final publisher composition may differ.

## How the existing class supplies the dimensions

Inspection of the actual class used by this draft resolves the apparent mismatch between the `10pt` option and the 9.5-point author instructions:

- In `compsoc` journal mode, the `10pt` option defines normal text as **9.5 bp with 11.54 bp leading**. The class comments explain this publisher-oriented adjustment. We preserve it; we do not replace it with a custom 11.5 value.
- It supplies Computer Society column widths, gutter, heading styles, and Palatino-family body text automatically.
- Its default physical sheet is US Letter. The `cspaper` option selects the 7.875 by 10.75-inch publication trim, without changing typesetting in Computer Society journal mode. The class explicitly advises authors to use that trim option only when the journal editors request it and otherwise generally to use US Letter.
- We retain the template's US Letter default instead of adding a custom geometry configuration. The published trim dimensions and the submission sheet dimensions are distinct; the typeset content and page count remain governed by the class.

The final verification should check that the TPDS entry point neither defines `arxivReadable` nor appends `supplement_body`, that the main PDF stays within the 12-page target, and that the supplementary PDF compiles independently.

## Evidence and limits

This verification uses the current primary author pages, the actual downloaded official template, and the source of the class in the draft. It does not infer policy from old special-issue calls, third-party summaries, or an old 12-page hard-limit statement. No claim is made that the downloaded sample and IEEE's final production system produce identical pagination.
