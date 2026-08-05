# How this maps to the CARMA role

I built this from Project Aletheia, my one-person verification lab.

The repository demonstrates:

- a typed graph for claims, evidence, assumptions, objections, rebuttals, and uncertainty
- deterministic grounded-semantics evaluation over a documented attack projection
- hash-bound provenance with runtime value extraction
- a fixed boundary between model proposals and accepted evidence
- explicit counterarguments and candidate-only uncertainty
- mutation tests for doctored sources, missing objections, confidence changes, dependency cycles, and inflated claims
- reproducible machine and human-readable exports

The example preserves an awkward mixed result. Two systems scored 0 of 25. A stronger system scored 15 of 25. The system keeps the capability evidence and the failure evidence together, then limits the conclusion to the frozen task.

This is the engineering pattern I would bring to a larger argumentation platform: machine assistance for population, explicit provenance, human ownership of judgment calls, and deterministic checks wherever the structure permits them.
