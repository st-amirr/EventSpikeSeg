# Progress

## Working now

- embedded DDD17 root: `C:/Users/stamir/Desktop/Dataset/DDD17`
- fixed layout: `events/{train,test}/*.npy` + `labels/{train,test}/*.png` paired by stem
- held-out set is Ev-SegNet `test`
- native six-channel event-statistic loading
- exact six-class mapping with ignore label 255
- direct SNN encoding over configurable internal timesteps
- ten configurable lightweight encoder/decoder variants
- same-seed architecture benchmark
- mIoU, per-class IoU, pixel accuracy, parameter count, and output spike-rate reporting
- winner-checkpoint promotion and visual validation
- Docker tests: passed

## Not yet measured

- real DDD17 smoke-training result
- real DDD17 benchmark results
- winning architecture
- high-resolution results
- multi-seed winner stability
- quantized accuracy
- FPGA synthesis, latency, power, or resource use
