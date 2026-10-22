#import ".utility/style.typ": style
#show: style

#let title = "TCP Throughput Back-of-the-Envelope"
#let id = 20260429150004

#id:networking:performance:

= #title
Motivated by @01-3[p.~56].

Approximation:
$ "throughput" approx "cwnd" / "rtt" $.

If congestion window doubles each RTT in slow start, growth is exponential.

= Links
- 20260429150003:Automata Snapshot
- 20260429150006:Memory Hierarchy Diagram
- 20260429150001:Algorithmic Growth Notes

#bibliography(".utility/sources.yaml")
