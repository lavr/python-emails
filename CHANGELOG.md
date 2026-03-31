# Changelog

## Unreleased

### Breaking changes

- Dropped Python 2 support. Python 3.9+ is now required (#188)
- HTML transformation dependencies (`cssutils`, `lxml`, `chardet`, `requests`, `premailer`) are now optional — install with `pip install emails[html]` (#190)

### Added

- Python 3.13 and 3.14 support (#184)
- CC/BCC importing in MsgLoader (#182)
- RFC 6532 support — non-ASCII characters in email addresses (#138)
- In-memory SMTP backend (#136)
- SMTP integration tests using Mailpit (#186)

### Fixed

- SMTP connection is now properly closed on any initialization failure (#180)
- SMTP connection is now properly closed on failed login (#173)
- Incorrect `isinstance` check in `parse_name_and_email_list` (#176)
- Message encoding to bytes in SMTP backend (#152)
- Unique filename generation for attachments
- Regex escape sequence warning (#148)
- Replaced deprecated `cgi` module with `email.message`

### Maintenance

- Updated pre-commit hooks to current versions
- Updated GitHub Actions to supported versions
- Removed universal wheel flag (py3-only)
- Cleaned up documentation and project metadata
- Added Python 3.12 to test matrix (#169)

## 0.6 — 2019-07-14

Last release before the changelog was introduced.
