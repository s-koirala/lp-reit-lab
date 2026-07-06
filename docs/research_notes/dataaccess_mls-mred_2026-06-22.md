---
type: project
date: 2026-06-22
author: SKIE
---

# MLS-Gated Field Access — MRED (Chicagoland) for North-Side Chicago

Goal: obtain condo bed/bath/sqft, rental days-to-lease (DOM), and HOA + special-assessment history that Cook County open data lacks.

**Top recommendation (independent researcher):** Start with **Track C (RentCast)** — no license, same-day API key, and its API License explicitly permits research + redistribution/display, clearing the public-repo concern. It fills bed/bath/sqft + DOM + recurring HOA; it does NOT reliably cover §22.1 special-assessment *history*. If sale-comp depth, full MRED fidelity, or special-assessment history become load-bearing, escalate to **Track A** (Broker license) feeding **Track B** (RESO Web API). Validate every vendor field against the already-ingested Cook County Assessor ground-truth before trusting it.

---

## Track A — Direct MRED (connectMLS) access via Illinois licensure
*Unlocks: full connectMLS UI + (with feed add-on) all gated fields incl. §22.1 special-assessment disclosures (field-level HOA/SA confirmation pending). Cost: mid — see below. Timeline: ~4–10 weeks.*

1. **Pick credential to data goal.** Rental DOM → 15-hr Residential Leasing Agent permit (cheapest qualifying login). Sale comps + HOA/SA history → full **Broker** license (75-hr); leasing-agent scope to *sale* listings is unconfirmed, so default to Broker if sale data is load-bearing.
2. **Complete IDFPR-approved pre-license education** (15 hr leasing / 75 hr broker = 60-hr topics + 15-hr applied). Transcript valid 2 yrs.
3. **Pass the PSI ILREP exam.** Fees: Broker/Managing-Broker $58, Residential Leasing Agent $37; up to 4 attempts in a 2-yr window. (Broker = 100-item National, pass 70%≈scaled-75, + 40-item State, pass 75%; Leasing Agent = 50 items, pass 74%.)
4. **Secure a sponsoring/designated Managing Broker** whose brokerage holds (or can obtain) MRED Participant status; file IDFPR application (Leasing-Agent permit fee $50; Broker/Managing-Broker application fee *(unverified)*). A Live Scan / background step is common for IL licensure but *(unverified)* as a real-estate-specific requirement.
5. **Subscribe to MRED via a participating board.** NAR/REALTOR membership no longer mandatory for MRED (vote 2026-03-16). Confirmed member route: Heartland REALTOR Organization MRED subscriber add-on **$420/yr ($105/qtr)** (official fee form). Non-member "MLS Plus" ~$1,000/yr + ~$144/yr Supra lockbox is *(unverified — trade press only)*.
6. **Complete MRED onboarding** (Participant/Subscriber agreement) → connectMLS login exposes gated fields in the UI. For automated ingest, add the Track-B feed (Web API order form + Participant Data Access Agreement). License/PII hygiene: license + MRED records are under legal identity, NOT the SKIE pseudonym; confirm the executed Data Access Agreement permits storing MRED-derived fields in a PUBLIC repo *before any data lands*.

---

## Track B — Programmatic MRED feed (RESO Web API via MLS Grid or MRED direct)
*Unlocks: BedroomsTotal, BathroomsTotalInteger, LivingArea, DaysOnMarket, AssociationFee (special-assessment history NOT a standard DD field — verify live $metadata). Cost: Path B $500 one-time (Feb-2017 form — reconfirm); Path A no platform fee, MRED feed price unpublished. Timeline: MRED enables ~3 business days post-order.*

*Requires a sponsoring MRED Participant (licensed broker) — there is NO non-licensed "researcher" access tier (MRED Systems Access Policy, 10 types). Query-on-demand replication only; not bulk download. New access is RESO Web API only (RETS sunset 2024-12-31).*

1. **Path A (MLS Grid, recommended for unified licensing):** Data Consumer creates a subscription at mlsgrid.com, adds the sponsoring MRED broker/agent as licensee, sets source = MRED.
2. **Path A:** All parties e-sign the MLS Grid Master Data License Agreement via the portal (Data Consumer + brokerage + MLS).
3. **Path A:** MRED approves the licensee → long-lived OAuth2 bearer token generated on the subscription token tab. Query `https://api.mlsgrid.com/v2/Property` with `Authorization: Bearer`; one `OriginatingSystemName` per filter; page via `@odata.nextLink`. Rate limits: ≤2 req/s, ≤7,200/hr, ≤4 GB/hr, ≤40,000/24h.
4. **Path B (MRED direct OpenID Connect):** Broker mails MRED Web API order form + signed Participant Data Access Agreement + payment ($500 one-time) to orders@mredllc.com. *(Form is V1.0 Feb-2017, titled "Broker RETS Order Form", predates RETS sunset — reconfirm path/price for NEW vendors with retssupport@mredllc.com.)*
5. **Path B:** Implement OpenID Connect client; email Redirect URIs to retssupport@mredllc.com. MRED returns credentials within 3 business days. OData base `https://connectmls-api.mredllc.com/reso/odata`; verify field list against live `$metadata`.
6. **Both paths:** Register every vendor under the broker's license; do not share credentials (MRED issues distinct per-vendor credentials free); notify MRED on termination. Filter to North-Side submarkets post-ingest (no community-area key — geocode by address/ListingId). Verify special-assessment history against live `$metadata` *(unverified — not a structured DD field)*.

---

## Track C — No-license commercial vendor (RentCast primary; Datafiniti #2)
*Unlocks: bedrooms, bathrooms, squareFootage, daysOnMarket (sale AND rental), hoa.fee (recurring), year-keyed tax/assessment, mlsNumber/listingAgent. Does NOT reliably unlock §22.1 special-assessment HISTORY (unverified). Cost: self-serve $0–$449/mo. Timeline: same-day.*

*No real-estate license, brokerage affiliation, or MLS subscription required (verified as absence of any stated gate + documented self-serve flow). Do NOT route Track C through MLS Grid/MRED — that is the licensed broker track.*

1. **RentCast (primary).** Sign up at rentcast.io (free Developer account, 50 calls/mo, $0), open API Dashboard → Create API Key → pick plan. Month-to-month, no contract. Its API License explicitly permits internal research AND resale/redistribution/display to third parties — but the key is confidential (no sharing, incl. affiliates) and scraping is prohibited.
2. **Pull the gated families:** `/properties` → bedrooms, bathrooms, squareFootage, hoa.fee, taxAssessments[YYYY], propertyTaxes[YYYY], lastSalePrice/Date; `/listings/sale` + `/listings/rental` → daysOnMarket, listedDate, status, mlsNumber, mlsName, beds/baths/sqft, listingAgent. (RentCast warns field availability varies by county — measure Cook County fill-rate at step 5.)
3. **Supplement with Datafiniti** for bulk historical depth (1K free / 2-wk trial): numBedroom, numBathroom, floorSizeValue, daysOnMarket, typed `fees`/`deposits`, `assessedValues`/`propertyTaxes` by year. Honor tighter terms: no republishing raw records without significant modification or a separate agreement; delete-on-termination + certify.
4. **Scope budget to estimand.** RentCast bills per CALL: Foundation $74/mo = 1,000 calls; Growth $199/5,000; Scale $449/25,000. Datafiniti bills per RECORD: Starter $119/1K; Professional $349/10K. A single North-Side submarket study lands in the low-hundreds-$/mo tier.
5. **Validate against Cook County Assessor ground-truth** ([src/lp_reit_lab/ingest/sources/cook_county.py](src/lp_reit_lab/ingest/sources/cook_county.py)): join on PIN/address, check beds/baths/sqft plausibility + assessment-year alignment before trusting DOM/HOA (which have no open-data check). This is the only way to establish Cook-County-specific fill-rate/accuracy — no vendor page verifies it at submarket level.
6. **Avoid as load-bearing:** ATTOM/CoreLogic full HOA/assessment entitlements are sales-gated, not self-serve *(ATTOM price unverified)*; unofficial Realtor.com RapidAPI scrapers fail the project evidence hierarchy (ToS/redistribution risk) — spot-check only.

---

## Cross-track flags (unverified — confirm before relying)
- §22.1 **special-assessment HISTORY**: NOT a standard RESO DD field and NOT confirmed in RentCast/Datafiniti schemas or (field-level) the MRED Residential Glossary. Most likely needs per-listing connectMLS/§22.1 disclosure (Track A UI) — the one field-family Track C probably does not fully unlock.
- Field-level confirmation that connectMLS/MRED feed carries discrete HOA-fee + special-assessment items (bed/bath/sqft + DOM ARE confirmed).
- Leasing-Agent user-type scope to full residential SALE-listing display.
- MRED $500 Path-B applicability to NEW 2026 vendors (Feb-2017 form); MLS-Grid MRED-specific feed price; MLS-Grid onboarding SLA.
- Heartland "MLS Plus" $1,000/yr + $144 Supra (trade press, not official); Broker/Managing-Broker IDFPR application fee + any Live Scan fee.
- Whether the executed MRED Participant Data Access Agreement permits storing MRED-derived fields in a PUBLIC repo.
- Note: MLS Grid docs' "Heartland MLS" = Kansas City (KCRAR), a DIFFERENT entity from IL "Heartland REALTOR Organization."

## Sources (official)
- IDFPR Real Estate — https://idfpr.illinois.gov/profs/realest.html ; https://idfpr.illinois.gov/dre/reabout.html
- IDFPR Residential Leasing Agent Applicant Guide — https://idfpr.illinois.gov/content/dam/soi/en/web/idfpr/forms/dre/Student%20Leasing%20Agent%20New%20Applicant%20Guide.pdf
- PSI ILREP booklet — https://test-takers.psiexams.com/api/content/bulletin/4655 ; https://www.psiexams.com/test-takers/ilrep/
- Heartland REALTOR Organization 2026 fee form — https://heartlandro.realtor/download/membershipfees.pdf
- MRED Rules & Regulations — https://www.mredllc.com/comms/resources/MREDRulesAndRegulations.pdf
- MRED Systems Access Policy — https://www.mredllc.com/comms/resources/Systems-Access-Policy-%20December%202023.pdf
- MRED User Privileges Policy — https://www.mredllc.com/comms/resources/MRED-User-Privileges-Policy.pdf
- MRED Residential Glossary — https://www.mredllc.com/comms/resources/MREDResidentialGlossary.pdf
- MRED Web API Broker Documents — https://ww2.mredllc.com/wp-content/uploads/2018/07/Web-API-Broker-Documents-Interactive.pdf
- MLS Grid — https://www.mlsgrid.com/ ; https://www.mlsgrid.com/faq ; https://www.mlsgrid.com/resources ; https://docs.mlsgrid.com/
- RESO Web API + DD 1.7 — https://www.reso.org/reso-web-api/ ; https://dd.reso.org/DD1.7/Property/BedroomsTotal/ ; https://dd.reso.org/DD1.7/Property/LivingArea/ ; https://dd.reso.org/DD1.7/Property/DaysOnMarket/ ; https://dd.reso.org/DD1.7/Property/AssociationFee/
- RentCast — https://www.rentcast.io/api ; https://www.rentcast.io/pricing ; https://www.rentcast.io/terms-api ; https://developers.rentcast.io/reference/property-data-schema.md ; https://developers.rentcast.io/reference/property-listings-schema.md
- Datafiniti — https://www.datafiniti.co/data/property-data ; https://docs.datafiniti.co/docs/property-data-schema ; https://www.datafiniti.co/terms
- MRED membership-optional reporting — https://www.realestatenews.com/2026/03/18/mred-mls-moves-to-make-association-membership-optional ; https://www.realestatenews.com/2026/04/24/mred-opens-access-to-all-agents-with-compass-the-first-to-join
- Heartland MLS Plus (trade press) — https://therealdeal.com/chicago/2026/05/07/chicago-area-organizations-offering-non-realtor-mls-access/

---
*AI-assistance statement: Drafted with Claude Opus 4.8 (role: research). Source synthesis only; all dollar figures, fees, and process steps are tagged with their confirmation status, and unverified items are marked "(unverified)". Confirm load-bearing items against the cited official pages before action.*
