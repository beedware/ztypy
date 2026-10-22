#import ".utility/style.typ": style
#show: style

#let title = "Automata Snapshot"
#let id = 20260429150003

#id:cs:theory:automata:

= #title
Quick reminder from @01-2[p.~19]:

$ L = { a^n b^n | n >= 0 } $ is context-free but not regular.

Pumping lemma often starts by assuming regularity and deriving contradiction.

= Links
- 20260429150002:Recurrence Cheatsheet
- 20260429150004:TCP Throughput Back-of-the-Envelope

#bibliography(".utility/sources.yaml")
