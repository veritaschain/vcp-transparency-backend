# Slack Introduction Post (transparency-dev)

> **Dated note — 25 October 2026:** This outreach draft was added to the repository on 5 January 2026. Whether and where it was posted is not recorded in this repository, so its text is left as written. Its description of IETF status is not accurate: `draft-kamimura-scitt-vcp` is an individual Internet-Draft (current revision `-05`), not adopted by the SCITT Working Group, and it is not "going through" or "progressing through" IETF as a SCITT profile. VCP v1.0 is superseded by VCP v1.2 (Released, tag `v1.2.0`). Do not reuse this text without correcting it.

**Channel:** #general or #trillian (check which is appropriate)

---

Hi all 👋

**Who:** I'm working on VeritasChain Protocol (VCP) — an open standard for cryptographic audit trails in algorithmic trading systems. Think "flight recorder for trading algorithms." We're going through IETF as a SCITT profile: https://datatracker.ietf.org/doc/draft-kamimura-scitt-vcp/

**What we want:** We'd like to use Trillian/Tessera as a transparency log backend for VCP evidence. The goal is to anchor VCP audit events in a Merkle tree so third parties (regulators, auditors) can verify append-only integrity without trusting the log operator.

**What we have:** 
- 1-page adapter spec mapping VCP events → leaf format → proof packaging
- Draft repo: [link to vcp-transparency-backend]

**Questions we're hoping to get guidance on:**
1. **Tessera status** — Is Tessera recommended for new production deployments now, or should we start with Trillian v1?
2. **Identity hash** — For timestamped event logs, what's the best practice: dedup-enabled (timestamp-excluded hash) or treat every event as unique?
3. **Proof packaging** — What's the minimum set of fields verifiers expect? Is checkpoint signature essential or optional?

Happy to file a GitHub issue with more detail if that's preferred. Just wanted to introduce ourselves first per the README guidance.

Thanks!
