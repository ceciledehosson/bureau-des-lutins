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
