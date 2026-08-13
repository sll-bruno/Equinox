# Pilot methodology

Universe: Bybit only, BTCUSDT spot and BTCUSDT linear perpetual. Decision features are observed at a closed one-hour candle; execution is the next candle open (`t+1`, UTC). A funding history record is a settled outcome: it is booked only when a position was already open at its settlement timestamp and is never used as contemporaneous input.

Costs are assumptions, not historical spreads: optimistic documented fee-only (10 bps round trip for both legs), base conservative (30 bps), stress (60 bps). The baseline analysis reports all three. No performance claim is valid until the collector, validations and analysis run successfully.

The unavailable `Auditoria_Dados_Bybit_BTCUSDT.md` was not used; this fact must remain in the research log until the source is recovered.
