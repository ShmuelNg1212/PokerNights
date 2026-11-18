# A restyled table loses its meaning in Safari

A `<table>` whose rows are given `display: grid` or `display: block` stops being a table to Safari's screen reader: it reads loose text. The closed session's ledger table (`templates/web/night.html`) shows each player on two lines on a phone when a figure is long (`.ledger-stacked`). So every part of it carries its role: `table`, `rowgroup`, `row`, `columnheader`, `rowheader`, `cell`. Keep the roles when the table is changed. `web/tests/test_ledger_table.py` checks that a row header keeps its role.
