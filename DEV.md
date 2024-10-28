# Development guidelines

## Github workflow
Before commiting or pushing to github, remember run these in the terminal and make sure everything passes:
```
python -m pytest .\MISOReports\test_MISOReports.py
```
```
mypy --strict .\MISOReports\MISOReports.py 
```

## Coding style
* We are using the vscode extension, autoDocstring's, one-line-sphinx documentation template.
* Try to keep the style the same as the code that was previously there in all respects (naming schemes, character length per line, etc.) 
* Try too keep the line length to PEP8 standards. Exceptions where it makes sense is fine.
* When adding support for a new report, if it is on the TODO list, mark it off as done. If not, make a new entry for it.

## Reports to pandas dataframe mapping logic
When in doubt, check previously completed reports (you can find them on the TODOS.md file).

* If any number in the column has a decimal, convert column to Float64.
* If the numbers in the column are all integers, convert column to Int64.
* If the number is a datetime, convert column to datetime64.