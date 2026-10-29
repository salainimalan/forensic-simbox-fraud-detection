from common import load_events, ensure_out

events, malformed, variants, fraud, duplicate_count = load_events()
out = ensure_out("01_preprocess")
events.to_csv(out / "canonical_events.csv", index=False)
malformed.to_csv(out / "malformed_rows.csv", index=False)
variants.to_csv(out / "schema_variants.csv", index=False)
(out / "fraudulent_users.txt").write_text("\n".join(sorted(fraud)) + "\n", encoding="utf-8")
(out / "quality_summary.txt").write_text(f"canonical_events={len(events)}\nmalformed_rows={len(malformed)}\nschema_variants={len(variants)}\ncross_file_duplicates_removed={duplicate_count}\ntimestamp_min={events.timestamp.min()}\ntimestamp_max={events.timestamp.max()}\n", encoding="utf-8")
print(f"canonical events={len(events):,}; cross-file duplicates removed={duplicate_count:,}")
