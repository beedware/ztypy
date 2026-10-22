#import ".utility/style.typ": style
#show: style

#let title = "Recurrence Cheatsheet"
#let id = 20260429150002

#id:cs:math:recurrence:

= #title
Master theorem reminders inspired by @01-1[p.~84].

$ T(n) = a T(n / b) + f(n) $

Case sample:
$ a = 2, b = 2, f(n) = n => T(n) = Theta(n log n). $

= Links
- 20260429150001:Algorithmic Growth Notes
- 20260429150003:Automata Snapshot

#bibliography(".utility/sources.yaml")
