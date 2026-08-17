# Block diagram

Placeholder — a visual block diagram should go here (e.g. exported from
the KiCad hierarchy or drawn separately). Textual summary of the signal
flow in the meantime:

```
USB-C (J3) ──► TPS25751 (PD sink + power path) ──► BQ25792 (buck-boost charger) ──► VBAT
                                                                                        │
4S2P 18650 pack ───────────────────────────────────────────────────────────────────────┤
                                                                                        ▼
                                                              BQ76920 (protection AFE)
                                                              + high-side dual-FET guard
                                                                                        │
                                                                                        ▼
                                                                                  VBAT_PROT
                                                                                        │
                                        ┌───────────────────────────────────────────────┼──────────────┐
                                        ▼                                               ▼              ▼
                              TPS563201 (3.3V buck)                          LM3409HV x2 (LED drivers, PWM_A/PWM_B from MCU)
                                        │                                               │
                                        ▼                                               ▼
                          STM32G031K8T6 (MCU) ◄──── HMI (4 buttons)          LED array (64x 660nm, 2ch x 8 parallel x 4 series)
                                        │
                                        ▼
                                 SWD debug (J6/J7)
```

Fill in with the actual rationale/tradeoffs discussed separately once
available (referenced in the original project brief as "I'll fill in
details from our chat separately").
