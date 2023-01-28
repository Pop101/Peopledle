# Project status

## Minimum Viable Product

- [x] Fix parser to parse Level 3 articles as well - it's only parsing Level 4 - Level 3
- [x] Redaction algorithm
    1. Remove everything inside parentheses, including the parentheses
    2. Remove everything past a comma, including the comma
    3. ~~Split name into Name-Components, 1 through ??? (probably no more than 5)~~
    4. Redact each of these per sentence by replacing it with █ ~~[NAME COMPONENT X] where X is the number of the component~~.
- [x] Fill website with placeholder information
- [x] Make website recognize wins and losses

## Stretch Goals

- [x] Allow continuous play
- [x] Allow past people
- [x] Keep a record of all wins and losses
- [ ] Keep an individual record of wins and losses (very shareable, like wordle)
- [x] Make deployments customizable
- [x] Move day.txt to a database
- [ ] Replace the overlays on win and loss
- [ ] Make GitHub page public
  - [x] Remove leftover Codel images
- [x] Add a custom people list
- [ ] Add marketing material
  - [ ] Opengraph
  - [x] Favicon
  - [x] Github pictures & page
- [x] Make it work on mobile (text is microscopic, flex direction should switch to column-reverse, etc)
