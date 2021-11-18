## [20.8.2] - 2021-11-18 -- Update Flask and itsdangerous packages
### Changed
    - Support Flask 2.x.x
        - werkzeug cache is no longer supported, changed to flask-caching
    - Support itsdangerous 2.x.x
        - TimedJSONWebSignatureSerializer is deprecated
        - Replaced with URLSafeTimedSerializer
## [20.8.1] - 2021-09-02 -- Tidy up Intermediate API and ReadMEs
### Changed
	- Rename Middleware to IntermediateAPI.
    - Upload `.env.example`.
    - Update ReadME to provide better information.
