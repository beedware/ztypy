#import ".utility/style.typ": style
#show: style

#let title = "Algorithmic Growth Notes"
#let id = 20260429150001

#id:cs:math:analysis:

= #title
This note sketches runtime intuition from @01-1[p.~37].

For a geometric series with ratio $r$, we use
$ S_n = (1-r^(n+1)) / (1-r). $

If $T(n) = 2T(n / 2) + n$, then $T(n) in Theta(n log n)$.

This is for maths.

= Links
- 20260429150002:Recurrence Cheatsheet
- 20260429150005:Queueing and Scheduling

#bibliography(".utility/sources.yaml")
