# Fixed-content packetization  (200 paired replications)  20260815-143024
out: results/20260815-packetization
Same recipient, same four delivery opportunities, same four focal elements, same background traffic, same seed. Only joint versus separate arrival differs.
frozen block frequencies: low=2 blocks/agent, high=12

## capacity 6   (the operating point named in the brief)
  piecemeal  low   adoption=0.8076 (sd 0.0357)  focal offered/agent=8.00  acquired=2.01  total=10.64  req.evictions=4.12
  bundled    low   adoption=0.8062 (sd 0.0357)  focal offered/agent=8.00  acquired=2.26  total=10.93  req.evictions=4.38
  piecemeal  high  adoption=0.7829 (sd 0.0460)  focal offered/agent=48.00  acquired=4.36  total=11.02  req.evictions=4.49
  bundled    high  adoption=0.7806 (sd 0.0472)  focal offered/agent=48.00  acquired=4.64  total=11.16  req.evictions=4.62
  contrasts at capacity 6:
    bundling effect, low flow    -0.0014
    bundling effect, high flow   -0.0023
    return to flow, piecemeal    -0.0247
    return to flow, bundled      -0.0256
    delivery x flow interaction  -0.0009

## capacity 5   (capacity binds harder under a fixed horizon)
  piecemeal  low   adoption=0.5692 (sd 0.0357)  focal offered/agent=8.00  acquired=2.64  total=13.49  req.evictions=7.61
  bundled    low   adoption=0.5770 (sd 0.0342)  focal offered/agent=8.00  acquired=3.10  total=13.95  req.evictions=8.03
  piecemeal  high  adoption=0.5594 (sd 0.0245)  focal offered/agent=48.00  acquired=6.23  total=14.02  req.evictions=8.21
  bundled    high  adoption=0.5514 (sd 0.0207)  focal offered/agent=48.00  acquired=6.81  total=14.20  req.evictions=8.38
  contrasts at capacity 5:
    bundling effect, low flow    +0.0078
    bundling effect, high flow   -0.0080
    return to flow, piecemeal    -0.0098
    return to flow, bundled      -0.0256
    delivery x flow interaction  -0.0158

DONE.
