# 🎄 Le Bureau des Lutins

Application Streamlit familiale : chacun écrit sa liste, les autres peuvent réserver sans dévoiler les surprises. **Projet en cours d'installation**.

## Installation
1. Créer un projet sur [Supabase](https://supabase.com).
2. Coller puis exécuter `schema.sql` dans **SQL Editor**.
3. Exécuter `python setup_lutins.py` en local, puis exécuter le contenu de `initialisation_privee.sql` dans Supabase, **une seule fois**.
4. Personnaliser les noms : `update public.members set name='Sophie' where name='Lutin 1';` (adapter pour chacun).
5. Copier `.streamlit/secrets.toml.example` vers `.streamlit/secrets.toml` puis renseigner l'URL Supabase et la clé **publique** (`anon` / `publishable`), jamais `service_role`.
6. Lancer `pip install -r requirements.txt` puis `streamlit run app.py`.
7. Déployer depuis ce dépôt privé sur [Streamlit Community Cloud](https://share.streamlit.io/), fichier principal `app.py`. Copier les paramètres Supabase dans les **Secrets** de Streamlit Cloud.

Les fichiers privés `initialisation_privee.sql`, `codes_lutins.txt` et `.streamlit/secrets.toml` sont exclus de Git. Envoyer chaque code **individuellement**.

## V1
- Listes modifiables avec description, budget, priorité, lien.
- Réservations exclusives, statut acheté, libération et hotte personnelle.
- Les réservations de sa propre liste ne sont pas retournées par la base.
- Cadeaux communs : coordination manuelle en V1.

⚠️ Prototype familial : les codes d'accès sont des secrets de connexion. Éviter toute donnée sensible. Avant une utilisation plus large, ajouter une limitation des tentatives de connexion et un mécanisme de renouvellement des codes.


## Mise à jour V2 (base existante)
1. Ouvrir `migration_v2.sql` et exécuter son contenu dans **Supabase → SQL Editor**.
2. La migration remplace les sept noms fictifs par Cécile, Emmanuelle, Aurélie, Samuel, Shayra, Zakia et Isidore, **sans modifier les codes**.
3. La même migration ajoute les contributions aux cadeaux collectifs.
4. Rafraîchir l'application Streamlit ; les modifications de `app.py` ont déjà été publiées sur GitHub.

Un cadeau collectif commence par une réservation normale. Les autres lutins peuvent alors le rejoindre, avec un montant facultatif. La coordination du paiement se fait entre eux. Le destinataire ne voit pas ces participations. L'application conserve son fonctionnement V1 si la migration n'est pas encore exécutée.

## Droits d’auteur

© 2026 Cécile de Hosson — Tous droits réservés.

Le dépôt est accessible publiquement pour consultation, mais aucune licence générale de réutilisation, modification ou redistribution n’est accordée à ce stade.

## Plusieurs liens pour un cadeau (novembre 2026)

Dans « Ma lettre », les champs « Liens » acceptent désormais **jusqu'à 5 URL**, une par ligne (1 000 caractères au total). Les liens apparaissent séparément dans « Ma lettre » et « L'atelier ». Les anciens cadeaux avec un seul lien restent compatibles. Aucune migration Supabase n'est nécessaire : le champ texte `url` existant conserve les lignes séparées par des retours à la ligne.
