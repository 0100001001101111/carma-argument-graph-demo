# Portable evidence boundary

The private Aletheia reports are larger and contain internal task material. This repository includes two sanitized JSON extracts instead.

Each extracted record carries the SHA-256 of its original artifact. The portable verifier can prove that the included extract did not change after the manifest was frozen. It cannot independently reconstruct the private source from the hash.

The model scores are read from the included extract at runtime. They are not copied into the generated graph by hand. A test changes Codex from 15 of 25 to 0 of 25, updates the extract hash and manifest hash, and confirms the case contract still rejects it.

This protects the work sample from decorative fingerprinting while keeping private task material out of the repository.
