#import ".utility/style.typ": style
#show: style

#let title = "C++ Value Category Notes"
#let id = 20260429150007

#id:cpp:language:notes:

= #title
Cross-check with @01-6[p.~91] and @01-7[p.~14].

Move semantics goal:
$ "cost"("move") << "cost"("copy") $ for resource-owning types.

Rule of five is a practical checklist, not a law.

= Links
- 20260429150006:Memory Hierarchy Diagram
- 20260429150008:Scala Type Inference Fragments

#bibliography(".utility/sources.yaml")
