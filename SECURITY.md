# Security

## Reporting a problem

If you find a security problem in this repository, in a page it publishes or in code it asks you to
run, please report it privately: write to apapadogiannis@gmail.com, or use "Report a vulnerability"
under the Security tab of the repository where that button is shown. Please do not open a public
issue for it. Say what you found, where, and how to see it. I answer within a few days.

A wrong number is not a security problem, but it is just as welcome: open an issue.

## What to expect from my repositories

- **No secrets.** No key, token or password is stored in a repository, and none is needed to use one.
- **Pages.** Each page is a static file served by GitHub Pages. It has no login and sets no cookies.
  A content security policy limits what it may load to the hosts it names, and a library loaded from
  a public host is checked against a fixed hash before it runs. What a page sends, and to whom, is
  stated in the Privacy section of its README.
- **Code you run yourself.** A program offered for your own machine (the MCP server of the
  `dual-risk-calculator`) opens no network connection and reads and writes no files. Its install line
  names a released version, never the moving head of the repository.
- **Automation.** The workflows run with read-only access. The one job that stores new data is the
  only one that can write, and it is handed its token for the single step that pushes. Every action
  is pinned to a full commit.
- **Data.** Downloads come from fixed, named public sources. New observations are added after the
  stored ones, and a revision of a stored value is reported, not absorbed.

## Supported versions

The latest release, and the head of `main`. Older releases stay archived on Zenodo as they were and
are not changed.
