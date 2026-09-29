# Kapselit ledgeriin — odottaa userin päätöstä (29.9.2026)

Mekanismi valmis: `tools/audit_capsule.py <lane>` tuottaa zipin (sha256-MANIFEST + PREREG_PROOF +
VERIFY.py), jonka kuka tahansa verifioi offline. Ensimmäinen: `shakeup-atlas-audit/atlas_capsule.zip`.

Julkistus vaatisi kaksi userin lupaa:
1. Kapseli talletukseen (esim. Atlas-recordin uusi versio `zenodo.py newversion --keep`) TAI
   suoraan sivulle tiedostona.
2. ledger.html:n verify-alaviitteeseen jatkolause, ehdotus:
   "The first capsule - a zip whose MANIFEST and VERIFY.py let a stranger check every file
   offline - ships with the Kaggle threshold deposit."

EI TOTEUTETTU — vain tämä muistiinpano. Kun user sanoo kyllä: aja kapseli uusiksi (lane on
muuttunut PREREG_PROOF-regeneroinnin jälkeen), newversion --keep, ledger-lause, check_ledger, push.
