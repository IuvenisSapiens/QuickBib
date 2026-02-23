# QuickBib Translations

Translations are stored as JSON files in this directory.

- `en.json` is the source of truth for all keys.
- Each translation file must be named with a locale code, for example:
  - `fr.json`
  - `pt_br.json`
  - `zh_cn.json`

QuickBib picks translations in this order:

1. `LC_ALL` (if set)
2. `LC_MESSAGES` (if set)
3. `LANG` (if set)
4. System locale from Qt (for example `fr_FR`)
5. Locale language fallback (for example `fr`)
6. `en`

## Add a new language

1. Copy `en.json` to a new locale file (for example `de.json`).
2. Translate values, but keep keys unchanged.
3. Run:

```bash
python tools/check_translations.py
```

4. Open a pull request.
