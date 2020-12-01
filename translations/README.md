# Translation files for WPIA motion tool

Add the needed translation files here.

The software is translated via Transifex: https://www.transifex.com/wpia/motion/.

The current files are also available in the motion-translations repository on our gitlab system https://git.ccs-baumann.de/wpia/motion-translations.

To extract the translation files use:

```
pybabel extract -F ./translations/babel.cfg -k _l -o ./translations/messages.pot --input-dirs=.
```

To create a language file use e.g. de

```
pybabel init -i ./translations/messages.pot -d translations -l de
```

The translation files are maintained in a repo and translated on Transifex [https://www.transifex.com/wpia/landingpage-1/dashboard/](https://www.transifex.com/wpia/landingpage-1/dashboard/).

The translation file are stored in this files structure translations/XX/LC_MESSAGES/messages.po with XX as language code.

To compile the translated text from *.po to *.mo use:

```
pybabel compile -f -d translations
```
