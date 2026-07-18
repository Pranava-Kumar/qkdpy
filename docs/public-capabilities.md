# Capabilities

A summary of what **QKDpy** does today. For installation, the API
reference, and worked examples, use the navigation on the left.

## What it is

QKDpy is a Python library for **quantum key distribution simulation**.
It models the protocols, the underlying physics, the key-distillation
pipeline, and a number of attacker scenarios — so you can study how a
QKD system behaves without standing up a photonics lab.

It is suitable for:
- Learning how QKD protocols work and comparing them side by side
- Studying how signal conditions translate to sifted-key rates and
  bit-error behaviour
- Pulling the public Python models into notebooks and ML experiments
- Building tooling on top of a clean, typed, fully-tested QKD API

## What's in the library

- **10+ QKD protocols.** BB84 family (including decoy-state variants),
  E91 entanglement-based, CV-QKD continuous-variable, high-dimensional,
  device-independent, twisted-pair, SARG04 and B92.
- **Realistic-ish channels.** Loss, depolarizing, bit / phase / amplitude
  damping, dephasing — plus atmospheric, free-space and satellite helpers
  for satellite-ground scenarios.
- **Key management.** Cascade, Winnow, LDPC, BCH, Reed-Solomon error
  correction. Universal hashing, Toeplitz, cryptographic hashing for
  privacy amplification.
- **Attack simulators.** Photon-number-splitting, intercept-resend,
  beam-splitting — useful both for studying defense and for generating
  realistic bad-channel data.
- **Framework bridges.** Optional extras for Qiskit, Cirq, PennyLane
  and the QpiAI Quantum SDK — so you can drop QKDpy's models into
  whichever quantum stack you already work with.
- **ML hooks.** Bayesian and genetic-optimization parameter search,
  small neural predictors meant to run on edge devices.

## What it is not

For the honest list of "do not do this with QKDpy," see the *Status &
Scope* section in the README on GitHub. In one line: this is a
simulator for understanding QKD, not a cryptographic module for
protecting production secrets.
