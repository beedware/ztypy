#import ".utility/style.typ": style
#show: style

#let title = "Queueing and Scheduling"
#let id = 20260429150005

#id:os:scheduling:math:

= #title
From @01-4[p.~42] and @01-5[p.~12].

Utilization bound reminder for RM scheduling:
$ U <= n(2^(1 / n)-1) $.

For large $n$, this approaches $ln 2 approx 0.693$.

= Links
- 20260429150001:Algorithmic Growth Notes
- 20260429150006:Memory Hierarchy Diagram

#bibliography(".utility/sources.yaml")
