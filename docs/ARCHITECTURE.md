# Architecture

## Active task

Six-class semantic segmentation of the Ev-SegNet DDD17 six-channel event-statistic representation. The model input is `[T,N,6,H,W]`; direct encoding repeats one six-channel sample over `T` internal updates.

## File separation

- `model.py`: canonical production model only (`v10_fpga_hybrid` until promotion)
- `model_components.py`: shared layers and neuron dynamics
- `top_ten_models.py`: frozen completed round-one presets
- `top_five_models.py`: preserved v1/v2 experiments and active retinotopic-mechanism five

## Shared encoder-decoder

The lightweight backbone uses depthwise/pointwise spiking blocks, two spatial downsampling stages, optional dilated or parallel multiscale context, nearest-neighbor upsampling, additive skips, optional residual paths, and a spiking 1×1 semantic head. Auxiliary heads are training-only supervision paths.

## Revised PLIF neuron

For channel `c`:

```text
V_c[t] = beta_c V_c[t-1] + I_c[t]
S_c[t] = H(V_c[t] - theta_c[t])
V_c[t] <- V_c[t] - theta_c[t] after a spike
```

Both `beta_c` and the base threshold are learnable and bounded. The first top-five learned only `beta_c`, leaving all thresholds fixed.

## Revised f_long

The failed v1 implementation used a fixed integer `T_thresh=4` and binary `amax` activity. V2 uses normalized feature-map spike rate:

```text
r_c[t] = mean_{N,H,W}(S_c[t])
a_c[t] = exp(-1/tau_c) a_c[t-1] + k_c (r_c[t] - r_target,c)
theta_c[t] = clamp(theta_base,c + a_c[t])
```

`tau_c`, `k_c`, and `r_target,c` are learnable. Bidirectional error lets silent channels lower their effective threshold and overactive channels raise it. The continuous tau is the trainable replacement for the nondifferentiable integer timer and must later be quantized for FPGA inference.

## Revised f_inst

Hard all-channel winner-take-all is no longer used in revised contenders. The one competition contender uses grouped top-2 competition in encoder features only. The repaired lightweight contender uses grouped top-2 only in the stem. Decoder and class-head features are not suppressed.

## Semantic readout

Revised heads allow independent class neurons to emit spikes. Class logits remain temporal spike counts, and final prediction is the argmax after accumulation. This removes timestep-level class starvation without introducing an analog classifier.

## Training protections

- 30% homeostasis/competition warm-up
- 3× optimizer rate for neuron dynamics
- weighted CE + focal CE + Dice
- dead/excessive layer activity regularization
- full selected-subset class-weight estimation
- recorded class support, predictions, layer spike rates, and learned neuron parameters

## Hardware interpretation

PLIF beta, base threshold, homeostasis tau, strength, and target rate are floating-point training parameters. A winner is not hardware-final until each is quantized to shift/add or fixed-point operations and the integer reference reproduces segmentation metrics.


## Retinotopic-mechanism neuron dynamics

The v2 rate controller is now historical. Debat et al. (2021) uses retinotopic membrane-energy inhibition rather than a global feature-map target rate. For one spatial patch, the retinotopic mechanisms compute a local `retinotopic_membrane_energy` as the RMS of feature-neuron membrane potential after subtracting the active shared threshold penalty.

When `triangular_threshold_adaptation` is enabled, each neuron that spikes starts one triangular `ULong` process. Its peak amplitude is `fLong * UPropInh`; it rises linearly for learned `TThresh`, falls linearly for another `TThresh`, and then becomes zero. All active processes at the same `(x,y)` are summed and added to every feature neuron's threshold at that retinotopic location. `fLong` and continuous `TThresh` are learned per layer in our supervised implementation.

For `winner_peer` fInst, if several feature neurons cross threshold at the same binned step, the strongest membrane is used as the synchronous proxy for Debat et al.'s first asynchronous spike. Only that feature spikes and peers at the same `(x,y)` receive the learned `fInst * UPropInh` membrane decrement. `peer_membrane` leaves simultaneous spikes intact but applies the peer decrement. Both are restricted to early/encoder features.

The semantic class head uses local class WTA independently of hidden fInst. This restores the successful round-one class-head behavior while keeping inhibition out of the decoder.
