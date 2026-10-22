#import ".utility/style.typ": style
#show: style

#let title = "Scala Type Inference Fragments"
#let id = 20260429150008

#id:scala:pl:types:

= #title
Inspired by @01-8[p.~63].

Identity function shape:
$ id(x) = x $ and principal type $forall a. a -> a$.

Prefer explicit type annotations at module boundaries.

= Links
- 20260429150007:C++ Value Category Notes
- 20260429150009:Functional Patterns with Images

#bibliography(".utility/sources.yaml")
