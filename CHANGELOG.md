# Changelog

All notable changes to this project are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/); releases are named by the date they reached production,
and each entry says why the change was made.

## [Unreleased]

## [2019-03-05]

### Changed

- Dependencies are locked in `package-lock.json`, and `twilio` moves from 2.x to 3.x (8c17145)

## [2016-11-17]

### Changed

- Every page is restyled, and `public/stylesheets/style.css` is cleaned up (472eac4)

### Fixed

- The `Models/` folder is renamed to `models/`, so `require('./models/models')` resolves on Heroku's case-sensitive file system (d09f935, 952e188)

## [2016-11-10]

### Added

- Groups for friends deciding where to go out: create one with a name and description, add members by username, and delete it (d063e6c)
- Votes over a date range: pick event types, and the group's candidates come from an event catalog that `seed.js` loads from `events.json` (d063e6c)
- Yes-or-no voting on each event, one at a time, with results ranked by yes votes and a page of the winners (d063e6c)
- Accounts with a username, password and phone number, confirmed by a 4-digit code sent by text message (d063e6c)
- Text messages to the group when a vote closes, because everyone voted or its time limit passed, and when a member confirms the winning event (d063e6c)

### Security

- The MongoDB URI, Twilio credentials and sending number are read from `MONGODB_URI`, `ACCOUNT_SID`, `AUTH_TOKEN` and `FROM_PHONE` instead of the code (f0390be)
