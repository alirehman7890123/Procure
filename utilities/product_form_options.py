"""
Shared product form options for product-creation flows.

The first entries are intentionally ordered by the most common medicine forms
so users don't land on an alphabetical default like "Aerosol".
"""

_PRIORITY_FORMS = [
    "Tablet",
    "Capsule",
    "Syrup",
    "Injection",
    "Infusion",
]

_OTHER_FORMS = [
    "Aerosol",
    "Balm",
    "Bubble Gum",
    "Caplet",
    "Capsule Sustained Release",
    "Cream",
    "Dragees",
    "Drops",
    "Dry Suspension",
    "Ear Drops",
    "Elixir",
    "Emulsion",
    "Enema",
    "Expectorant",
    "Eye Drops",
    "Eye Gel",
    "Eye Ointment",
    "Eye Suspension",
    "Gel",
    "Granules",
    "Inhaler",
    "Injection Concentrated Solution",
    "Injection Double Strength",
    "Injection Intramuscular",
    "Injection Intramuscular/Intravenous",
    "Injection Intravenous",
    "Injection Subcutaneous",
    "Injection Sustained Release",
    "Linctus",
    "Liniment",
    "Liquid",
    "Lotion",
    "Lozenges",
    "Mixture",
    "Mouth Spray",
    "Mouth Wash",
    "Nasal Drops",
    "Nasal Spray",
    "Nebuliser",
    "Oil",
    "Ointment",
    "Oral Solution",
    "Paint",
    "Paste",
    "Patches",
    "Pellets",
    "Poultice",
    "Powder",
    "Rota Capsules",
    "Sachet",
    "Scrub",
    "Shampoo",
    "Soap",
    "Soft Capsules",
    "Solution",
    "Spray",
    "Suppositories",
    "Suspension",
    "Suspension Double Strength",
    "Syringe",
    "Tablet Chewable",
    "Tablet Double Strength",
    "Tablet Effervescent",
    "Tablet Enteric Coated",
    "Tablet Sublingual",
    "Tablet Sustained Release",
    "Tincture",
    "Toothpaste",
    "Vaginal Cream",
    "Vaginal Ovule",
    "Vaginal Pessaries",
    "Vaginal Tablet",
]


def get_product_form_options():
    seen = set()
    ordered = []

    for form in _PRIORITY_FORMS + sorted(_OTHER_FORMS):
        key = form.strip().lower()
        if not key or key in seen:
            continue
        seen.add(key)
        ordered.append(form)

    return ordered
