# Changelog

## 1.0

### Breaking changes

- Require Python 3.10+ (dropped 3.9) (#188)
- HTML transformation dependencies (`cssutils`, `lxml`, `chardet`, `requests`, `premailer`) are now optional — install with `pip install emails[html]` (#190)
- Removed Python 2 compatibility helpers `to_bytes`, `to_native`, `to_unicode` from `emails.utils` (#197)
- Replaced vendored `emails.packages.dkim` with upstream `dkimpy` package — use `import dkim` directly (#196)

### Added

- `reply_to` parameter for Message (#115)
- Content-based MIME type detection via `puremagic` when file extension is missing (#163)
- Data URI support in transformer — `data:` URIs are preserved as-is (#62)
- Type hints for public API (#191)
- mypy in CI (#194)
- Python 3.13 and 3.14 support (#184)
- Django CI jobs with Django 4.2, 5.2, 6.0 (#201)
- CC/BCC importing in MsgLoader (#182)
- RFC 6532 support — non-ASCII characters in email addresses (#138)
- In-memory SMTP backend (#136)
- SMTP integration tests using Mailpit (#186)

### Fixed

- Double stream read in `BaseFile.mime` for file-like attachments (#199)
- `as_bytes` DKIM signing bug (#194)
- SMTP connection is now properly closed on any initialization failure (#180)
- SMTP connection is now properly closed on failed login (#173)
- Incorrect `isinstance` check in `parse_name_and_email_list` (#176)
- Message encoding to bytes in SMTP backend (#152)
- Unique filename generation for attachments
- Regex escape sequence warning (#148)
- Replaced deprecated `cgi` module with `email.message`
- Coverage reports now correctly exclude `emails/testsuite/`

### Maintenance

- Removed vendored dkim package (~1400 lines)
- Removed Python 2 compatibility code and helpers (#188, #197, #198)
- Updated pre-commit hooks to current versions
- Updated GitHub Actions to supported versions
- Removed universal wheel flag (py3-only)
- Cleaned up documentation and project metadata
- Added Python 3.12 to test matrix (#169)

## 0.6 — 2019-07-14

Last release before the changelog was introduced.
