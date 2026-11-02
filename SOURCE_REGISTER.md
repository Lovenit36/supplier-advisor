# Verified manufacturer source register — 1 Nov 2026

Product-level evidence URLs are embedded in `data/pumps.json` and appear in the actual results.

## Wilo — Yonos PICO exact variants

Official Wilo [product series and article-number table](https://wilo.com/gb/en/Products/en/products/yonos-pico_id199) lists 12 pump variants with article number, G thread connection, port-to-port length, PN10 and 1~230 V mains supply. Selected records below are used in this MVP (model, article, length):

| Variant | Article | Length | Thread |
|---|---:|---:|---|
| Yonos PICO 25/1-4 | 4215513 | 180 mm | G 1½ |
| Yonos PICO 25/1-4-130 | 4215514 | 130 mm | G 1½ |
| Yonos PICO 25/1-5-130 | 4215522 | 130 mm | G 1½ |
| Yonos PICO 25/1-6 | 4215515 | 180 mm | G 1½ |
| Yonos PICO 25/1-6-130 | 4215516 | 130 mm | G 1½ |
| Yonos PICO 25/1-8 | 4215517 | 180 mm | G 1½ |

Specific Wilo product pages support selected max head/flow and operating characteristics, for example [25/1-4](https://wilo.com/au/en/Catalogue/en/products/yonos-pico_id199/4215513), [25/1-5-130](https://wilo.com/au/en/Catalogue/en/products/yonos-pico_id199/4215522), [25/1-6](https://wilo.com/au/en/Catalogue/en/products/yonos-pico_id199/4215515), [25/1-6-130](https://wilo.com/au/en/Catalogue/en/application/building-services-residential/cooling-and-air-conditioning/cooling/wilo-yonos-pico/yonos-pico-25-1-6-130) and [25/1-8](https://wilo.com/au/en/Catalogue/en/products/yonos-pico_id199/4215517). Unconfirmed individual values are stored as `null` rather than inferred from a model code. At **no point** does a maximum-flow or maximum-head number prove actual operation at a requested simultaneous flow/head duty point.

## Grundfos — ALPHA2 D-A-CH Model E

Official [Grundfos ALPHA2 data booklet](https://api.grundfos.com/literature/Grundfosliterature-6014959.pdf), product-number table p. 34 (Germany, Austria and Switzerland), lists these exact pump models and article numbers:

| Model E variant | Article | Length | Thread |
|---|---:|---:|---|
| ALPHA2 25-40 180 | 99260497 | 180 mm | G 1½ |
| ALPHA2 25-60 180 | 99261730 | 180 mm | G 1½ |
| ALPHA2 25-40 130 | 99261701 | 130 mm | G 1½ |

The booklet's electrical data lists 1 × 230 V ±10% at 50/60 Hz and describes the ALPHA2 modes. The exact-model point on an actual performance curve, hydraulic compatibility, and some temperature/pressure numbers remain `null` rather than assumed from the family designation. These are D-A-CH article identifiers; an offer for a different regional model is not automatically equivalent.

## Plancraft referral

Official [Plancraft feature overview](https://plancraft.com/en-gb/features) and [project folder](https://plancraft.com/en-gb/features/project-folder) describe document storage, project folders, cost management and supplier invoices. The outbound CTA links to a genuine Plancraft feature page; it does not imply that this independent prototype is a Plancraft product or integrates with their app.

## Source constraints

This register proves catalogue facts, **not** cross-brand replacement approval, universal compatibility, retail price, availability or accessories. All labour and additional-part prices are installer-entered and displayed with that provenance. Read manufacturer installation instructions and inspect the system before purchasing or replacing a pump.
