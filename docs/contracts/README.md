# ModelShield Contracts

These files define the data contracts shared between the ModelShield
subsystems.

The contracts are the integration boundary between:

- Core ML Evaluation
- Adaptive Investigation
- Failure Intelligence
- Reproducibility
- Failure Memory
- Regression Engine
- CLI
- API
- Dashboard

## Core principle

Do not directly depend on another teammate's internal implementation.

Communicate through these contracts.

## Product flow

Model
→ Challenge
→ EvaluationResult
→ FailureRecord
→ ReproducibilityCapsule
→ Failure Memory
→ RegressionRecord
→ ReleaseDecision

## Contract ownership

### EvaluationResult
Produced by:
Core ML / Evaluator

Consumed by:
Failure Analyzer
Adaptive Investigator
Failure Memory
Dashboard

### FailureRecord
Produced by:
Failure Detection / Failure Fingerprint

Consumed by:
Failure Memory
Reproducibility
Regression Engine
Dashboard

### RegressionRecord
Produced by:
Regression Engine / Failure Memory

Consumed by:
Regression Runner
CLI
CI/CD
Dashboard

### ReproducibilityCapsule
Produced by:
Reproducibility subsystem

Consumed by:
Replay system
Failure Memory
Regression system

### ReleaseDecision
Produced by:
Release Gate

Consumed by:
CLI
Dashboard
CI/CD

## Rules

1. Do not silently rename fields.
2. Do not change the meaning of existing fields.
3. New fields should be backward compatible where possible.
4. IDs must be stable.
5. Challenge parameters must be explicit.
6. Metrics must be numeric and machine-readable.
7. Failures must distinguish verified from unverified.
8. AI-generated suggestions are not evidence.
9. Release decisions must be deterministic.
10. Never store secrets in these contracts.