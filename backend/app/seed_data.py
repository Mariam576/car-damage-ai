"""UK repair-cost reference data loaded into SQLite on first start.

The damage classes and repair methods follow the notebook (cell 27). Each
price range comes from a published UK web page, recorded with its URL and
dates so every figure in a report can be traced to where it came from.

All pages were read on 9 October 2026. Prices are indicative guide figures
as published by each source (UK consumer prices are normally quoted with
VAT included); they are not quotations.

To change a price, edit this file and run ``python -m app.seed --reset``,
or edit the ``repair_methods`` table in ``data/repair_costs.db`` directly.
"""

from __future__ import annotations

RETRIEVED_ON = "2026-10-09"

# The six classes the YOLO model was trained on (data.yaml in the notebook).
DAMAGE_CLASSES: list[dict] = [
    {"name": "dent", "label": "Dent", "safety_related": False},
    {"name": "scratch", "label": "Scratch", "safety_related": False},
    {"name": "crack", "label": "Crack", "safety_related": False},
    {"name": "glass shatter", "label": "Glass shatter", "safety_related": True},
    {"name": "lamp broken", "label": "Lamp broken", "safety_related": True},
    {"name": "tire flat", "label": "Flat tyre", "safety_related": True},
]

SOURCES: list[dict] = [
    {
        "key": "chipex-scratch-2026",
        "publisher": "Chipex",
        "title": "Touch-Up Paint vs Body Shop Respray: Which to Choose? Car Scratch Repair Cost UK Guide",
        "url": "https://chipex.co.uk/blog/how-to-guides/touch-up-paint-vs-body-shop-respray-which-to-choose-car-scratch-repair-cost-uk-guide/",
        "published": "2026-07-13",
        "updated": None,
    },
    {
        "key": "startrescue-scratch-2025",
        "publisher": "Start Rescue",
        "title": "How much does a car scratch repair cost?",
        "url": "https://www.startrescue.co.uk/breakdown-cover/motoring-advice/car-servicing-and-repairs/how-much-does-a-car-scratch-repair-cost",
        "published": "2025-04-03",
        "updated": None,
    },
    {
        "key": "dentscout-dent-2026",
        "publisher": "Dentscout",
        "title": "How Much Does Dent Repair Cost in the UK?",
        "url": "https://dentscout.co.uk/blog/dent-repair-cost-uk",
        "published": "2025-04-01",
        "updated": "2026-08-30",
    },
    {
        "key": "damagefix-dent-2026",
        "publisher": "Damage Fix",
        "title": "Dent Repair Cost UK | PDR & Painted Dent Prices",
        "url": "https://www.damagefix.co.uk/dent-repair-cost-uk-pdr-painted-dent-prices/",
        "published": "2026-08-31",
        "updated": None,
    },
    {
        "key": "bumper-bumper-2025",
        "publisher": "Bumper",
        "title": "What does bumper repair cost in the UK?",
        "url": "https://www.bumper.co/blog/bumper-repair-cost-uk",
        "published": None,
        "updated": "2025-07-08",
    },
    {
        "key": "bumper-windscreen-2026",
        "publisher": "Bumper",
        "title": "How Much Does a Windscreen Replacement Cost? (2026)",
        "url": "https://www.bumper.co/blog/windscreen-replacement-cost",
        "published": None,
        "updated": "2026-07-20",
    },
    {
        "key": "startrescue-headlights-2026",
        "publisher": "Start Rescue",
        "title": "Why your car's headlights are getting smarter, but more expensive to replace",
        "url": "https://www.startrescue.co.uk/breakdown-cover/motoring-advice/motoring-costs/why-your-cars-headlights-are-getting-smarter--but-more-expensive-to-replace",
        "published": "2026-08-18",
        "updated": None,
    },
    {
        "key": "drive-puncture-2026",
        "publisher": "Drive (Andrew Brady)",
        "title": "How much does it cost to get a tyre repaired?",
        "url": "https://drive.co.uk/guides/how-much-does-it-cost-to-get-a-tyre-repaired",
        "published": "2026-07-16",
        "updated": None,
    },
    {
        "key": "bumper-tyre-2026",
        "publisher": "Bumper",
        "title": "Tyre Replacement Cost Guide: £45 to £250+ (2026)",
        "url": "https://www.bumper.co/blog/tyre-replacement-cost",
        "published": None,
        "updated": "2026-07-27",
    },
]

# min_gbp / max_gbp: the range used in reports.
# max_open: True where the source gives an open upper bound ("£1,000+").
REPAIR_METHODS: list[dict] = [
    # --- scratch -----------------------------------------------------------
    {
        "damage_type": "scratch",
        "method": "Clear-coat scratch repair",
        "description": "Machine polish of light scratches that have not gone through the clear coat.",
        "min_gbp": 80, "max_gbp": 150, "max_open": False, "unit": "panel",
        "source": "chipex-scratch-2026",
        "source_note": "Clear coat polish-out: around £80 to £150 per panel.",
    },
    {
        "damage_type": "scratch",
        "method": "Paintwork scratch repair",
        "description": "Scratch through the clear coat into the colour coat, filled and colour-matched.",
        "min_gbp": 60, "max_gbp": 300, "max_open": False, "unit": "panel",
        "source": "chipex-scratch-2026",
        "source_note": "Through-paint scratch repair: around £60 to £300 per panel.",
    },
    {
        "damage_type": "scratch",
        "method": "Deep scratch repair",
        "description": "Scratch through the paint to primer or metal: filled, primed and the panel resprayed.",
        "min_gbp": 200, "max_gbp": 400, "max_open": False, "unit": "panel",
        "source": "startrescue-scratch-2025",
        "source_note": "Full panel respray for deep scratches: small panels (doors, wings, bumpers) £200 to £400; larger panels (bonnet, roof, full side) £400 to £600+.",
    },
    {
        "damage_type": "scratch",
        "method": "Full-panel repaint",
        "description": "Whole panel prepared and resprayed in a body shop.",
        "min_gbp": 350, "max_gbp": 600, "max_open": False, "unit": "panel",
        "source": "chipex-scratch-2026",
        "source_note": "Single panel respray: around £350 to £600.",
    },
    # --- dent --------------------------------------------------------------
    {
        "damage_type": "dent",
        "method": "Paintless dent removal",
        "description": "Dent massaged out from behind; only possible when the paint is unbroken.",
        "min_gbp": 60, "max_gbp": 180, "max_open": False, "unit": "dent",
        "source": "dentscout-dent-2026",
        "source_note": "Small (up to 10 mm) £60 to £80; medium £80 to £120; large (30 to 60 mm) £120 to £180; complex locations £150 to £250.",
    },
    {
        "damage_type": "dent",
        "method": "Dent repair and repaint",
        "description": "Dent pulled and filled, then the area painted and blended.",
        "min_gbp": 200, "max_gbp": 450, "max_open": False, "unit": "dent",
        "source": "damagefix-dent-2026",
        "source_note": "Localised dent repair with paint: about £200 to £450; larger panel and paint repair £350 to £800+.",
    },
    # --- crack -------------------------------------------------------------
    {
        "damage_type": "crack",
        "method": "Panel repair",
        "description": "Crack or split in a plastic panel (usually a bumper) welded, filled and painted.",
        "min_gbp": 250, "max_gbp": 500, "max_open": False, "unit": "panel",
        "source": "bumper-bumper-2025",
        "source_note": "Cracks or splits in plastic bumpers: £250 to £500.",
    },
    {
        "damage_type": "crack",
        "method": "Panel replacement",
        "description": "Damaged panel (usually a bumper) replaced with a new one.",
        "min_gbp": 600, "max_gbp": 1000, "max_open": True, "unit": "panel",
        "source": "bumper-bumper-2025",
        "source_note": "Full bumper replacement: £600 to £1,000+.",
    },
    # --- glass shatter -----------------------------------------------------
    {
        "damage_type": "glass shatter",
        "method": "Automotive glass replacement",
        "description": "Windscreen replaced with standard glass (no driver-assistance camera).",
        "min_gbp": 150, "max_gbp": 400, "max_open": False, "unit": "windscreen",
        "source": "bumper-windscreen-2026",
        "source_note": "Standard replacement £150 to £400 (small car £150 to £250; hatchback or saloon £200 to £350; SUV £250 to £450).",
    },
    {
        "damage_type": "glass shatter",
        "method": "Automotive glass replacement with ADAS recalibration",
        "description": "Windscreen replaced and the driver-assistance camera recalibrated.",
        "min_gbp": 350, "max_gbp": 700, "max_open": True, "unit": "windscreen",
        "source": "bumper-windscreen-2026",
        "source_note": "Premium or ADAS-equipped vehicle: £350 to £700+; recalibration alone adds £100 to £300+.",
    },
    # --- lamp broken -------------------------------------------------------
    {
        "damage_type": "lamp broken",
        "method": "Lamp assembly replacement (halogen / basic LED)",
        "description": "Whole headlamp unit replaced and fitted.",
        "min_gbp": 280, "max_gbp": 805, "max_open": False, "unit": "lamp",
        "source": "startrescue-headlights-2026",
        "source_note": "Fitted cost: Toyota Aygo X halogen about £280 to £320; Ford Fiesta about £350 to £805.",
    },
    {
        "damage_type": "lamp broken",
        "method": "Lamp assembly replacement (LED / matrix LED)",
        "description": "LED or matrix-LED headlamp unit replaced and fitted.",
        "min_gbp": 775, "max_gbp": 1400, "max_open": True, "unit": "lamp",
        "source": "startrescue-headlights-2026",
        "source_note": "Fitted cost: VW Golf full LED about £775 to £950; Audi A3 matrix LED about £1,110 to £1,400; BMW X5 adaptive LED £1,550 to £2,200+.",
    },
    # --- tire flat ---------------------------------------------------------
    {
        "damage_type": "tire flat",
        "method": "Puncture repair",
        "description": "Plug-and-patch repair; only for punctures in the central tread, not run-flats or sidewalls.",
        "min_gbp": 20, "max_gbp": 45, "max_open": False, "unit": "tyre",
        "source": "drive-puncture-2026",
        "source_note": "Formula One Autocentres £22, Halfords £25, National Tyres £25, Kwik Fit £29.95; independents £20 to £30; mobile £35 to £45.",
    },
    {
        "damage_type": "tire flat",
        "method": "Tyre replacement (budget)",
        "description": "New budget-brand tyre. Ask whether fitting and balancing are included.",
        "min_gbp": 45, "max_gbp": 70, "max_open": False, "unit": "tyre",
        "source": "bumper-tyre-2026",
        "source_note": "Cost per tyre, budget: £45 to £70.",
    },
    {
        "damage_type": "tire flat",
        "method": "Tyre replacement (mid-range)",
        "description": "New mid-range tyre. Ask whether fitting and balancing are included.",
        "min_gbp": 75, "max_gbp": 120, "max_open": False, "unit": "tyre",
        "source": "bumper-tyre-2026",
        "source_note": "Cost per tyre, mid-range: £75 to £120.",
    },
    {
        "damage_type": "tire flat",
        "method": "Tyre replacement (premium)",
        "description": "New premium-brand tyre. Ask whether fitting and balancing are included.",
        "min_gbp": 120, "max_gbp": 250, "max_open": True, "unit": "tyre",
        "source": "bumper-tyre-2026",
        "source_note": "Cost per tyre, premium: £120 to £250+; some premium models as high as £500.",
    },
]
