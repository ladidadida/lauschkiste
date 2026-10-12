# Documentation with Markdown

We use markdown for documentation. Please add/update documentation in `documentation`.

## Where what goes

- `documentation/en` and `documentation/de` are the guide for people who build and use a Lauschkiste. It is arranged the
  way a newcomer meets it: `get-started` (what you need, install, first card), `what-next.md`, `using`, `hardware` and
  `maintenance`. Both languages have the same files with the same names; **change both when you change one**, and keep
  the order and the headings parallel so that links work in both. The German text addresses the reader with "du".
- `documentation/assets/screenshots/<language>` holds the pictures of the web app. They are generated from a simulated box
  with made-up content: `cd packages/webapp && npx playwright test e2e/screenshots.spec.js --project=mobile`. Run it again
  when the web app changes in a way the guide shows.
- `documentation/developers` is for contributors and is English only.
- Use the names the web app shows for its buttons and settings (see `packages/webapp/public/locales`), and keep the
  steps for beginners free of jargon: say what to type, and what to expect when it worked.

## Linting

To ensure a consistent documentation we lint markdown files.

We use [markdownlint-cli2](https://github.com/DavidAnson/markdownlint-cli2) for linting.

`.markdownlint-cli2.yaml` configures linting consistently for the Github Action, the pre-commit hook, manual linting and the [markdownlint extension](https://github.com/DavidAnson/vscode-markdownlint) for Visual Studio Code.

You can start a manual check, if you call `bam markdownlint`.

After creating a PR or pushing to the repo a GitHub Action triggers the linter, if markdown files are changed (see `.github/workflows/markdown_v3.yml`).

### Disabling Rules

> [!NOTE]
> Please use disabling rules with caution and always try to fix the violation first.

A few rules are globally disabled in `.markdownlint-cli2.yaml` (see section `config`).

If you want to disable a rule for a specific section of a markdown file you can use

```markdown
<!-- markdownlint-disable MD010 -->
section where MD010 should be ignored 
<!-- markdownlint-restore -->
```

### References

- <https://github.com/DavidAnson/markdownlint-cli2>
- Rules:
  - <https://github.com/DavidAnson/markdownlint/blob/main/doc/Rules.md>
  - <https://github.com/DavidAnson/markdownlint/blob/main/README.md#rules--aliases>
