# Roadmap

What we're building next for **QKDpy**, in practical terms. For
researchers using the library today, that's mostly just a heads up on
what additional capabilities are landing in following releases.

## What's landing next

**Broader attack simulations.** More attacker models out of the box —
beyond the existing PNS, intercept-resend, and beam-splitting — so
researchers can study how each protocol holds up under different
threat scenarios.

**Plug-in channels.** A clean interface for plugging in *your own*
fiber / free-space / mixed-channel model without forking the simulator.
Today's library ships several built-in models; the next release adds
the contract to bring your own.

**Better tuning tools.** Bayesian-driven parameter search is already
here; following work makes that loop faster and easier to drive from
the public API.

**Larger protocol coverage.** Each release picks up one or two
additional protocol variants based on what the community has been
asking for.

## What we are intentionally not promising

QKDpy is a **simulator** — it models phenomena. It is **not** a
cryptographic module you can drop into production. We don't ship — and
don't intend to ship — anything that would let it be confused with a
certified HSM, a license server, or an audited enterprise machine.

That boundary is intentional. Inside that boundary, the goal is to
keep building a fast, honest simulator that researchers and educators
can trust.

## Releases

The public roadmap above rolls up into the release notes published on
GitHub. New functionality tends to land in minor releases on a roughly
monthly cadence, with bug-fix patch releases as needed between them.

For the precise current version and a list of what changed, see the
project's GitHub release page.
