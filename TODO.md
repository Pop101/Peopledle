\### Project status

- [] Fix parser to parse Level 3 articles as well - it's only parsing Level 4 - Level 3
- [] Redaction algorithm 
    - 1. Remove everything inside parentheses, including the parentheses
    - 2. Remove everything past a comma, including the comma
    - 3. Split name into Name-Components, 1 through ??? (probably no more than 5)
    - 4. Redact each of these per sentence by replacing it with [NAME COMPONENT X] where X is the number of the component.
